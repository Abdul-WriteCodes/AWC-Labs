import streamlit as st
from datetime import datetime
from utils.sheets import is_valid_code, register_participant, get_participant
from utils.auth import login_participant
from config import PROGRAM_NAME, BOOK_PRICE


def show():
    st.markdown("## Join the program")
    st.markdown(
        f"Welcome to the **{PROGRAM_NAME}**. "
        f"To register, you need a payment code from your *Enter AI* book purchase ({BOOK_PRICE})."
    )

    st.divider()

    tab_register, tab_login = st.tabs(["New registration", "Already registered — log in"])

    # ── Registration ──────────────────────────────────────────
    with tab_register:
        st.markdown("#### Create your account")
        with st.form("registration_form"):
            full_name    = st.text_input("Full name")
            email        = st.text_input("Email address")
            phone        = st.text_input("WhatsApp number (with country code, e.g. +2348012345678)")
            cohort_type  = st.selectbox(
                "Which best describes you?",
                ["Student", "Graduate / Job seeker", "Career pivoter"]
            )
            payment_code = st.text_input("Payment code (from your book purchase receipt)")
            submitted    = st.form_submit_button("Register →", use_container_width=True)

        if submitted:
            # Basic validation
            if not all([full_name, email, phone, payment_code]):
                st.error("Please fill in all fields.")
                return

            # Check if already registered
            existing = get_participant(email)
            if existing:
                st.warning("This email is already registered. Use the login tab to access your dashboard.")
                return

            # Validate payment code
            with st.spinner("Verifying your payment code..."):
                valid = is_valid_code(payment_code)

            if not valid:
                st.error("Invalid or already used payment code. Please check your purchase receipt or contact support.")
                return

            # Register
            with st.spinner("Setting up your account..."):
                register_participant({
                    "full_name":    full_name.strip(),
                    "email":        email.strip().lower(),
                    "phone":        phone.strip(),
                    "cohort_type":  cohort_type,
                    "payment_code": payment_code.strip(),
                    "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

            st.success(f"Welcome, {full_name.split()[0]}! Your account is ready.")
            login_participant(email.strip().lower())
            st.rerun()

    # ── Login ─────────────────────────────────────────────────
    with tab_login:
        st.markdown("#### Access your dashboard")
        with st.form("login_form"):
            login_email = st.text_input("Your registered email address")
            login_btn   = st.form_submit_button("Log in →", use_container_width=True)

        if login_btn:
            if not login_email:
                st.error("Please enter your email address.")
                return
            with st.spinner("Looking up your account..."):
                found = login_participant(login_email.strip().lower())
            if found:
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("No account found with that email. Please register first.")
