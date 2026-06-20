import streamlit as st

# ── Google Sheets ──────────────────────────────────────────────
# Set these in your Streamlit secrets.toml:
# [gsheets]
# spreadsheet_id = "your-sheet-id-here"
# worksheet_participants = "Participants"
# worksheet_progress = "Progress"
# worksheet_codes = "PaymentCodes"

SPREADSHEET_ID       = st.secrets["gsheets"]["spreadsheet_id"]
WS_PARTICIPANTS      = st.secrets["gsheets"].get("worksheet_participants", "Participants")
WS_PROGRESS          = st.secrets["gsheets"].get("worksheet_progress", "Progress")
WS_CODES             = st.secrets["gsheets"].get("worksheet_codes", "PaymentCodes")

# ── Admin ──────────────────────────────────────────────────────
ADMIN_PASSWORD       = st.secrets["admin"]["password"]

# ── Program ───────────────────────────────────────────────────
PROGRAM_NAME         = "Crea8it AI Career Launch Program"
TOTAL_WEEKS          = 6
BOOK_PRICE           = "₦5,000"

# ── Cohort control (admin sets this in the app) ───────────────
# Current active week is stored in Google Sheets, not hardcoded.
# This is the fallback default when sheet is empty.
DEFAULT_ACTIVE_WEEK  = 1
