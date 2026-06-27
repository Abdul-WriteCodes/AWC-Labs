import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from config import SPREADSHEET_ID, WS_PARTICIPANTS, WS_PROGRESS, WS_CODES

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_spreadsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)


@st.cache_resource
def get_sheet(worksheet_name: str):
    return get_spreadsheet().worksheet(worksheet_name)


def _fresh_sheet(name: str):
    """Always return a live handle, bypassing the cache_resource."""
    return get_spreadsheet().worksheet(name)


def _ensure_sheet(name: str, rows: int, cols: int, header: list) -> None:
    """Create a worksheet with header if it does not exist.
    Never calls get_sheet.clear() to avoid nuking all cached handles.
    """
    try:
        get_sheet(name)
        return
    except Exception:
        pass
    try:
        ss = get_spreadsheet()
        ws = ss.add_worksheet(title=name, rows=rows, cols=cols)
        ws.append_row(header)
    except Exception:
        pass


# ── Payment Codes ──────────────────────────────────────────────

def is_valid_code(code: str) -> bool:
    all_values = get_sheet(WS_CODES).get_all_values()
    if not all_values:
        return False
    headers = [h.strip().lower() for h in all_values[0]]
    try:
        code_col = headers.index("code")
        used_col = headers.index("used")
    except ValueError:
        return False
    for row in all_values[1:]:
        while len(row) <= max(code_col, used_col):
            row.append("")
        if row[code_col].strip().upper() == code.strip().upper():
            used_val = row[used_col].strip().lower()
            return used_val not in ("yes", "true", "1", "used")
    return False


def mark_code_used(code: str):
    ws = get_sheet(WS_CODES)
    all_values = ws.get_all_values()
    if not all_values:
        return
    headers = [h.strip().lower() for h in all_values[0]]
    try:
        code_col = headers.index("code")
        used_col = headers.index("used")
    except ValueError:
        return
    for i, row in enumerate(all_values[1:], start=2):
        while len(row) <= max(code_col, used_col):
            row.append("")
        if row[code_col].strip().upper() == code.strip().upper():
            ws.update_cell(i, used_col + 1, "yes")
            break


# ── Participants ───────────────────────────────────────────────

@st.cache_data(ttl=120)
def get_all_participants() -> list[dict]:
    return get_sheet(WS_PARTICIPANTS).get_all_records()


def register_participant(data: dict):
    get_sheet(WS_PARTICIPANTS).append_row([
        data["full_name"],
        data["email"],
        data["phone"],
        data["cohort_type"],
        data["payment_code"].upper(),
        data["registered_at"],
    ])
    get_all_participants.clear()
    mark_code_used(data["payment_code"])


def get_participant_cached(email: str) -> dict | None:
    records = get_all_participants()
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            return row
    return None


def get_participant(email: str) -> dict | None:
    return get_participant_cached(email)


# ── Progress ───────────────────────────────────────────────────

def get_progress_from_sheet(email: str) -> dict:
    records = get_sheet(WS_PROGRESS).get_all_records()
    progress = {}
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            week = int(row.get("week", 0))
            task_idx = int(row.get("task_index", 0))
            progress.setdefault(week, []).append(task_idx)
    return progress


def mark_task_done(email: str, week: int, task_index: int, completed_at: str):
    get_sheet(WS_PROGRESS).append_row([email, week, task_index, completed_at])
    if "progress" not in st.session_state:
        st.session_state["progress"] = {}
    st.session_state["progress"].setdefault(week, [])
    if task_index not in st.session_state["progress"][week]:
        st.session_state["progress"][week].append(task_index)


@st.cache_data(ttl=60)
def get_all_progress() -> list[dict]:
    return get_sheet(WS_PROGRESS).get_all_records()


def wipe_all_progress():
    ws = get_sheet(WS_PROGRESS)
    all_values = ws.get_all_values()
    if len(all_values) > 1:
        ws.delete_rows(2, len(all_values))
    get_all_progress.clear()


# ── Active Program ─────────────────────────────────────────────
# Stored in a dedicated sheet called "ActiveProgram".
# A1 = active program_id
# A2 = active unit_label
# A3 = active week number
#
# One sheet, fixed cells, no column indexing, no key-value lookup.
# This is the single source of truth that persists across all sessions.

_AP_SHEET = "ActiveProgram"


def _ap_ws():
    """Get a live (non-cached) handle to the ActiveProgram sheet, creating it if needed."""
    try:
        return _fresh_sheet(_AP_SHEET)
    except Exception:
        pass
    # Sheet doesn't exist — create it with seed values
    ss = get_spreadsheet()
    ws = ss.add_worksheet(title=_AP_SHEET, rows=10, cols=2)
    ws.update("A1", [[""], ["Week"], [1]])
    return ws


def get_active_program_id_live() -> str:
    try:
        val = _ap_ws().acell("A1").value
        return str(val).strip() if val else ""
    except Exception:
        return ""


@st.cache_data(ttl=30)
def get_active_program_id() -> str:
    return get_active_program_id_live()


def get_active_unit_label_live() -> str:
    try:
        val = _ap_ws().acell("A2").value
        return str(val).strip() if val else "Week"
    except Exception:
        return "Week"


@st.cache_data(ttl=30)
def get_active_unit_label() -> str:
    return get_active_unit_label_live()


@st.cache_data(ttl=30)
def get_active_week() -> int:
    try:
        val = _ap_ws().acell("A3").value
        return int(val) if val else 1
    except Exception:
        return 1


def set_active_week(week: int):
    _ap_ws().update("A3", [[week]])
    get_active_week.clear()


def set_active_program(program_id: str, unit_label: str):
    """
    Write the active program to the ActiveProgram sheet.
    A1 = program_id, A2 = unit_label, A3 = 1 (reset week).
    Persists across all sessions and survives logout/login/redeploy.
    """
    ws = _ap_ws()
    ws.update("A1", [[program_id]])
    ws.update("A2", [[unit_label]])
    ws.update("A3", [[1]])
    get_active_program_id.clear()
    get_active_unit_label.clear()
    get_active_week.clear()


# ── Programs registry ──────────────────────────────────────────

def _ensure_programs_sheet():
    _ensure_sheet("Programs", 100, 4,
                  ["program_id", "name", "unit_label", "created_at"])


@st.cache_data(ttl=30)
def get_all_programs() -> list[dict]:
    try:
        _ensure_programs_sheet()
        return get_sheet("Programs").get_all_records()
    except Exception:
        return []


def create_program(program_id: str, name: str, unit_label: str, created_at: str):
    _ensure_programs_sheet()
    get_sheet("Programs").append_row([program_id, name, unit_label, created_at])
    get_all_programs.clear()


def delete_program(program_id: str):
    ws = _fresh_sheet("Programs")
    all_values = ws.get_all_values()
    rows_to_delete = []
    for i, row in enumerate(all_values[1:], start=2):
        if row and str(row[0]).strip() == program_id:
            rows_to_delete.append(i)
    for r in reversed(rows_to_delete):
        ws.delete_rows(r)
    get_all_programs.clear()
    _delete_program_content(program_id)


# ── Program Content ────────────────────────────────────────────

WS_PROGRAM = "ProgramContent"


def _ensure_program_content_sheet():
    _ensure_sheet(WS_PROGRAM, 1000, 6,
                  ["program_id", "week", "type", "order", "value", "extra"])


@st.cache_data(ttl=30)
def get_program_weeks(program_id: str) -> dict:
    _ensure_program_content_sheet()
    try:
        records = get_sheet(WS_PROGRAM).get_all_records()
    except Exception:
        return {}

    weeks: dict = {}
    for row in records:
        if str(row.get("program_id", "")).strip() != program_id:
            continue
        w = int(row.get("week", 0))
        if w == 0:
            continue
        if w not in weeks:
            weeks[w] = {"title": "", "theme": "", "materials": [], "tasks": []}
        rtype = str(row.get("type", "")).strip().lower()
        value = str(row.get("value", "")).strip()
        extra = str(row.get("extra", "")).strip()
        if rtype == "title":
            weeks[w]["title"] = value
        elif rtype == "theme":
            weeks[w]["theme"] = value
        elif rtype == "material":
            weeks[w]["materials"].append({"type": extra or "article", "label": value})
        elif rtype == "task":
            weeks[w]["tasks"].append(value)
    return weeks


def save_program_week(program_id: str, week: int, title: str, theme: str,
                      materials: list[dict], tasks: list[str]):
    _ensure_program_content_sheet()
    ws = get_sheet(WS_PROGRAM)
    all_values = ws.get_all_values()

    rows_to_delete = []
    for i, row in enumerate(all_values[1:], start=2):
        try:
            if str(row[0]).strip() == program_id and int(row[1]) == week:
                rows_to_delete.append(i)
        except (ValueError, IndexError):
            pass
    for r in reversed(rows_to_delete):
        ws.delete_rows(r)

    new_rows = [
        [program_id, week, "title",  0, title, ""],
        [program_id, week, "theme",  0, theme, ""],
    ]
    for idx, mat in enumerate(materials):
        new_rows.append([program_id, week, "material", idx,
                         mat.get("label", ""), mat.get("type", "article")])
    for idx, task in enumerate(tasks):
        new_rows.append([program_id, week, "task", idx, task, ""])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")

    get_program_weeks.clear()


def delete_week_from_program(program_id: str, week: int):
    ws = get_sheet(WS_PROGRAM)
    all_values = ws.get_all_values()
    rows_to_delete = []
    for i, row in enumerate(all_values[1:], start=2):
        try:
            if str(row[0]).strip() == program_id and int(row[1]) == week:
                rows_to_delete.append(i)
        except (ValueError, IndexError):
            pass
    for r in reversed(rows_to_delete):
        ws.delete_rows(r)
    get_program_weeks.clear()


def _delete_program_content(program_id: str):
    try:
        ws = get_sheet(WS_PROGRAM)
        all_values = ws.get_all_values()
        rows_to_delete = []
        for i, row in enumerate(all_values[1:], start=2):
            if row and str(row[0]).strip() == program_id:
                rows_to_delete.append(i)
        for r in reversed(rows_to_delete):
            ws.delete_rows(r)
        get_program_weeks.clear()
    except Exception:
        pass


# ── Prompts ────────────────────────────────────────────────────

def get_prompt(week: int) -> str:
    try:
        records = get_sheet("Prompts").get_all_records()
        for row in records:
            if int(row.get("week", 0)) == week:
                return str(row.get("prompt", "")).strip()
    except Exception:
        pass
    return ""


def set_prompt(week: int, prompt: str):
    ws = get_sheet("Prompts")
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if int(row.get("week", 0)) == week:
            ws.update_cell(i, 2, prompt)
            return
    ws.append_row([week, prompt])


# ── Reflections ────────────────────────────────────────────────

def get_reflection(email: str, week: int) -> dict | None:
    try:
        records = get_sheet("Reflections").get_all_records()
        for row in records:
            if (str(row.get("email", "")).strip().lower() == email.strip().lower()
                    and int(row.get("week", 0)) == week):
                return row
    except Exception:
        pass
    return None


def submit_reflection(email: str, week: int, response: str, submitted_at: str):
    get_sheet("Reflections").append_row([email, week, response, submitted_at])
    key = f"reflection_{week}"
    st.session_state[key] = {"email": email, "week": week, "response": response,
                              "submitted_at": submitted_at, "feedback": ""}


@st.cache_data(ttl=60)
def get_all_reflections() -> list[dict]:
    try:
        return get_sheet("Reflections").get_all_records()
    except Exception:
        return []


# ── Feedback ───────────────────────────────────────────────────

def get_feedback(email: str, week: int) -> str:
    try:
        records = get_sheet("Feedback").get_all_records()
        for row in records:
            if (str(row.get("email", "")).strip().lower() == email.strip().lower()
                    and int(row.get("week", 0)) == week):
                return str(row.get("feedback", "")).strip()
    except Exception:
        pass
    return ""


def save_feedback(email: str, week: int, feedback: str, written_at: str):
    ws = get_sheet("Feedback")
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if (str(row.get("email", "")).strip().lower() == email.strip().lower()
                and int(row.get("week", 0)) == week):
            ws.update_cell(i, 3, feedback)
            ws.update_cell(i, 4, written_at)
            return
    ws.append_row([email, week, feedback, written_at])


@st.cache_data(ttl=60)
def get_all_feedback() -> list[dict]:
    try:
        return get_sheet("Feedback").get_all_records()
    except Exception:
        return []
