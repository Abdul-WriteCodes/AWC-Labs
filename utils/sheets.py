import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from config import SPREADSHEET_ID, WS_PARTICIPANTS, WS_PROGRESS, WS_CODES

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_sheet(worksheet_name: str):
    client = get_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(worksheet_name)


# ── Payment Codes ──────────────────────────────────────────────

@st.cache_data(ttl=30)
def _get_all_codes() -> list[list]:
    """Cached — refreshes every 30 seconds."""
    return get_sheet(WS_CODES).get_all_values()


def is_valid_code(code: str) -> bool:
    all_values = _get_all_codes()
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
            _get_all_codes.clear()  # Bust cache after write
            break


# ── Participants ───────────────────────────────────────────────

@st.cache_data(ttl=60)
def _get_all_participants_cached() -> list[dict]:
    """Cached — refreshes every 60 seconds."""
    return get_sheet(WS_PARTICIPANTS).get_all_records()


def register_participant(data: dict):
    ws = get_sheet(WS_PARTICIPANTS)
    ws.append_row([
        data["full_name"],
        data["email"],
        data["phone"],
        data["cohort_type"],
        data["payment_code"].upper(),
        data["registered_at"],
    ])
    _get_all_participants_cached.clear()  # Bust cache after write
    mark_code_used(data["payment_code"])


def get_participant(email: str) -> dict | None:
    records = _get_all_participants_cached()
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            return row
    return None


def get_all_participants() -> list[dict]:
    return _get_all_participants_cached()


# ── Progress ───────────────────────────────────────────────────

@st.cache_data(ttl=30)
def _get_all_progress_cached() -> list[dict]:
    """Cached — refreshes every 30 seconds."""
    return get_sheet(WS_PROGRESS).get_all_records()


def get_progress(email: str) -> dict:
    records = _get_all_progress_cached()
    progress = {}
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            week = int(row.get("week", 0))
            task_idx = int(row.get("task_index", 0))
            progress.setdefault(week, []).append(task_idx)
    return progress


def mark_task_done(email: str, week: int, task_index: int, completed_at: str):
    get_sheet(WS_PROGRESS).append_row([email, week, task_index, completed_at])
    _get_all_progress_cached.clear()  # Bust cache after write


def get_all_progress() -> list[dict]:
    return _get_all_progress_cached()


# ── Active Week (admin-controlled) ────────────────────────────

@st.cache_data(ttl=60)
def get_active_week() -> int:
    try:
        val = get_sheet("Settings").acell("B1").value
        return int(val) if val else 1
    except Exception:
        return 1


def set_active_week(week: int):
    try:
        get_sheet("Settings").update("B1", week)
        get_active_week.clear()  # Bust cache after write
    except Exception:
        pass
