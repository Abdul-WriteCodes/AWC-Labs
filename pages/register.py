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


# ── CSS goes via st.markdown — it injects into the main Streamlit DOM ─────────
# st.html() is sandboxed per-call; CSS inside it never reaches other elements.
# st.markdown(unsafe_allow_html=True) with <style> tags DOES reach the main DOM.
LAB_CSS = """
<style>
/* ── Lab SVG: fixed full-page background, behind everything ── */
#lab-bg-svg {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  pointer-events: none;
  z-index: 0;
  opacity: 1;
}

/* ── Hero ── */
.lp-hero { padding: 24px 0 16px; text-align: center; }
.lp-wordmark {
  font-family: 'Syne', sans-serif;
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.05;
  margin-bottom: 10px;
}
.lp-tagline {
  font-size: 0.88rem;
  color: #8BA0B8;
  letter-spacing: 0.06em;
  margin-bottom: 14px;
}
.lp-badge {
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
}
.lp-badge-dot { color: #22c55e; }

/* ── Icon strip ── */
.lab-icon-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px 0 20px;
}
.lab-icon-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: #111827;
  border: 1px solid #1F2D3D;
  border-radius: 20px;
  padding: 6px 14px;
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem;
  color: #8BA0B8;
  white-space: nowrap;
}

/* ── Social proof ── */
.sp-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 4px 0 12px;
}
.sp-avatars { display: flex; align-items: center; }
.sp-avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #0A1628;
  margin-left: -10px;
  box-shadow: 0 0 0 2px #00B4D8;
}
.sp-avatars img:first-child { margin-left: 0; }
.sp-text { font-size: 0.82rem; color: #8BA0B8; line-height: 1.45; }
.sp-text strong { color: #E8EDF2; display: block; }
.sp-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
  margin-right: 5px;
  box-shadow: 0 0 5px #22c55e;
}
.sp-blurb {
  font-size: 11px;
  color: #6B7280;
  text-align: center;
  line-height: 1.7;
  max-width: 320px;
  margin: 0 auto 20px;
}

/* ── Trust strip ── */
.lp-trust-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 20px;
  padding: 18px 0 10px;
}
.lp-trust-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem;
  color: #4A6080;
}
.lp-check { color: #00C896; }
</style>
"""

# ── SVG background via st.html() (only SVG here, nothing else) ───────────────
LAB_SVG = """
<svg id="lab-bg-svg" viewBox="0 0 800 900" preserveAspectRatio="xMidYMid slice"
     xmlns="http://www.w3.org/2000/svg" aria-hidden="true">

  <!-- Orbital rings: top-right -->
  <circle cx="740" cy="90" r="80" fill="none" stroke="#00B4D8" stroke-width="0.7" opacity="0.2"/>
  <circle cx="740" cy="90" r="55" fill="none" stroke="#00B4D8" stroke-width="0.5" opacity="0.14"/>
  <circle cx="740" cy="90" r="8"  fill="#00B4D8" opacity="0.28"/>
  <line x1="740" y1="10" x2="740" y2="170" stroke="#00B4D8" stroke-width="0.4" opacity="0.12"/>
  <line x1="660" y1="90" x2="820" y2="90"  stroke="#00B4D8" stroke-width="0.4" opacity="0.12"/>

  <!-- Orbital rings: bottom-left -->
  <circle cx="60" cy="780" r="70" fill="none" stroke="#F5A623" stroke-width="0.7" opacity="0.18"/>
  <circle cx="60" cy="780" r="45" fill="none" stroke="#F5A623" stroke-width="0.5" opacity="0.12"/>
  <circle cx="60" cy="780" r="6"  fill="#F5A623" opacity="0.25"/>

  <!-- Orbital rings: mid-right -->
  <circle cx="790" cy="520" r="60" fill="none" stroke="#00C896" stroke-width="0.6" opacity="0.16"/>
  <circle cx="790" cy="520" r="38" fill="none" stroke="#00C896" stroke-width="0.4" opacity="0.10"/>
  <circle cx="790" cy="520" r="5"  fill="#00C896" opacity="0.25"/>

  <!-- Flask: top-left -->
  <g opacity="0.28" transform="translate(28, 40)">
    <line x1="20" y1="0"  x2="20" y2="55" stroke="#1F2D3D" stroke-width="1.2"/>
    <line x1="36" y1="0"  x2="36" y2="55" stroke="#1F2D3D" stroke-width="1.2"/>
    <line x1="14" y1="0"  x2="42" y2="0"  stroke="#1F2D3D" stroke-width="1.2"/>
    <polygon points="20,55 8,95 48,95 36,55" fill="#0D1117" stroke="#1F2D3D" stroke-width="1"/>
    <polygon points="20,55 10,90 46,90 36,55" fill="#00B4D8" opacity="0.12"/>
    <ellipse cx="28" cy="93" rx="20" ry="5" fill="none" stroke="#00B4D8" stroke-width="0.7" opacity="0.4"/>
    <ellipse cx="28" cy="97" rx="20" ry="5" fill="none" stroke="#00B4D8" stroke-width="0.5" opacity="0.25"/>
    <circle cx="18" cy="72" r="2.5" fill="#00B4D8" opacity="0.5"/>
    <circle cx="34" cy="80" r="1.8" fill="#00B4D8" opacity="0.35"/>
    <circle cx="24" cy="85" r="1.4" fill="#00B4D8" opacity="0.28"/>
  </g>

  <!-- Flask: bottom-right -->
  <g opacity="0.22" transform="translate(690, 700)">
    <line x1="18" y1="0"  x2="18" y2="48" stroke="#1F2D3D" stroke-width="1"/>
    <line x1="32" y1="0"  x2="32" y2="48" stroke="#1F2D3D" stroke-width="1"/>
    <line x1="12" y1="0"  x2="38" y2="0"  stroke="#1F2D3D" stroke-width="1"/>
    <polygon points="18,48 7,82 43,82 32,48" fill="#0D1117" stroke="#1F2D3D" stroke-width="0.9"/>
    <polygon points="18,48 9,78 41,78 32,48" fill="#F5A623" opacity="0.10"/>
    <ellipse cx="25" cy="80" rx="18" ry="4.5" fill="none" stroke="#F5A623" stroke-width="0.7" opacity="0.35"/>
    <circle cx="16" cy="62" r="2"   fill="#F5A623" opacity="0.45"/>
    <circle cx="30" cy="70" r="1.5" fill="#F5A623" opacity="0.30"/>
  </g>

  <!-- Test tube: right side -->
  <g opacity="0.20" transform="translate(770, 200)">
    <rect x="0"  y="0"  width="14" height="50" rx="2" fill="#0D1117" stroke="#1F2D3D" stroke-width="0.9"/>
    <rect x="0"  y="28" width="14" height="22" rx="2" fill="#00C896" opacity="0.18"/>
    <rect x="-3" y="-5" width="20" height="8"  rx="2" fill="#0D1117" stroke="#1F2D3D" stroke-width="0.8"/>
    <ellipse cx="7" cy="50" rx="7" ry="3" fill="#00C896" opacity="0.3"/>
  </g>

  <!-- Test tube: left-mid (rotated) -->
  <g opacity="0.18" transform="translate(15, 390) rotate(-20)">
    <rect x="0"  y="0"  width="12" height="44" rx="2" fill="#0D1117" stroke="#1F2D3D" stroke-width="0.8"/>
    <rect x="0"  y="24" width="12" height="20" rx="2" fill="#F5A623" opacity="0.15"/>
    <rect x="-2" y="-4" width="16" height="7"  rx="2" fill="#0D1117" stroke="#1F2D3D" stroke-width="0.7"/>
    <ellipse cx="6" cy="44" rx="6" ry="2.5" fill="#F5A623" opacity="0.25"/>
  </g>

  <!-- Neural net: top-center -->
  <g opacity="0.16" transform="translate(360, 18)">
    <circle cx="0"  cy="0"  r="5" fill="#0D1117" stroke="#00B4D8" stroke-width="0.8"/>
    <circle cx="50" cy="0"  r="5" fill="#0D1117" stroke="#00B4D8" stroke-width="0.8"/>
    <circle cx="25" cy="32" r="5" fill="#0D1117" stroke="#F5A623"  stroke-width="0.8"/>
    <circle cx="25" cy="64" r="5" fill="#0D1117" stroke="#00C896"  stroke-width="0.8"/>
    <line x1="0"  y1="0"  x2="25" y2="32" stroke="#8BA0B8" stroke-width="0.5"/>
    <line x1="50" y1="0"  x2="25" y2="32" stroke="#8BA0B8" stroke-width="0.5"/>
    <line x1="25" y1="32" x2="25" y2="64" stroke="#8BA0B8" stroke-width="0.5"/>
  </g>

  <!-- Neural net: bottom-center -->
  <g opacity="0.14" transform="translate(370, 820)">
    <circle cx="0"  cy="0"  r="4" fill="#0D1117" stroke="#00C896" stroke-width="0.7"/>
    <circle cx="40" cy="0"  r="4" fill="#0D1117" stroke="#00C896" stroke-width="0.7"/>
    <circle cx="20" cy="26" r="4" fill="#0D1117" stroke="#F5A623"  stroke-width="0.7"/>
    <line x1="0"  y1="0"  x2="20" y2="26" stroke="#2A4050" stroke-width="0.5"/>
    <line x1="40" y1="0"  x2="20" y2="26" stroke="#2A4050" stroke-width="0.5"/>
  </g>

  <!-- Circuit traces: top-right -->
  <g opacity="0.14" stroke="#1F2D3D" stroke-width="0.7" fill="none">
    <polyline points="580,10 580,40 640,40 640,70 700,70"/>
    <circle cx="580" cy="10" r="2.5" fill="#00B4D8" opacity="0.5"  stroke="none"/>
    <circle cx="640" cy="40" r="2.5" fill="#1F2D3D" stroke="#00B4D8" stroke-width="0.6"/>
    <circle cx="700" cy="70" r="2.5" fill="#00B4D8" opacity="0.4"  stroke="none"/>
  </g>

  <!-- Circuit traces: bottom-left -->
  <g opacity="0.13" stroke="#1F2D3D" stroke-width="0.7" fill="none">
    <polyline points="30,700 30,660 90,660 90,630 150,630"/>
    <circle cx="30"  cy="700" r="2.5" fill="#F5A623" opacity="0.45" stroke="none"/>
    <circle cx="90"  cy="660" r="2.5" fill="#1F2D3D" stroke="#F5A623" stroke-width="0.6"/>
    <circle cx="150" cy="630" r="2.5" fill="#F5A623" opacity="0.35" stroke="none"/>
  </g>

  <!-- Circuit traces: mid-left -->
  <g opacity="0.12" stroke="#1F2D3D" stroke-width="0.6" fill="none">
    <polyline points="0,450 50,450 50,490 110,490"/>
    <circle cx="0"   cy="450" r="2" fill="#00C896" opacity="0.4"  stroke="none"/>
    <circle cx="50"  cy="490" r="2" fill="#1F2D3D" stroke="#00C896" stroke-width="0.6"/>
    <circle cx="110" cy="490" r="2" fill="#00C896" opacity="0.3"  stroke="none"/>
  </g>

  <!-- Atom: mid-left -->
  <g opacity="0.16" transform="translate(0, 250)">
    <circle cx="35" cy="35" r="5" fill="#F5A623" opacity="0.5"/>
    <ellipse cx="35" cy="35" rx="30" ry="10" fill="none" stroke="#F5A623" stroke-width="0.7"
             transform="rotate(0, 35, 35)"/>
    <ellipse cx="35" cy="35" rx="30" ry="10" fill="none" stroke="#F5A623" stroke-width="0.7"
             transform="rotate(60, 35, 35)"/>
    <ellipse cx="35" cy="35" rx="30" ry="10" fill="none" stroke="#F5A623" stroke-width="0.7"
             transform="rotate(120, 35, 35)"/>
  </g>

  <!-- Atom: right-bottom -->
  <g opacity="0.13" transform="translate(720, 600)">
    <circle cx="35" cy="35" r="4" fill="#00B4D8" opacity="0.45"/>
    <ellipse cx="35" cy="35" rx="28" ry="9" fill="none" stroke="#00B4D8" stroke-width="0.6"
             transform="rotate(0, 35, 35)"/>
    <ellipse cx="35" cy="35" rx="28" ry="9" fill="none" stroke="#00B4D8" stroke-width="0.6"
             transform="rotate(60, 35, 35)"/>
    <ellipse cx="35" cy="35" rx="28" ry="9" fill="none" stroke="#00B4D8" stroke-width="0.6"
             transform="rotate(120, 35, 35)"/>
  </g>

  <!-- Dashed connectors -->
  <line x1="740" y1="170" x2="700" y2="200" stroke="#1F2D3D" stroke-width="0.4"
        stroke-dasharray="3 6" opacity="0.18"/>
  <line x1="60"  y1="710" x2="90"  y2="630" stroke="#1F2D3D" stroke-width="0.4"
        stroke-dasharray="3 6" opacity="0.14"/>
  <line x1="385" y1="82"  x2="385" y2="120" stroke="#1F2D3D" stroke-width="0.4"
        stroke-dasharray="2 5" opacity="0.12"/>
</svg>
"""

ICON_STRIP_HTML = """
<div class="lab-icon-strip">
  <div class="lab-icon-pill">
    <svg width="11" height="14" viewBox="0 0 11 14" fill="none" xmlns="http://www.w3.org/2000/svg">
      <line x1="3.5" y1="0" x2="3.5" y2="5.5" stroke="#00B4D8" stroke-width="1.1" stroke-linecap="round"/>
      <line x1="7.5" y1="0" x2="7.5" y2="5.5" stroke="#00B4D8" stroke-width="1.1" stroke-linecap="round"/>
      <line x1="1.5" y1="0" x2="9.5" y2="0"   stroke="#00B4D8" stroke-width="1.1" stroke-linecap="round"/>
      <polygon points="3.5,5.5 0.5,12 10.5,12 7.5,5.5" fill="none" stroke="#00B4D8"
               stroke-width="0.9" stroke-linejoin="round"/>
      <ellipse cx="5.5" cy="12" rx="4.5" ry="1.2" fill="none" stroke="#00B4D8"
               stroke-width="0.6" opacity="0.5"/>
    </svg>
    Flask lab
  </div>
  <div class="lab-icon-pill">
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7" cy="7" r="2" stroke="#F5A623" stroke-width="1"/>
      <ellipse cx="7" cy="7" rx="6" ry="2.2" fill="none" stroke="#F5A623" stroke-width="0.8"
               transform="rotate(-30, 7, 7)" opacity="0.6"/>
      <ellipse cx="7" cy="7" rx="6" ry="2.2" fill="none" stroke="#F5A623" stroke-width="0.8"
               transform="rotate(30, 7, 7)" opacity="0.6"/>
      <ellipse cx="7" cy="7" rx="6" ry="2.2" fill="none" stroke="#F5A623" stroke-width="0.8"
               opacity="0.45"/>
    </svg>
    AI/ML circuits
  </div>
  <div class="lab-icon-pill">
    <svg width="14" height="12" viewBox="0 0 14 12" fill="none" xmlns="http://www.w3.org/2000/svg">
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
    <svg width="14" height="10" viewBox="0 0 14 10" fill="none" xmlns="http://www.w3.org/2000/svg">
      <polyline points="0,7 3,7 4.5,1.5 7,9 9.5,4 11,7 14,7"
                stroke="#8BA0B8" stroke-width="0.9"
                stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    Live signals
  </div>
</div>
"""


def show():
    apply_css()

    # 1. Inject CSS into the main Streamlit DOM via st.markdown
    #    (st.markdown <style> tags reach the real page DOM, unlike st.html iframes)
    st.markdown(LAB_CSS, unsafe_allow_html=True)

    # 2. Inject the SVG background via st.html
    #    It uses position:fixed so it sits behind all Streamlit content
    #    without needing to wrap anything
    st.html(LAB_SVG)

    # 3. Hero — plain markdown, CSS classes already injected above
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

    # 4. Icon strip
    st.markdown(ICON_STRIP_HTML, unsafe_allow_html=True)

    # 5. Avatar strip — build img tags, inject via markdown
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
        <div class="sp-wrap">
          <div class="sp-avatars">{imgs_html}</div>
          <div class="sp-text">
            <span><span class="sp-dot"></span>Actively Used by 100+ Builders</span>
          </div>
        </div>
        <p class="sp-blurb">
          Join the builders turning
          <span style="color:#FFD700;">ideas into real products, careers, and startups</span>
          — from scratch, with grit and resilience, in the most creative way.
        </p>
        """, unsafe_allow_html=True)

    # ── Registration & Login expander ──────────────────────
    with st.expander("Get Started Here👇: Registration & Login 🔐", expanded=False):

        tab_register, tab_login = st.tabs(
            ["✦ New Registration", "→ Already Registered"]
        )

        # ── REGISTRATION TAB ──
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

        # ── LOGIN TAB ──
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

    # ── Trust strip ─────────────────────────────────────────
    st.markdown("""
    <div class="lp-trust-strip">
      <div class="lp-trust-item"><span class="lp-check">✓</span> No password needed</div>
      <div class="lp-trust-item"><span class="lp-check">✓</span> Secure code access</div>
      <div class="lp-trust-item"><span class="lp-check">✓</span> 6-week program</div>
    </div>
    """, unsafe_allow_html=True)
