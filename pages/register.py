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


def show():
    apply_css()

    # ── Hero ────────────────────────────────────────────────
    st.markdown("""
    <div class="lp-hero">
      <div class="lp-wordmark">
        <span class="c8-gold" style="color:#FFD700;">Crea8it</span>
        <span class="c8-teal" style="color:#00B4D8;"> Labs</span>
      </div>

      <div class="lp-tagline">
        Build ● Launch ● Win
      </div>

      <div class="lp-badge">
        <span class="dot">●</span> Cohort 1 is open
        <span class="dot">●</span> 6 weeks
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Social Proof Avatar Strip ───────────────────────────
    # Loads user1.jpeg – user6.jpeg from assets/avatars/
    avatar_files = [f"user{i}.jpeg" for i in range(1, 7)]
    avatar_b64 = []

    for fname in avatar_files:
        path = os.path.join("assets", "avatars", fname)
        if os.path.exists(path):
            with open(path, "rb") as f:
                ext = fname.rsplit(".", 1)[-1].lower()
                mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                encoded = base64.b64encode(f.read()).decode()
                avatar_b64.append(f"data:{mime};base64,{encoded}")

    if avatar_b64:
        imgs_html = "".join(
            f'<img src="{src}" class="sp-avatar" alt="cohort member" />'
            for src in avatar_b64
        )
        st.markdown(f"""
        <style>
          .sp-wrap {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 18px 0 22px;
          }}
          .sp-avatars {{
            display: flex;
            align-items: center;
          }}
          .sp-avatar {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #0A1628;
            margin-left: -10px;
            box-shadow: 0 0 0 2px #00B4D8;
          }}
          .sp-avatars img:first-child {{ margin-left: 0; }}
          .sp-text {{
            font-size: 0.85rem;
            color: #8BA0B8;
            line-height: 1.45;
          }}
          .sp-text strong {{
            color: #E8EDF2;
            display: block;
          }}
          .sp-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            display: inline-block;
            margin-right: 5px;
            box-shadow: 0 0 6px #22c55e;
          }}
        </style>
        <div class="sp-wrap">
          <div class="sp-avatars">{imgs_html}</div>
          <div class="sp-text">
            <strong></strong>
            <span><span class="sp-dot"></span><br>Actively Used by 100+ Builders</span>
          </div>
          
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="font-size:12px;color:#6B7280;text-align:center;
              line-height:1.7;max-width:340px;margin:0 auto;">
              Join the builders turning
              <span style="color:#FFD700;">ideas into real products, careers, and startups</span>
              — from scratch, with grit and resilience, in the most Crea8ive way.
        </div>
        """, unsafe_allow_html=True)



    # ── Registration & Login ───────────────────────────────
    with st.expander("Get Started👇: Registration & Login 🔐", expanded=False):

        tab_register, tab_login = st.tabs(
            ["✦ New Registration", "→ Already Registered"]
        )

        # ====================================================
        # REGISTRATION TAB
        # ====================================================
        with tab_register:

            st.markdown("""
            <div class="alert-warn" style="margin:16px 0 20px;">
              <strong>How to join:</strong>
              Purchase <em>Enter AI</em> (₦5,000) →
              receive your unique payment code →
              enter it below to unlock your 6-week program.
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
                    phone = st.text_input(
                        "WhatsApp Number",
                        placeholder="+2348012345678"
                    )

                with col4:
                    cohort_type = st.selectbox(
                        "Which best describes you?",
                        [
                            "Student",
                            "Graduate / Job seeker",
                            "Career pivoter"
                        ]
                    )

                payment_code = st.text_input(
                    "Payment Code",
                    placeholder="From your Enter AI purchase receipt"
                )

                submitted = st.form_submit_button(
                    "Create My Account →",
                    use_container_width=True
                )

            if submitted:

                if not all([
                    full_name,
                    email,
                    phone,
                    payment_code
                ]):
                    st.error("Please fill in all fields.")
                    return

                if get_participant(email.strip().lower()):
                    st.warning(
                        "Email already registered — use the login tab."
                    )
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
                        "full_name": full_name.strip(),
                        "email": email.strip().lower(),
                        "phone": phone.strip(),
                        "cohort_type": cohort_type,
                        "payment_code": payment_code.strip(),
                        "registered_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    })

                st.success(
                    f"Welcome, {full_name.split()[0]}! "
                    f"Your {PROGRAM_NAME} account is ready."
                )

                login_participant(email.strip().lower())
                st.rerun()

        # ====================================================
        # LOGIN TAB
        # ====================================================
        with tab_login:

            st.markdown("""
            <div style="padding:16px 0 8px;">
              <p style="
                  color:#8BA0B8;
                  font-size:0.88rem;
                  margin-bottom:20px;
                  line-height:1.6;
              ">
                Enter the email address you used to register
                and we'll take you straight to your dashboard.
              </p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("login_form"):

                login_email = st.text_input(
                    "Your Registered Email Address"
                )

                login_btn = st.form_submit_button(
                    "Access My Dashboard →",
                    use_container_width=True
                )

            if login_btn:

                if not login_email:
                    st.error("Please enter your email address.")
                    return

                with st.spinner("Looking up your account..."):
                    found = login_participant(
                        login_email.strip().lower()
                    )

                if found:
                    st.rerun()
                else:
                    st.error(
                        "No account found with that email. "
                        "Please register first or check for a typo."
                    )

    # ── Trust Strip ─────────────────────────────────────────
    st.markdown("""
    <div class="lp-trust-strip">
      <div class="lp-trust-item">
        <span class="check">✓</span>
        No password needed
      </div>

      <div class="lp-trust-item">
        <span class="check">✓</span>
        One payment code per account
      </div>

      <div class="lp-trust-item">
        <span class="check">✓</span>
        Progress saved automatically
      </div>

      <div class="lp-trust-item">
        <span class="check">✓</span>
        Personal feedback from Abdul
      </div>
    </div>
    """, unsafe_allow_html=True)
