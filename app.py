import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Crea8it Labs",
    page_icon="🧩",
    layout="centered",
)

from utils.theme import apply_css
from utils.auth import is_logged_in, is_admin

# ── Route BEFORE any UI renders ───────────────────────────────
# Check session state directly so we never render the register
# page (and its avatar strip) for an already-authenticated user.
_logged_in = is_logged_in()
_is_admin  = is_admin()

if _is_admin:
    apply_css()
    import pages.admin as admin
    admin.show()

elif _logged_in:
    apply_css()
    import pages.dashboard as dashboard
    dashboard.show()

else:
    # Only unauthenticated users see the sidebar + register page
    apply_css()
    import pages.register as register

    with st.sidebar:
        st.markdown("""
<div style="padding:12px 0 16px 0;">
  <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
              letter-spacing:-0.04em;line-height:1;">
    <span style="color:#F0F4F8;">Crea8it</span><span style="color:#F5A623;"> Lab </span><span style="color:#00B4D8;">Lab</span>
  </div>
  <div style="font-size:0.68rem;color:#4A6080;text-transform:uppercase;
              letter-spacing:0.12em;margin-top:4px;font-family:'DM Mono',monospace;">
    Build • Launch • Learn • Win
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

        page = st.radio("", ["Register / Log in", "Admin"], label_visibility="collapsed")

        st.divider()
        st.markdown("""
<div style="font-size:0.68rem;color:#2A4050;text-align:center;padding-top:4px;
            font-family:'DM Mono',monospace;">
  Powered by <span style="color:#F5A623;">Crea8it</span>
</div>
        """, unsafe_allow_html=True)

    if page == "Admin":
        import pages.admin as admin
        admin.show()
    else:
        register.show()
