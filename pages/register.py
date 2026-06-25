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


# ── Helper: encode SVG string → data URI ─────────────────────
def _svg_uri(svg: str) -> str:
    """Convert an SVG string to a base64 data URI safe for <img src=>."""
    encoded = base64.b64encode(svg.strip().encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


# ── AI Lab decorative icons (inline SVG → base64 img) ────────
# These render as <img> tags — zero raw SVG leaks to screen.

ICON_CIRCUIT = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" fill="none"/>
  <!-- circuit board traces -->
  <polyline points="8,24 18,24 18,14 30,14 30,24 40,24"
    stroke="#00B4D8" stroke-width="1.8" fill="none" opacity="0.7"/>
  <polyline points="18,24 18,34 30,34 30,24"
    stroke="#00B4D8" stroke-width="1.8" fill="none" opacity="0.5"/>
  <!-- nodes -->
  <circle cx="18" cy="14" r="3" fill="#00B4D8" opacity="0.9"/>
  <circle cx="30" cy="14" r="3" fill="#FFD700" opacity="0.9"/>
  <circle cx="18" cy="34" r="3" fill="#FFD700" opacity="0.7"/>
  <circle cx="30" cy="34" r="3" fill="#00B4D8" opacity="0.7"/>
  <!-- chip -->
  <rect x="20" y="20" width="8" height="8" rx="1.5"
    fill="#0D1F3C" stroke="#00B4D8" stroke-width="1.2"/>
  <line x1="22" y1="20" x2="22" y2="18" stroke="#00B4D8" stroke-width="1"/>
  <line x1="26" y1="20" x2="26" y2="18" stroke="#00B4D8" stroke-width="1"/>
  <line x1="22" y1="28" x2="22" y2="30" stroke="#00B4D8" stroke-width="1"/>
  <line x1="26" y1="28" x2="26" y2="30" stroke="#00B4D8" stroke-width="1"/>
</svg>
""")

ICON_FLASK = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" fill="none"/>
  <!-- flask body -->
  <path d="M19,8 L19,22 L10,36 Q8,40 12,41 L36,41 Q40,40 38,36 L29,22 L29,8 Z"
    fill="#0D1F3C" stroke="#F5A623" stroke-width="1.6" stroke-linejoin="round"/>
  <!-- liquid -->
  <path d="M14,35 Q13,38 16,39 L32,39 Q35,38 34,35 L26,22 L22,22 Z"
    fill="#00B4D8" opacity="0.35"/>
  <!-- bubbles -->
  <circle cx="19" cy="33" r="2" fill="#00B4D8" opacity="0.7"/>
  <circle cx="26" cy="30" r="1.4" fill="#FFD700" opacity="0.6"/>
  <circle cx="22" cy="36" r="1" fill="#00B4D8" opacity="0.5"/>
  <!-- neck band -->
  <rect x="18" y="7" width="12" height="3" rx="1.5"
    fill="#0D1F3C" stroke="#F5A623" stroke-width="1.2"/>
</svg>
""")

ICON_ATOM = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" fill="none"/>
  <!-- nucleus -->
  <circle cx="24" cy="24" r="4" fill="#FFD700" opacity="0.9"/>
  <!-- orbits -->
  <ellipse cx="24" cy="24" rx="18" ry="7"
    fill="none" stroke="#00B4D8" stroke-width="1.4" opacity="0.7"/>
  <ellipse cx="24" cy="24" rx="18" ry="7"
    fill="none" stroke="#00B4D8" stroke-width="1.4" opacity="0.7"
    transform="rotate(60 24 24)"/>
  <ellipse cx="24" cy="24" rx="18" ry="7"
    fill="none" stroke="#F5A623" stroke-width="1.4" opacity="0.5"
    transform="rotate(120 24 24)"/>
  <!-- electrons -->
  <circle cx="42" cy="24" r="2.2" fill="#00B4D8" opacity="0.9"/>
  <circle cx="15" cy="37" r="2.2" fill="#00B4D8" opacity="0.9"/>
  <circle cx="15" cy="11" r="2.2" fill="#F5A623" opacity="0.7"/>
</svg>
""")

ICON_ROBOT = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" fill="none"/>
  <!-- antenna -->
  <line x1="24" y1="6" x2="24" y2="12" stroke="#00B4D8" stroke-width="1.6"/>
  <circle cx="24" cy="5" r="2.2" fill="#FFD700" opacity="0.9"/>
  <!-- head -->
  <rect x="12" y="12" width="24" height="20" rx="4"
    fill="#0D1F3C" stroke="#00B4D8" stroke-width="1.6"/>
  <!-- eyes -->
  <rect x="16" y="17" width="6" height="5" rx="1.5"
    fill="#00B4D8" opacity="0.9"/>
  <rect x="26" y="17" width="6" height="5" rx="1.5"
    fill="#00B4D8" opacity="0.9"/>
  <!-- pupils -->
  <circle cx="19" cy="19.5" r="1.5" fill="#0D1F3C"/>
  <circle cx="29" cy="19.5" r="1.5" fill="#0D1F3C"/>
  <!-- mouth -->
  <rect x="17" y="26" width="14" height="3" rx="1.5"
    fill="#1A3050" stroke="#F5A623" stroke-width="0.8"/>
  <rect x="19" y="26.5" width="2" height="2" rx="0.5" fill="#F5A623" opacity="0.7"/>
  <rect x="23" y="26.5" width="2" height="2" rx="0.5" fill="#F5A623" opacity="0.7"/>
  <rect x="27" y="26.5" width="2" height="2" rx="0.5" fill="#F5A623" opacity="0.7"/>
  <!-- ears/bolts -->
  <circle cx="12" cy="22" r="2.5" fill="#1A3050" stroke="#00B4D8" stroke-width="1"/>
  <circle cx="36" cy="22" r="2.5" fill="#1A3050" stroke="#00B4D8" stroke-width="1"/>
  <!-- neck -->
  <rect x="20" y="32" width="8" height="5" rx="1"
    fill="#0D1F3C" stroke="#00B4D8" stroke-width="1"/>
</svg>
""")

ICON_NODE = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" fill="none"/>
  <!-- data node / network hub -->
  <circle cx="24" cy="24" r="8" fill="#0D1F3C" stroke="#F5A623" stroke-width="1.8"/>
  <circle cx="24" cy="24" r="3.5" fill="#F5A623" opacity="0.8"/>
  <!-- spokes -->
  <line x1="24" y1="8"  x2="24" y2="16" stroke="#F5A623" stroke-width="1.2" opacity="0.6"/>
  <line x1="24" y1="32" x2="24" y2="40" stroke="#F5A623" stroke-width="1.2" opacity="0.6"/>
  <line x1="8"  y1="24" x2="16" y2="24" stroke="#00B4D8" stroke-width="1.2" opacity="0.6"/>
  <line x1="32" y1="24" x2="40" y2="24" stroke="#00B4D8" stroke-width="1.2" opacity="0.6"/>
  <line x1="12" y1="12" x2="18" y2="18" stroke="#00B4D8" stroke-width="1.2" opacity="0.4"/>
  <line x1="30" y1="30" x2="36" y2="36" stroke="#00B4D8" stroke-width="1.2" opacity="0.4"/>
  <!-- satellite nodes -->
  <circle cx="24" cy="8"  r="2.5" fill="#00B4D8" opacity="0.7"/>
  <circle cx="24" cy="40" r="2.5" fill="#00B4D8" opacity="0.7"/>
  <circle cx="8"  cy="24" r="2.5" fill="#F5A623" opacity="0.7"/>
  <circle cx="40" cy="24" r="2.5" fill="#F5A623" opacity="0.7"/>
</svg>
""")


def show():
    apply_css()

    # ── Hero ────────────────────────────────────────────────
    st.markdown("""
    <div class="lp-hero">
      <div class="lp-wordmark">
        <span class="c8-gold" style="color:#FFD700;">Crea8it</span>
        <span class="c8-teal" style="color:#00B4D8;"> Lab</span>
      </div>

      <div class="lp-tagline">
        Build ⚙️ ● Launch 🚀 ● Learn 🤸🏻 ● Win 🏆
      </div>

      <div class="lp-badge">
        <span class="dot">●</span> Cohort 1 is open
        <span class="dot">●</span> 6 weeks
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── AI Lab Icon Strip ────────────────────────────────────
    # SVGs are base64-encoded → injected as <img> tags.
    # Streamlit renders <img src="data:image/svg+xml;base64,..."> safely.
    # No raw SVG code ever appears on screen.
    icons = [
        (ICON_CIRCUIT, "AI/ML circuits"),
        (ICON_FLASK,   "Flask lab"),
        (ICON_ATOM,    "Atom / neural"),
        (ICON_ROBOT,   "AI robot"),
        (ICON_NODE,    "Data node"),
    ]
    icons_html = "".join(
        f"""
        <div class="lab-icon-wrap">
          <img src="{uri}" alt="{label}" class="lab-icon" />
          <span class="lab-icon-label">{label}</span>
        </div>
        """
        for uri, label in icons
    )

    st.markdown(f"""
    <style>
      .lab-strip {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 14px 0 10px;
        flex-wrap: wrap;
      }}
      .lab-icon-wrap {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 5px;
        opacity: 0.72;
        transition: opacity 0.2s;
      }}
      .lab-icon-wrap:hover {{ opacity: 1; }}
      .lab-icon {{
        width: 44px;
        height: 44px;
        display: block;
      }}
      .lab-icon-label {{
        font-size: 9px;
        color: #4A6080;
        text-align: center;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        white-space: nowrap;
      }}
    </style>
    <div class="lab-strip">{icons_html}</div>
    """, unsafe_allow_html=True)

    # ── Social Proof Avatar Strip ───────────────────────────
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
          .sp-avatars {{ display: flex; align-items: center; }}
          .sp-avatar {{
            width: 42px; height: 42px;
            border-radius: 50%; object-fit: cover;
            border: 2px solid #0A1628;
            margin-left: -10px;
            box-shadow: 0 0 0 2px #00B4D8;
          }}
          .sp-avatars img:first-child {{ margin-left: 0; }}
          .sp-text {{ font-size: 0.85rem; color: #8BA0B8; line-height: 1.45; }}
          .sp-text strong {{ color: #E8EDF2; display: block; }}
          .sp-dot {{
            width: 7px; height: 7px; border-radius: 50%;
            background: #22c55e; display: inline-block;
            margin-right: 5px; box-shadow: 0 0 6px #22c55e;
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
              — from scratch, with grit and resilience, in the most creative way.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ── Registration & Login ───────────────────────────────
    with st.expander("Get Started Here👇: Registration & Login 🔐", expanded=False):

        tab_register, tab_login = st.tabs(
            ["✦ New Registration", "→ Already Registered"]
        )

        # ====================================================
        # REGISTRATION TAB
        # ====================================================
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
                    phone = st.text_input(
                        "WhatsApp Number",
                        placeholder="+2348012345678"
                    )
                with col4:
                    cohort_type = st.selectbox(
                        "Which best describes you?",
                        ["Student", "Graduate / Job seeker", "Career pivoter"]
                    )

                payment_code = st.text_input(
                    "Payment Code",
                    placeholder="Enter your program code"
                )

                submitted = st.form_submit_button(
                    "Create My Account →",
                    use_container_width=True
                )

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
                        "full_name":      full_name.strip(),
                        "email":          email.strip().lower(),
                        "phone":          phone.strip(),
                        "cohort_type":    cohort_type,
                        "payment_code":   payment_code.strip(),
                        "registered_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
              <p style="color:#8BA0B8;font-size:0.88rem;
                        margin-bottom:20px;line-height:1.6;">
                Enter the email address you used to register
                and we'll take you straight to your dashboard.
              </p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                login_email = st.text_input("Your Registered Email Address")
                login_btn = st.form_submit_button(
                    "Access My Dashboard →",
                    use_container_width=True
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

    # ── Trust Strip ─────────────────────────────────────────
    st.markdown("""
    <div class="lp-trust-strip">
      <div class="lp-trust-item">
        <span class="check">✓</span>
        No password needed
      </div>
    </div>
    """, unsafe_allow_html=True)
