import streamlit as st
from datetime import datetime
from utils.sheets import is_valid_code, register_participant, get_participant
from utils.auth import login_participant
from config import PROGRAM_NAME, BOOK_PRICE

LOGO_PATH = "https://raw.githubusercontent.com/abdulbuilds/crea8it/main/assets/logo.jpeg"

def show():
    # ── Hero ──────────────────────────────────────────────────
    st.markdown("""
        <div style="text-align: center; padding: 2.5rem 0 1.5rem 0;">
            <div style="display: inline-block; background: linear-gradient(135deg, #0A1520, #0D2035);
                        border: 1px solid #1A3A52; border-radius: 16px; padding: 28px 40px 20px 40px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-family: 'Space Grotesk', sans-serif; font-size: 2.8rem; font-weight: 700;
                            letter-spacing: -0.03em; line-height: 1;">
                    <span style="color: #E8EDF2;">Crea</span><span style="color: #F4A022;">8</span><span style="color: #00B4D8;">it</span>
                </div>
                <div style="font-size: 0.72rem; color: #4A6478; text-transform: uppercase;
                            letter-spacing: 0.15em; margin-top: 6px;">
                    AI Career Launch Program
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Tagline cards ─────────────────────────────────────────
    st.markdown("""
        <div style="display: flex; gap: 8px; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap;">
            <div style="background: rgba(0,180,216,0.08); border: 1px solid rgba(0,180,216,0.2);
                        border-radius: 20px; padding: 5px 14px; font-size: 0.78rem; color: #00B4D8;">
                📖 Enter AI Book
            </div>
            <div style="background: rgba(244,160,34,0.08); border: 1px solid rgba(244,160,34,0.2);
                        border-radius: 20px; padding: 5px 14px; font-size: 0.78rem; color: #F4A022;">
                🗓 6 Weeks · Cohort 1
            </div>
            <div style="background: rgba(0,200,120,0.08); border: 1px solid rgba(0,200,120,0.2);
                        border-radius: 20px; padding: 5px 14px; font-size: 0.78rem; color: #00C878;">
                🚀 Aspirant to Career
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Auth tabs ─────────────────────────────────────────────
    tab_register, tab_login = st.tabs(["✦  New registration", "→  Already registered"])

    # ── Registration ──────────────────────────────────────────
    with tab_register:
        st.markdown("""
            <div style="background: rgba(244,160,34,0.05); border: 1px solid rgba(244,160,34,0.15);
                        border-radius: 10px; padding: 14px 18px; margin: 16px 0 20px 0; font-size: 0.85rem; color: #C4A060;">
                <strong style="color: #F4A022;">How it works:</strong>
                Purchase <em>Enter AI</em> (₦5,000) → receive a unique payment code →
                enter it below to unlock your 6-week program.
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
                phone = st.text_input("WhatsApp number", placeholder="+2348012345678")
            with col4:
                cohort_type = st.selectbox(
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

            existing = get_participant(email)
            if existing:
                st.warning("This email is already registered. Use the login tab to access your dashboard.")
                return

            with st.spinner("Verifying your payment code..."):
                valid = is_valid_code(payment_code)

            if not valid:
                st.error("Invalid or already used payment code. Check your purchase receipt or contact support.")
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

    # ── Login ─────────────────────────────────────────────────
    with tab_login:
        st.markdown("""
            <div style="padding: 20px 0 8px 0;">
                <p style="color: #7A94A8; font-size: 0.88rem; margin-bottom: 20px;">
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

    # ── Footer ────────────────────────────────────────────────
    st.markdown("""
        <div style="text-align: center; padding: 2.5rem 0 1rem 0; border-top: 1px solid #1A3A52; margin-top: 2.5rem;">
            <div style="font-size: 0.78rem; color: #2A4A5E;">
                Having trouble? Reach us on WhatsApp via the Career Lab group.
            </div>
        </div>
    """, unsafe_allow_html=True)
