import streamlit as st
from datetime import datetime
from utils.theme import apply_css
from utils.sheets import is_valid_code, register_participant, get_participant
from utils.auth import login_participant
from config import PROGRAM_NAME


def show():
    apply_css()

    # ── Hero ──────────────────────────────────────────────────
    st.markdown("""
<div class="lp-hero">
  <div class="lp-wordmark">
    <span class="c8-white">Crea</span><span class="c8-8">8it</span><span class="c8-teal" style="color:#00B4D8;"> Labs</span>
  </div>
  <div class="lp-tagline">Build ● Launch ● Win</div>
  <div class="lp-badge">
    <span class="dot">●</span> Cohort 1 is open
    <span class="dot">●</span> 6 weeks
  </div>

  
</div>
""", unsafe_allow_html=True)

with st.expander("🔐 Registration & Login", expanded=True):

    # ── Auth tabs ─────────────────────────────────────────────
    tab_register, tab_login = st.tabs(
        ["✦ New registration", "→ Already registered"]
    )

    with tab_register:
        st.markdown("""
<div class="alert-warn" style="margin:16px 0 20px;">
  <strong>How to join:</strong> Purchase <em>Enter AI</em> (₦5,000) →
  receive your unique payment code → enter it below to unlock your 6-week program.
</div>
""", unsafe_allow_html=True)

        with st.form("registration_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full name")
            with col2:
                email = st.text_input("Email address")

            col3, col4 = st.columns(2)
            with col3:
                phone = st.text_input(
                    "WhatsApp number",
                    placeholder="+2348012345678"
                )
            with col4:
                cohort_type = st.selectbox(
                    "Which best describes you?",
                    ["Student", "Graduate / Job seeker", "Career pivoter"]
                )

            payment_code = st.text_input(
                "Payment code",
                placeholder="From your Enter AI purchase receipt"
            )

            submitted = st.form_submit_button(
                "Create my account →",
                use_container_width=True
            )

        # Registration logic here...

    with tab_login:
        st.markdown("""
<div style="padding:16px 0 8px;">
  <p style="color:#8BA0B8;font-size:0.88rem;margin-bottom:20px;line-height:1.6;">
    Enter the email address you used to register and we'll take you straight to your dashboard.
  </p>
</div>
""", unsafe_allow_html=True)

        with st.form("login_form"):
            login_email = st.text_input(
                "Your registered email address"
            )
            login_btn = st.form_submit_button(
                "Access my dashboard →",
                use_container_width=True
            )

        # Login logic here...

    # ── Trust strip ───────────────────────────────────────────
    st.markdown("""
<div class="lp-trust-strip">
  <div class="lp-trust-item"><span class="check">✓</span> No password needed</div>
  <div class="lp-trust-item"><span class="check">✓</span> One payment code per account</div>
  <div class="lp-trust-item"><span class="check">✓</span> Progress saved automatically</div>
  <div class="lp-trust-item"><span class="check">✓</span> Personal feedback from Abdul</div>
</div>
""", unsafe_allow_html=True)
