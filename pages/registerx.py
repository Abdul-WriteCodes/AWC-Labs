import os
import base64
import streamlit as st
from datetime import datetime

from utils.theme import apply_css
from utils.sheets import (
    is_valid_code,
    register_participant,
    get_participant
)
from utils.auth import login_participant
from config import PROGRAM_NAME


# SVG encoded as a data URI for use as a CSS background-image.
# This is the only approach that reliably works on Streamlit Cloud:
# - st.markdown <style> reaches the real DOM
# - background-image on the app root doesn't require iframe escaping
# - No CSP violations, no sanitisation issues
LAB_SVG_DATA_URI = (
    "data:image/svg+xml,"
    "%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20"
    "viewBox%3D%270%200%20800%20900%27%20preserveAspectRatio%3D%27xMidYMid%20slice%27%3E"
    # Orbital rings top-right
    "%3Ccircle%20cx%3D%27740%27%20cy%3D%2790%27%20r%3D%2780%27%20fill%3D%27none%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.7%27%20opacity%3D%270.22%27%2F%3E"
    "%3Ccircle%20cx%3D%27740%27%20cy%3D%2790%27%20r%3D%2755%27%20fill%3D%27none%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.5%27%20opacity%3D%270.15%27%2F%3E"
    "%3Ccircle%20cx%3D%27740%27%20cy%3D%2790%27%20r%3D%278%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.3%27%2F%3E"
    "%3Cline%20x1%3D%27740%27%20y1%3D%2710%27%20x2%3D%27740%27%20y2%3D%27170%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.4%27%20opacity%3D%270.14%27%2F%3E"
    "%3Cline%20x1%3D%27660%27%20y1%3D%2790%27%20x2%3D%27820%27%20y2%3D%2790%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.4%27%20opacity%3D%270.14%27%2F%3E"
    # Orbital rings bottom-left
    "%3Ccircle%20cx%3D%2760%27%20cy%3D%27780%27%20r%3D%2770%27%20fill%3D%27none%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.7%27%20opacity%3D%270.2%27%2F%3E"
    "%3Ccircle%20cx%3D%2760%27%20cy%3D%27780%27%20r%3D%2745%27%20fill%3D%27none%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.5%27%20opacity%3D%270.13%27%2F%3E"
    "%3Ccircle%20cx%3D%2760%27%20cy%3D%27780%27%20r%3D%276%27%20fill%3D%27%23F5A623%27%20opacity%3D%270.28%27%2F%3E"
    # Orbital rings mid-right
    "%3Ccircle%20cx%3D%27790%27%20cy%3D%27520%27%20r%3D%2760%27%20fill%3D%27none%27%20stroke%3D%27%2300C896%27%20stroke-width%3D%270.6%27%20opacity%3D%270.18%27%2F%3E"
    "%3Ccircle%20cx%3D%27790%27%20cy%3D%27520%27%20r%3D%2738%27%20fill%3D%27none%27%20stroke%3D%27%2300C896%27%20stroke-width%3D%270.4%27%20opacity%3D%270.12%27%2F%3E"
    "%3Ccircle%20cx%3D%27790%27%20cy%3D%27520%27%20r%3D%275%27%20fill%3D%27%2300C896%27%20opacity%3D%270.28%27%2F%3E"
    # Flask top-left (simplified polygon)
    "%3Cpolygon%20points%3D%2720%2C40%2036%2C40%2048%2C135%208%2C135%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.06%27%2F%3E"
    "%3Crect%20x%3D%2714%27%20y%3D%2736%27%20width%3D%2728%27%20height%3D%274%27%20fill%3D%27%231F2D3D%27%20opacity%3D%270.5%27%2F%3E"
    "%3Cellipse%20cx%3D%2728%27%20cy%3D%27133%27%20rx%3D%2720%27%20ry%3D%275%27%20fill%3D%27none%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.8%27%20opacity%3D%270.4%27%2F%3E"
    "%3Ccircle%20cx%3D%2718%27%20cy%3D%27105%27%20r%3D%273%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%2734%27%20cy%3D%27118%27%20r%3D%272%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.38%27%2F%3E"
    # Flask bottom-right (simplified)
    "%3Cpolygon%20points%3D%27708%2C700%20722%2C700%20733%2C782%20697%2C782%27%20fill%3D%27%23F5A623%27%20opacity%3D%270.06%27%2F%3E"
    "%3Crect%20x%3D%27702%27%20y%3D%27696%27%20width%3D%2726%27%20height%3D%274%27%20fill%3D%27%231F2D3D%27%20opacity%3D%270.45%27%2F%3E"
    "%3Cellipse%20cx%3D%27715%27%20cy%3D%27780%27%20rx%3D%2718%27%20ry%3D%274%27%20fill%3D%27none%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.7%27%20opacity%3D%270.35%27%2F%3E"
    # Test tube right
    "%3Crect%20x%3D%27773%27%20y%3D%27195%27%20width%3D%2714%27%20height%3D%2755%27%20rx%3D%272%27%20fill%3D%27%231F2D3D%27%20opacity%3D%270.3%27%2F%3E"
    "%3Crect%20x%3D%27773%27%20y%3D%27222%27%20width%3D%2714%27%20height%3D%2728%27%20rx%3D%271%27%20fill%3D%27%2300C896%27%20opacity%3D%270.18%27%2F%3E"
    # Neural net top-center
    "%3Ccircle%20cx%3D%27360%27%20cy%3D%2718%27%20r%3D%275%27%20fill%3D%27%230D1117%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.8%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%27410%27%20cy%3D%2718%27%20r%3D%275%27%20fill%3D%27%230D1117%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.8%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%27385%27%20cy%3D%2750%27%20r%3D%275%27%20fill%3D%27%230D1117%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.8%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%27385%27%20cy%3D%2782%27%20r%3D%275%27%20fill%3D%27%230D1117%27%20stroke%3D%27%2300C896%27%20stroke-width%3D%270.8%27%20opacity%3D%270.5%27%2F%3E"
    "%3Cline%20x1%3D%27360%27%20y1%3D%2718%27%20x2%3D%27385%27%20y2%3D%2750%27%20stroke%3D%27%238BA0B8%27%20stroke-width%3D%270.5%27%20opacity%3D%270.3%27%2F%3E"
    "%3Cline%20x1%3D%27410%27%20y1%3D%2718%27%20x2%3D%27385%27%20y2%3D%2750%27%20stroke%3D%27%238BA0B8%27%20stroke-width%3D%270.5%27%20opacity%3D%270.3%27%2F%3E"
    "%3Cline%20x1%3D%27385%27%20y1%3D%2750%27%20x2%3D%27385%27%20y2%3D%2782%27%20stroke%3D%27%238BA0B8%27%20stroke-width%3D%270.5%27%20opacity%3D%270.3%27%2F%3E"
    # Circuit top-right
    "%3Cpolyline%20points%3D%27580%2C10%20580%2C40%20640%2C40%20640%2C70%20700%2C70%27%20fill%3D%27none%27%20stroke%3D%27%231F2D3D%27%20stroke-width%3D%270.7%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%27580%27%20cy%3D%2710%27%20r%3D%272.5%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%27640%27%20cy%3D%2740%27%20r%3D%222.5%27%20fill%3D%27%231F2D3D%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.6%27%20opacity%3D%270.5%27%2F%3E"
    "%3Ccircle%20cx%3D%27700%27%20cy%3D%2770%27%20r%3D%222.5%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.4%27%2F%3E"
    # Circuit bottom-left
    "%3Cpolyline%20points%3D%2730%2C700%2030%2C660%2090%2C660%2090%2C630%20150%2C630%27%20fill%3D%27none%27%20stroke%3D%27%231F2D3D%27%20stroke-width%3D%270.7%27%20opacity%3D%270.45%27%2F%3E"
    "%3Ccircle%20cx%3D%2730%27%20cy%3D%27700%27%20r%3D%222.5%27%20fill%3D%27%23F5A623%27%20opacity%3D%270.45%27%2F%3E"
    "%3Ccircle%20cx%3D%2790%27%20cy%3D%27660%27%20r%3D%222.5%27%20fill%3D%27%231F2D3D%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.6%27%20opacity%3D%270.45%27%2F%3E"
    # Atom mid-left
    "%3Ccircle%20cx%3D%2735%27%20cy%3D%27285%27%20r%3D%275%27%20fill%3D%27%23F5A623%27%20opacity%3D%270.45%27%2F%3E"
    "%3Cellipse%20cx%3D%2735%27%20cy%3D%27285%27%20rx%3D%2730%27%20ry%3D%2710%27%20fill%3D%27none%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.7%27%20opacity%3D%270.3%27%2F%3E"
    "%3Cellipse%20cx%3D%2735%27%20cy%3D%27285%27%20rx%3D%2730%27%20ry%3D%2710%27%20fill%3D%27none%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.7%27%20opacity%3D%270.3%27%20transform%3D%27rotate(60%2035%20285)%27%2F%3E"
    "%3Cellipse%20cx%3D%2735%27%20cy%3D%27285%27%20rx%3D%2730%27%20ry%3D%2710%27%20fill%3D%27none%27%20stroke%3D%27%23F5A623%27%20stroke-width%3D%270.7%27%20opacity%3D%270.3%27%20transform%3D%27rotate(120%2035%20285)%27%2F%3E"
    # Atom right-bottom
    "%3Ccircle%20cx%3D%27755%27%20cy%3D%27635%27%20r%3D%274%27%20fill%3D%27%2300B4D8%27%20opacity%3D%270.4%27%2F%3E"
    "%3Cellipse%20cx%3D%27755%27%20cy%3D%27635%27%20rx%3D%2728%27%20ry%3D%279%27%20fill%3D%27none%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.6%27%20opacity%3D%270.25%27%2F%3E"
    "%3Cellipse%20cx%3D%27755%27%20cy%3D%27635%27%20rx%3D%2728%27%20ry%3D%279%27%20fill%3D%27none%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.6%27%20opacity%3D%270.25%27%20transform%3D%27rotate(60%20755%20635)%27%2F%3E"
    "%3Cellipse%20cx%3D%27755%27%20cy%3D%27635%27%20rx%3D%2728%27%20ry%3D%279%27%20fill%3D%27none%27%20stroke%3D%27%2300B4D8%27%20stroke-width%3D%270.6%27%20opacity%3D%270.25%27%20transform%3D%27rotate(120%20755%20635)%27%2F%3E"
    "%3C%2Fsvg%3E"
)


LAB_CSS = f"""
<style>
/* ── Lab SVG background on the Streamlit root container ── */
[data-testid="stAppViewContainer"] {{
  background-image: url("{LAB_SVG_DATA_URI}");
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
  background-attachment: fixed;
}}

/* ── Hero ── */
.lp-hero {{
  padding: 24px 0 16px;
  text-align: center;
}}
.lp-wordmark {{
  font-family: 'Syne', sans-serif;
  font-size: 2.6rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.1;
  white-space: nowrap;
  margin-bottom: 10px;
}}
.lp-tagline {{
  font-size: 0.78rem;
  color: #8BA0B8;
  letter-spacing: 0.05em;
  margin-bottom: 14px;
  white-space: nowrap;
}}
.lp-badge {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #111827;
  border: 1px solid #1F2D3D;
  border-radius: 20px;
  padding: 6px 16px;
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  color: #4A6080;
  letter-spacing: 0.1em;
  white-space: nowrap;
}}
.lp-badge-dot {{ color: #22c55e; }}

/* ── Icon strip ── */
.lab-icon-strip {{
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 0 18px;
}}
.lab-icon-pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #111827;
  border: 1px solid #1F2D3D;
  border-radius: 20px;
  padding: 5px 12px;
  font-family: 'DM Mono', monospace;
  font-size: 0.6rem;
  color: #8BA0B8;
  white-space: nowrap;
}}

/* ── Social proof ── */
.sp-section {{
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 4px 0 8px;
}}
.sp-wrap {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 8px;
}}
.sp-avatars {{ display: flex; align-items: center; }}
.sp-avatar {{
  width: 34px; height: 34px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #0A1628;
  margin-left: -9px;
  box-shadow: 0 0 0 1.5px #00B4D8;
}}
.sp-avatars img:first-child {{ margin-left: 0; }}
.sp-text {{
  font-size: 0.75rem;
  color: #8BA0B8;
  line-height: 1.4;
  white-space: nowrap;
}}
.sp-dot {{
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
  margin-right: 4px;
  box-shadow: 0 0 4px #22c55e;
}}
.sp-blurb {{
  font-size: 0.72rem;
  color: #6B7280;
  text-align: center;
  line-height: 1.65;
  max-width: 280px;
  margin: 0 auto 18px;
}}

/* ── Trust strip ── */
.lp-trust-strip {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 16px 0 10px;
  white-space: nowrap;
}}
.lp-trust-item {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem;
  color: #4A6080;
}}
.lp-check {{ color: #00C896; }}
</style>
"""

ICON_STRIP_HTML = """
<div class="lab-icon-strip">
  <div class="lab-icon-pill">
    <svg width="11" height="14" viewBox="0 0 11 14" fill="none">
      <line x1="3.5" y1="0" x2="3.5" y2="5.5" stroke="#00B4D8" stroke-width="1.1" stroke-linecap="round"/>
      <line x1="7.5" y1="0" x2="7.5" y2="5.5" stroke="#00B4D8" stroke-width="1.1" stroke-linecap="round"/>
      <line x1="1.5" y1="0" x2="9.5" y2="0"   stroke="#00B4D8" stroke-width="1.1" stroke-linecap="round"/>
      <polygon points="3.5,5.5 0.5,12 10.5,12 7.5,5.5" fill="none" stroke="#00B4D8" stroke-width="0.9" stroke-linejoin="round"/>
      <ellipse cx="5.5" cy="12" rx="4.5" ry="1.2" fill="none" stroke="#00B4D8" stroke-width="0.6" opacity="0.5"/>
    </svg>
    Flask lab
  </div>
  <div class="lab-icon-pill">
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="2" stroke="#F5A623" stroke-width="1"/>
      <ellipse cx="7" cy="7" rx="6" ry="2.2" fill="none" stroke="#F5A623" stroke-width="0.8" transform="rotate(-30, 7, 7)" opacity="0.6"/>
      <ellipse cx="7" cy="7" rx="6" ry="2.2" fill="none" stroke="#F5A623" stroke-width="0.8" transform="rotate(30, 7, 7)" opacity="0.6"/>
      <ellipse cx="7" cy="7" rx="6" ry="2.2" fill="none" stroke="#F5A623" stroke-width="0.8" opacity="0.45"/>
    </svg>
    AI/ML circuits
  </div>
  <div class="lab-icon-pill">
    <svg width="14" height="12" viewBox="0 0 14 12" fill="none">
      <circle cx="2"  cy="2"  r="2" fill="#0D1117" stroke="#00C896" stroke-width="0.8"/>
      <circle cx="12" cy="2"  r="2" fill="#0D1117" stroke="#00C896" stroke-width="0.8"/>
      <circle cx="7"  cy="10" r="2" fill="#0D1117" stroke="#00C896" stroke-width="0.8"/>
      <line x1="4"  y1="2"  x2="10" y2="2"  stroke="#00C896" stroke-width="0.6"/>
      <line x1="2"  y1="4"  x2="7"  y2="8"  stroke="#00C896" stroke-width="0.6"/>
      <line x1="12" y1="4"  x2="7"  y2="8"  stroke="#00C896" stroke-width="0.6"/>
    </svg>
    Neural paths
  </div>
  <div class="lab-icon-pill">
    <svg width="14" height="10" viewBox="0 0 14 10" fill="none">
      <polyline points="0,7 3,7 4.5,1.5 7,9 9.5,4 11,7 14,7"
                stroke="#8BA0B8" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    Live signals
  </div>
</div>
"""


def show():
    apply_css()

    # Inject CSS (including SVG as background-image data URI) into main DOM
    st.markdown(LAB_CSS, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="lp-hero">
      <div class="lp-wordmark">
        <span style="color:#FFD700;">Crea8it</span><span style="color:#00B4D8;"> Lab</span>
      </div>
      <div class="lp-tagline">
        Build ⚙️ &nbsp;●&nbsp; Launch 🚀 &nbsp;●&nbsp; Learn 🤸🏻 &nbsp;●&nbsp; Win 🏆
      </div>
      <div class="lp-badge">
        <span class="lp-badge-dot">●</span> Cohort 1 is open
        <span class="lp-badge-dot">●</span> 6 weeks
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Icon strip
    st.markdown(ICON_STRIP_HTML, unsafe_allow_html=True)

    # Avatar strip
    avatar_files = [f"user{i}.jpeg" for i in range(1, 7)]
    imgs_html = ""
    for fname in avatar_files:
        path = os.path.join("assets", "avatars", fname)
        if os.path.exists(path):
            with open(path, "rb") as f:
                ext = fname.rsplit(".", 1)[-1].lower()
                mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                encoded = base64.b64encode(f.read()).decode()
                imgs_html += (
                    f'<img src="data:{mime};base64,{encoded}" '
                    f'class="sp-avatar" alt="cohort member" />'
                )

    if imgs_html:
        st.markdown(f"""
        <div class="sp-section">
          <div class="sp-wrap">
            <div class="sp-avatars">{imgs_html}</div>
            <div class="sp-text">
              <span class="sp-dot"></span>Actively Used by 100+ Builders
            </div>
          </div>
          <p class="sp-blurb">
            Join the builders turning
            <span style="color:#FFD700;">ideas into real products, careers, and startups</span>
            — from scratch, with grit and resilience.
          </p>
        </div>
        """, unsafe_allow_html=True)

    # Registration & Login expander
    with st.expander("Get Started Here👇: Registration & Login 🔐", expanded=False):

        tab_register, tab_login = st.tabs(
            ["✦ New Registration", "→ Already Registered"]
        )

        with tab_register:
            st.markdown("""
            <div class="alert-warn" style="margin:16px 0 20px;">
              <strong>How to join a Program:</strong>
              Fill your biodata and the Program Registration Code
              issued to you and sign up to unlock your 6-week program.
            </div>
            """, unsafe_allow_html=True)

            with st.form("registration_form"):
                col1, col2 = st.columns(2)
                with col1:
                    full_name = st.text_input("Full Name")
                with col2:
                    email = st.text_input("Email Address")

                col3, col4 = st.columns(2)
                with col3:
                    phone = st.text_input("WhatsApp Number", placeholder="+2348012345678")
                with col4:
                    cohort_type = st.selectbox(
                        "Which best describes you?",
                        ["Student", "Graduate / Job seeker", "Career pivoter"]
                    )

                payment_code = st.text_input("Payment Code", placeholder="Enter your program code")
                submitted = st.form_submit_button("Create My Account →", use_container_width=True)

            if submitted:
                if not all([full_name, email, phone, payment_code]):
                    st.error("Please fill in all fields.")
                    return
                if get_participant(email.strip().lower()):
                    st.warning("Email already registered — use the login tab.")
                    return
                with st.spinner("Verifying payment code..."):
                    if not is_valid_code(payment_code.strip()):
                        st.error(
                            "Invalid or already used payment code. "
                            "Check your receipt or contact support."
                        )
                        return
                with st.spinner("Setting up your account..."):
                    register_participant({
                        "full_name":     full_name.strip(),
                        "email":         email.strip().lower(),
                        "phone":         phone.strip(),
                        "cohort_type":   cohort_type,
                        "payment_code":  payment_code.strip(),
                        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                st.success(
                    f"Welcome, {full_name.split()[0]}! "
                    f"Your {PROGRAM_NAME} account is ready."
                )
                login_participant(email.strip().lower())
                st.rerun()

        with tab_login:
            st.markdown("""
            <p style="color:#8BA0B8;font-size:0.88rem;margin:16px 0 20px;line-height:1.6;">
              Enter the email address you used to register
              and we'll take you straight to your dashboard.
            </p>
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                login_email = st.text_input("Your Registered Email Address")
                login_btn = st.form_submit_button(
                    "Access My Dashboard →", use_container_width=True
                )

            if login_btn:
                if not login_email:
                    st.error("Please enter your email address.")
                    return
                with st.spinner("Looking up your account..."):
                    found = login_participant(login_email.strip().lower())
                if found:
                    st.rerun()
                else:
                    st.error(
                        "No account found with that email. "
                        "Please register first or check for a typo."
                    )

    # Trust strip
    st.markdown("""
    <div class="lp-trust-strip">
      <div class="lp-trust-item"><span class="lp-check">✓</span> No password needed</div>
      <div class="lp-trust-item"><span class="lp-check">✓</span> Secure code access</div>
      <div class="lp-trust-item"><span class="lp-check">✓</span> 6-week program</div>
    </div>
    """, unsafe_allow_html=True)
