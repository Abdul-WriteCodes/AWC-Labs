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
    """Cache both the client AND the spreadsheet object — avoids open_by_key() on every call."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)


@st.cache_resource
def get_sheet(worksheet_name: str):
    """Cache worksheet objects — avoids metadata fetch on every call."""
    return get_spreadsheet().worksheet(worksheet_name)


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
    """Reuses the get_all_participants cache — avoids a separate API call."""
    records = get_all_participants()
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            return row
    return None


def get_participant(email: str) -> dict | None:
    return get_participant_cached(email)


# ── Progress ───────────────────────────────────────────────────

def get_progress_from_sheet(email: str) -> dict:
    """Live read — called once per session on first dashboard load."""
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
    # Update session state immediately so UI reflects without re-fetch
    if "progress" not in st.session_state:
        st.session_state["progress"] = {}
    st.session_state["progress"].setdefault(week, [])
    if task_index not in st.session_state["progress"][week]:
        st.session_state["progress"][week].append(task_index)


@st.cache_data(ttl=60)
def get_all_progress() -> list[dict]:
    return get_sheet(WS_PROGRESS).get_all_records()


# ── Active Week ────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_active_week() -> int:
    """Short cache — admin changes reflect within 30 seconds."""
    try:
        val = get_sheet("Settings").acell("B1").value
        return int(val) if val else 1
    except Exception:
        return 1


def set_active_week(week: int):
    """Write active week to Settings sheet and bust the read cache. Raises on failure so caller can show error."""
    ws = get_sheet("Settings")
    ws.update(range_name="B1", values=[[week]])
    # Bust the cached value so the next get_active_week() call returns the new week immediately.
    get_active_week.clear()


# ── Active week helper (no cache — always live) ────────────────

def get_active_week_live() -> int:
    """Always reads from sheet directly. No cache."""
    try:
        val = get_sheet("Settings").acell("B1").value
        return int(val) if val else 1
    except Exception:
        return 1


# ── Prompts ────────────────────────────────────────────────────

def get_prompt(week: int) -> str:
    """Return the reflection prompt for a given week. Empty string if not set."""
    try:
        records = get_sheet("Prompts").get_all_records()
        for row in records:
            if int(row.get("week", 0)) == week:
                return str(row.get("prompt", "")).strip()
    except Exception:
        pass
    return ""


def set_prompt(week: int, prompt: str):
    """Upsert the reflection prompt for a week."""
    ws = get_sheet("Prompts")
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if int(row.get("week", 0)) == week:
            ws.update_cell(i, 2, prompt)
            return
    ws.append_row([week, prompt])


# ── Reflections ────────────────────────────────────────────────

def get_reflection(email: str, week: int) -> dict | None:
    """Return the participant's reflection for a week, or None."""
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
    # Cache in session so UI updates immediately
    key = f"reflection_{week}"
    st.session_state[key] = {"email": email, "week": week, "response": response, "submitted_at": submitted_at, "feedback": ""}


@st.cache_data(ttl=60)
def get_all_reflections() -> list[dict]:
    try:
        return get_sheet("Reflections").get_all_records()
    except Exception:
        return []


# ── Feedback ───────────────────────────────────────────────────

def get_feedback(email: str, week: int) -> str:
    """Return admin feedback for a participant's week reflection."""
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
    """Upsert admin feedback for a participant + week."""
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
