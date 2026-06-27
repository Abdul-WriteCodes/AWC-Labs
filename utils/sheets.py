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


def _ensure_sheet(name: str, rows: int, cols: int, header: list) -> None:
    """Create a worksheet with header if it doesn't exist.
    Never calls get_sheet.clear() — that nukes ALL cached worksheet handles.
    """
    try:
        get_sheet(name)
        return  # already exists
    except Exception:
        pass
    try:
        ss = get_spreadsheet()
        ws = ss.add_worksheet(title=name, rows=rows, cols=cols)
        ws.append_row(header)
    except Exception:
        pass  # concurrent session may have created it; silently ignore


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
    """Delete all data rows from Progress sheet (keep header)."""
    ws = get_sheet(WS_PROGRESS)
    all_values = ws.get_all_values()
    if len(all_values) > 1:
        ws.delete_rows(2, len(all_values))
    get_all_progress.clear()


# ── Active Week (still stored in Settings — it's a cohort control, not config) ──
# Settings sheet: two columns  key | value
#   Row 2: active_week | <int>

def _settings_ws():
    _ensure_sheet("Settings", 10, 2, ["key", "value"])
    try:
        return get_spreadsheet().worksheet("Settings")
    except Exception:
        return get_sheet("Settings")


@st.cache_data(ttl=30)
def get_active_week() -> int:
    try:
        records = _settings_ws().get_all_records()
        for row in records:
            if str(row.get("key", "")).strip().lower() == "active_week":
                val = row.get("value", "")
                return int(val) if val else 1
    except Exception:
        pass
    return 1


def set_active_week(week: int):
    ws = _settings_ws()
    try:
        records = ws.get_all_records()
        for i, row in enumerate(records, start=2):
            if str(row.get("key", "")).strip().lower() == "active_week":
                ws.update_cell(i, 2, week)
                get_active_week.clear()
                return
        ws.append_row(["active_week", week])
    except Exception:
        pass
    get_active_week.clear()


# ── Programs registry ──────────────────────────────────────────
# Programs sheet columns: program_id | name | unit_label | created_at | is_active
# is_active = "yes" for the one active program, "" for all others.
# This is the single source of truth — no Settings cell dependency.

def _ensure_programs_sheet():
    _ensure_sheet("Programs", 100, 5,
                  ["program_id", "name", "unit_label", "created_at", "is_active"])


def _programs_ws():
    """Always fetch a live handle so reads reflect recent writes."""
    _ensure_programs_sheet()
    try:
        return get_spreadsheet().worksheet("Programs")
    except Exception:
        return get_sheet("Programs")


@st.cache_data(ttl=30)
def get_all_programs() -> list[dict]:
    try:
        _ensure_programs_sheet()
        records = get_sheet("Programs").get_all_records()
        # Back-fill missing is_active key for rows written before this column existed
        for r in records:
            r.setdefault("is_active", "")
        return records
    except Exception:
        return []


def create_program(program_id: str, name: str, unit_label: str, created_at: str):
    _ensure_programs_sheet()
    get_sheet("Programs").append_row([program_id, name, unit_label, created_at, ""])
    get_all_programs.clear()


def delete_program(program_id: str):
    """Delete program from registry and all its content rows."""
    ws = _programs_ws()
    all_values = ws.get_all_values()
    rows_to_delete = []
    for i, row in enumerate(all_values[1:], start=2):
        if row and str(row[0]).strip() == program_id:
            rows_to_delete.append(i)
    for r in reversed(rows_to_delete):
        ws.delete_rows(r)
    get_all_programs.clear()
    _delete_program_content(program_id)


# ── Active Program — read/write via Programs sheet is_active column ────────────

def get_active_program_id_live() -> str:
    """
    Read the active program ID directly from the Programs sheet every time.
    No session state caching — the sheet IS the source of truth.
    Short-circuits to a 30-second cache only if a live read fails.
    """
    try:
        ws = _programs_ws()
        records = ws.get_all_records()
        for row in records:
            if str(row.get("is_active", "")).strip().lower() == "yes":
                return str(row.get("program_id", "")).strip()
        return ""
    except Exception:
        return get_active_program_id()


@st.cache_data(ttl=30)
def get_active_program_id() -> str:
    """Cached fallback — used only when a live sheet read fails."""
    try:
        _ensure_programs_sheet()
        records = get_sheet("Programs").get_all_records()
        for row in records:
            if str(row.get("is_active", "")).strip().lower() == "yes":
                return str(row.get("program_id", "")).strip()
        return ""
    except Exception:
        return ""


def get_active_unit_label_live() -> str:
    """Return the unit_label of whichever program is currently active."""
    try:
        ws = _programs_ws()
        records = ws.get_all_records()
        for row in records:
            if str(row.get("is_active", "")).strip().lower() == "yes":
                return str(row.get("unit_label", "")).strip() or "Week"
        return "Week"
    except Exception:
        return get_active_unit_label()


@st.cache_data(ttl=30)
def get_active_unit_label() -> str:
    try:
        _ensure_programs_sheet()
        records = get_sheet("Programs").get_all_records()
        for row in records:
            if str(row.get("is_active", "")).strip().lower() == "yes":
                return str(row.get("unit_label", "")).strip() or "Week"
        return "Week"
    except Exception:
        return "Week"


def set_active_program(program_id: str, unit_label: str):
    """
    Mark program_id as active in the Programs sheet by writing 'yes' to its
    is_active column and clearing 'yes' from all other rows.
    This persists across all sessions and survives logout/login.
    """
    ws = _programs_ws()
    all_values = ws.get_all_values()
    if not all_values:
        return

    headers = [h.strip().lower() for h in all_values[0]]
    try:
        pid_col    = headers.index("program_id") + 1   # 1-indexed for gspread
        active_col = headers.index("is_active")  + 1
    except ValueError:
        # is_active column doesn't exist yet — add it
        ws.update_cell(1, len(headers) + 1, "is_active")
        all_values = ws.get_all_values()
        headers = [h.strip().lower() for h in all_values[0]]
        pid_col    = headers.index("program_id") + 1
        active_col = headers.index("is_active")  + 1

    # Build batch update: set "yes" for the target row, "" for all others
    updates = []
    for i, row in enumerate(all_values[1:], start=2):
        if not row or not row[0].strip():
            continue
        val = "yes" if str(row[0]).strip() == program_id else ""
        updates.append({"range": f"{_col_letter(active_col)}{i}", "values": [[val]]})

    if updates:
        ws.batch_update(updates)

    # Reset active_week to 1 for the newly activated program
    set_active_week(1)

    # Bust caches
    get_all_programs.clear()
    get_active_program_id.clear()
    get_active_unit_label.clear()
    get_active_week.clear()


def _col_letter(n: int) -> str:
    """Convert 1-based column index to letter (1→A, 2→B, …, 26→Z, 27→AA)."""
    result = ""
    while n:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


# ── Program Content ────────────────────────────────────────────
# ProgramContent sheet columns: program_id | week | type | order | value | extra

WS_PROGRAM = "ProgramContent"


def _ensure_program_content_sheet():
    _ensure_sheet(WS_PROGRAM, 1000, 6,
                  ["program_id", "week", "type", "order", "value", "extra"])


@st.cache_data(ttl=30)
def get_program_weeks(program_id: str) -> dict:
    """Load weeks + materials + tasks for a specific program_id."""
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
    """Full replace of a single week's rows for a given program."""
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
        new_rows.append([program_id, week, "material", idx, mat.get("label", ""), mat.get("type", "article")])
    for idx, task in enumerate(tasks):
        new_rows.append([program_id, week, "task", idx, task, ""])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")

    get_program_weeks.clear()


def delete_week_from_program(program_id: str, week: int):
    """Remove all rows for a specific week inside a program."""
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
    """Remove ALL content rows for a program (used when deleting a program)."""
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
