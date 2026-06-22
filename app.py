import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Crea8it Labs",
    page_icon="🚀",
    layout="centered",
)

from utils.theme import apply_css
apply_css()

from utils.auth import is_logged_in, is_admin
import pages.register as register
import pages.dashboard as dashboard
import pages.admin as admin

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:12px 0 16px 0;">
  <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
              letter-spacing:-0.04em;line-height:1;">
    <span style="color:#F0F4F8;">Crea8it</span><span style="color:#F5A623;"> Lab </span><span style="color:#00B4D8;">Lab</span>
  </div>
  <div style="font-size:0.68rem;color:#4A6080;text-transform:uppercase;
              letter-spacing:0.12em;margin-top:4px;font-family:'DM Mono',monospace;">
    AI Career Launch Program
  </div>
</div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div style="background:#111827;border:1px solid #1F2D3D;border-radius:8px;
            padding:10px 14px;margin-bottom:14px;">
  <div style="font-size:0.65rem;color:#4A6080;text-transform:uppercase;
              letter-spacing:0.1em;font-family:'DM Mono',monospace;">Cohort</div>
  <div style="font-size:0.88rem;color:#F0F4F8;font-weight:600;margin-top:2px;">
    Cohort 1 · 6 Weeks
  </div>
</div>
    """, unsafe_allow_html=True)

    st.divider()

    if is_logged_in():
        page = "Dashboard"
        st.markdown('<div style="font-size:0.8rem;color:#4A6080;">📊 My Dashboard</div>',
                    unsafe_allow_html=True)
    elif is_admin():
        page = "Admin"
        st.markdown('<div style="font-size:0.8rem;color:#4A6080;">⚙️ Admin Panel</div>',
                    unsafe_allow_html=True)
    else:
        page = st.radio("", ["Register / Log in", "Admin"], label_visibility="collapsed")

    st.divider()
    st.markdown("""
<div style="font-size:0.68rem;color:#2A4050;text-align:center;padding-top:4px;
            font-family:'DM Mono',monospace;">
  Powered by <span style="color:#F5A623;">Crea8it</span>
</div>
    """, unsafe_allow_html=True)

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
