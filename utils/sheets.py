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

def is_valid_code(code: str) -> bool:
    """Check if payment code exists and has not been used."""
    ws = get_sheet(WS_CODES)
    records = ws.get_all_records()
    for row in records:
        if str(row.get("code", "")).strip().upper() == code.strip().upper():
            return str(row.get("used", "")).strip().lower() != "yes"
    return False


def mark_code_used(code: str):
    ws = get_sheet(WS_CODES)
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):  # row 1 = header
        if str(row.get("code", "")).strip().upper() == code.strip().upper():
            ws.update_cell(i, list(row.keys()).index("used") + 1, "yes")
            break


# ── Participants ───────────────────────────────────────────────

def register_participant(data: dict):
    """
    data keys: full_name, email, phone, cohort_type, payment_code, registered_at
    """
    ws = get_sheet(WS_PARTICIPANTS)
    ws.append_row([
        data["full_name"],
        data["email"],
        data["phone"],
        data["cohort_type"],
        data["payment_code"].upper(),
        data["registered_at"],
    ])
    mark_code_used(data["payment_code"])


def get_participant(email: str) -> dict | None:
    ws = get_sheet(WS_PARTICIPANTS)
    records = ws.get_all_records()
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            return row
    return None


def get_all_participants() -> list[dict]:
    ws = get_sheet(WS_PARTICIPANTS)
    return ws.get_all_records()


# ── Progress ───────────────────────────────────────────────────

def get_progress(email: str) -> dict:
    """Returns {week: [task_indices_completed]} for a participant."""
    ws = get_sheet(WS_PROGRESS)
    records = ws.get_all_records()
    progress = {}
    for row in records:
        if str(row.get("email", "")).strip().lower() == email.strip().lower():
            week = int(row.get("week", 0))
            task_idx = int(row.get("task_index", 0))
            progress.setdefault(week, []).append(task_idx)
    return progress


def mark_task_done(email: str, week: int, task_index: int, completed_at: str):
    ws = get_sheet(WS_PROGRESS)
    ws.append_row([email, week, task_index, completed_at])


def get_all_progress() -> list[dict]:
    ws = get_sheet(WS_PROGRESS)
    return ws.get_all_records()


# ── Active Week (admin-controlled) ────────────────────────────

def get_active_week() -> int:
    try:
        ws = get_sheet("Settings")
        val = ws.acell("B1").value
        return int(val) if val else 1
    except Exception:
        return 1


def set_active_week(week: int):
    try:
        ws = get_sheet("Settings")
        ws.update("B1", week)
    except Exception:
        pass
