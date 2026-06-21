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

  <div class="lp-value-grid">
    <div class="lp-value-card">
      <div class="lp-value-icon">📖</div>
      <div class="lp-value-title">Book-led curriculum</div>
      <div class="lp-value-desc">Weekly tasks tied directly to Enter AI chapters</div>
    </div>
    <div class="lp-value-card">
      <div class="lp-value-icon">✍️</div>
      <div class="lp-value-title">Personal feedback</div>
      <div class="lp-value-desc">Submit weekly reflections and get direct responses</div>
    </div>
    <div class="lp-value-card">
      <div class="lp-value-icon">🚀</div>
      <div class="lp-value-title">Career accountability</div>
      <div class="lp-value-desc">Track your progress from aspirant to AI-ready</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Auth tabs ─────────────────────────────────────────────
    tab_register, tab_login = st.tabs(["✦  New registration", "→  Already registered"])

    with tab_register:
        st.markdown("""
<div class="alert-warn" style="margin:16px 0 20px;">
  <strong>How to join:</strong> Purchase <em>Enter AI</em> (₦5,000) →
  receive your unique payment code → enter it below to unlock your 6-week program.
</div>
""", unsafe_allow_html=True)

        with st.form("registration_form"):
            col1, col2 = st.columns(2)
            with col1: full_name = st.text_input("Full name")
            with col2: email     = st.text_input("Email address")

            col3, col4 = st.columns(2)
            with col3: phone = st.text_input("WhatsApp number", placeholder="+2348012345678")
            with col4: cohort_type = st.selectbox(
                "Which best describes you?",
                ["Student", "Graduate / Job seeker", "Career pivoter"]
            )

            payment_code = st.text_input(
                "Payment code",
                placeholder="From your Enter AI purchase receipt"
            )
            submitted = st.form_submit_button("Create my account →", use_container_width=True)

        if submitted:
            if not all([full_name, email, phone, payment_code]):
                st.error("Please fill in all fields.")
                return
            if get_participant(email):
                st.warning("Email already registered — use the login tab.")
                return
            with st.spinner("Verifying payment code..."):
                if not is_valid_code(payment_code):
                    st.error("Invalid or already used payment code. Check your receipt or contact support.")
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
            st.success(f"Welcome, {full_name.split()[0]}! Your account is ready.")
            login_participant(email.strip().lower())
            st.rerun()

    with tab_login:
        st.markdown("""
<div style="padding:16px 0 8px;">
  <p style="color:#8BA0B8;font-size:0.88rem;margin-bottom:20px;line-height:1.6;">
    Enter the email address you used to register and we'll take you straight to your dashboard.
  </p>
</div>
""", unsafe_allow_html=True)

        with st.form("login_form"):
            login_email = st.text_input("Your registered email address")
            login_btn   = st.form_submit_button("Access my dashboard →", use_container_width=True)

        if login_btn:
            if not login_email:
                st.error("Please enter your email address.")
                return
            with st.spinner("Looking up your account..."):
                found = login_participant(login_email.strip().lower())
            if found:
                st.rerun()
            else:
                st.error("No account found with that email. Please register first, or check for a typo.")

    # ── Trust strip ───────────────────────────────────────────
    st.markdown("""
<div class="lp-trust-strip">
  <div class="lp-trust-item"><span class="check">✓</span> No password needed</div>
  <div class="lp-trust-item"><span class="check">✓</span> One payment code per account</div>
  <div class="lp-trust-item"><span class="check">✓</span> Progress saved automatically</div>
  <div class="lp-trust-item"><span class="check">✓</span> Personal feedback from Abdul</div>
</div>
""", unsafe_allow_html=True)
