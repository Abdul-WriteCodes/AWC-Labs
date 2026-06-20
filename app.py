import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Crea8it — AI Career Launch Program",
    page_icon="🚀",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit chrome */
[data-testid="stSidebarNav"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Global background ── */
.stApp {
    background-color: #0D1B2A;
    color: #E8EDF2;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0A1520 !important;
    border-right: 1px solid #1A2E44;
}
[data-testid="stSidebar"] * {
    color: #A0B4C8 !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #E8EDF2 !important;
    font-size: 0.9rem;
    padding: 6px 0;
}

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #E8EDF2 !important;
}
h2 { font-size: 1.8rem !important; font-weight: 700 !important; }
h3 { font-size: 1.3rem !important; font-weight: 600 !important; }
p, li, span, div { color: #C8D6E0; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #F4A022, #E8860A) !important;
    color: #0D1B2A !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #FFB340, #F4A022) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(244, 160, 34, 0.3) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #1A3A52 !important;
    color: #A0B4C8 !important;
}

/* ── Form inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #0A1520 !important;
    border: 1px solid #1A3A52 !important;
    border-radius: 8px !important;
    color: #E8EDF2 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00B4D8 !important;
    box-shadow: 0 0 0 2px rgba(0, 180, 216, 0.15) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label {
    color: #A0B4C8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0A1520 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #1A3A52 !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 7px !important;
    color: #7A94A8 !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 6px 14px !important;
}
.stTabs [aria-selected="true"] {
    background-color: #F4A022 !important;
    color: #0D1B2A !important;
    font-weight: 700 !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background-color: #0A1520 !important;
    border: 1px solid #1A3A52 !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #7A94A8 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #F4A022 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #00B4D8, #F4A022) !important;
    border-radius: 4px !important;
}
.stProgress > div > div > div {
    background-color: #1A3A52 !important;
    border-radius: 4px !important;
}

/* ── Alerts / info boxes ── */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
}
[data-testid="stInfo"] {
    background-color: rgba(0, 180, 216, 0.08) !important;
    border-left: 3px solid #00B4D8 !important;
    color: #A0C4D8 !important;
}
[data-testid="stSuccess"] {
    background-color: rgba(0, 200, 120, 0.08) !important;
    border-left: 3px solid #00C878 !important;
    color: #80D8B0 !important;
}
[data-testid="stWarning"] {
    background-color: rgba(244, 160, 34, 0.08) !important;
    border-left: 3px solid #F4A022 !important;
    color: #D4A060 !important;
}
[data-testid="stError"] {
    background-color: rgba(220, 60, 60, 0.08) !important;
    border-left: 3px solid #DC3C3C !important;
    color: #D08080 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background-color: #0A1520 !important;
    border: 1px solid #1A3A52 !important;
    border-radius: 8px !important;
    color: #A0B4C8 !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background-color: #0A1520 !important;
    border: 1px solid #1A3A52 !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Divider ── */
hr {
    border-color: #1A3A52 !important;
    margin: 1.5rem 0 !important;
}

/* ── Checkbox ── */
.stCheckbox label { color: #C8D6E0 !important; }

/* ── Dataframe ── */
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #F4A022 !important; }

/* ── Selectbox dropdown ── */
[data-baseweb="select"] > div {
    background-color: #0A1520 !important;
    border-color: #1A3A52 !important;
}
[data-baseweb="menu"] {
    background-color: #0A1520 !important;
    border: 1px solid #1A3A52 !important;
}
[data-baseweb="option"]:hover {
    background-color: #1A3A52 !important;
}
</style>
""", unsafe_allow_html=True)

from utils.auth import is_logged_in, is_admin
import pages.register as register
import pages.dashboard as dashboard
import pages.admin as admin

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding: 8px 0 16px 0;">
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; font-weight: 700; color: #F4A022; letter-spacing: -0.02em;">
                Crea<span style="color: #00B4D8;">8</span>it
            </div>
            <div style="font-size: 0.72rem; color: #4A6478; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px;">
                AI Career Launch Program
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: #0A1520; border: 1px solid #1A3A52; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
            <div style="font-size: 0.72rem; color: #4A6478; text-transform: uppercase; letter-spacing: 0.08em;">Cohort</div>
            <div style="font-size: 0.9rem; color: #E8EDF2; font-weight: 600; margin-top: 2px;">Cohort 1 · 6 Weeks</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    if is_logged_in():
        page = "Dashboard"
    elif is_admin():
        page = "Admin"
    else:
        page = st.radio("", ["Register / Log in", "Admin"], label_visibility="collapsed")

    st.divider()
    st.markdown("""
        <div style="font-size: 0.72rem; color: #2A4A5E; text-align: center; padding-top: 8px;">
            Powered by <span style="color: #F4A022;">Crea8it</span>
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
