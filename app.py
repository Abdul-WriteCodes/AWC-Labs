import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Crea8it — AI Career Launch Program",
    page_icon="🚀",
    layout="centered",
)

from utils.auth import is_logged_in, is_admin
import pages.register as register
import pages.dashboard as dashboard
import pages.admin as admin

# ── Sidebar navigation ────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=Crea8it", use_column_width=True)
    st.markdown("**AI Career Launch Program**")
    st.caption("Cohort 1 · 6 Weeks")
    st.divider()

    if is_logged_in():
        page = st.radio("Navigate", ["My Dashboard"], label_visibility="collapsed")
    elif is_admin():
        page = "Admin"
    else:
        page = st.radio("Navigate", ["Register / Log in", "Admin"], label_visibility="collapsed")

    st.divider()
    st.caption("Powered by [Crea8it](https://crea8it.com)")

# ── Routing ───────────────────────────────────────────────────
if is_admin():
    admin.show()
elif is_logged_in():
    dashboard.show()
else:
    if page == "Admin":
        admin.show()
    else:
        register.show()
