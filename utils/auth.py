import streamlit as st
from utils.sheets import get_participant


def login_participant(email: str) -> bool:
    """Look up participant by email and store in session."""
    participant = get_participant(email)
    if participant:
        st.session_state["participant"] = participant
        st.session_state["logged_in"] = True
        return True
    return False


def logout():
    st.session_state["participant"] = None
    st.session_state["logged_in"] = False
    st.session_state["is_admin"] = False
    # Clear program-state keys so the next login always re-reads from the
    # sheet instead of inheriting stale session values.
    for key in ("_active_program_id", "_active_unit_label",
                "active_week", "active_week_last_check"):
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def get_current_participant() -> dict | None:
    return st.session_state.get("participant", None)


def login_admin(password: str) -> bool:
    from config import ADMIN_PASSWORD
    if password == ADMIN_PASSWORD:
        st.session_state["is_admin"] = True
        return True
    return False


def is_admin() -> bool:
    return st.session_state.get("is_admin", False)
