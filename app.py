# ============================================================
#  SME DASHBOARD — app.py
#  Lightweight Business Intelligence SaaS for SMEs
#  Stack: Streamlit · Supabase (PostgreSQL) · Plotly · Pandas
# ============================================================

import streamlit as st
import bcrypt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
import re
import secrets
import string
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from supabase import create_client, Client

# ─────────────────────────────────────────────
#  APP CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BizPulse — SME Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Supabase table names
TBL_USERS    = "users"
TBL_PRODUCTS = "products"
TBL_SALES    = "sales"
TBL_EXPENSES = "expenses"
TBL_PAYMENTS = "payments"
TBL_RESTOCK  = "restock_log"

# Plan pricing & Flutterwave links
PAYMENT_DETAILS = {
    "monthly_price":      1500,
    "yearly_price":       15000,
    "trial_days":         14,
    # ── Paste your Flutterwave payment links below ──
    "flutterwave_monthly": "https://flutterwave.com/pay/YOUR_MONTHLY_LINK",
    "flutterwave_yearly":  "https://flutterwave.com/pay/YOUR_YEARLY_LINK",
}

# Admin credentials from secrets
ADMIN_EMAIL    = st.secrets["admin"]["email"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]
ADMIN_BIZ_ID   = st.secrets["admin"]["business_id"]


# ─────────────────────────────────────────────
#  GLOBAL STYLES
# ─────────────────────────────────────────────
def inject_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');

/* ── CSS Variables ── */
:root {
--obsidian:    #080B0F;
--deep:        #0D1117;
--surface:     #111827;
--surface2:    #1A2332;
--border:      #1F2D3D;
--border2:     #2D3F55;
--gold:        #F5A623;
--gold-dim:    #C4831A;
--gold-glow:   rgba(245,166,35,0.15);
--jade:        #00C896;
--jade-dim:    rgba(0,200,150,0.12);
--ruby:        #FF4D6D;
--ruby-dim:    rgba(255,77,109,0.12);
--text-primary: #F0F4F8;
--text-secondary: #8BA0B8;
--text-muted:   #4A6080;
--font-display: 'Syne', sans-serif;
--font-body:    'DM Sans', sans-serif;
--font-mono:    'DM Mono', monospace;
}

/* ── Base Reset ── */
html, body, [class*="css"], .stApp {
font-family: var(--font-body);
background-color: var(--deep) !important;
color: var(--text-primary);
}
#MainMenu, footer { visibility: hidden; }

/* Keep header and ALL its children fully visible — sidebar toggle lives here */
header, [data-testid="stHeader"] {
background:  rgba(8,11,15,0.95) !important;
visibility:  visible !important;
display:     flex    !important;
opacity:     1       !important;
z-index:     999990  !important;
backdrop-filter: blur(8px);
border-bottom: 1px solid #1F2D3D;
}
/* Do NOT hide the toolbar — it contains the sidebar toggle button */
header [data-testid="stToolbar"],
[data-testid="stHeader"] [data-testid="stToolbar"] {
visibility:  visible !important;
display:     flex    !important;
opacity:     1       !important;
}

/* Ensure every possible Streamlit sidebar toggle selector is visible */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarToggle"],
[data-testid="stSidebarToggleButton"],
button[aria-label="Open sidebar"],
button[aria-label="Close sidebar"],
button[aria-label="collapse sidebar"],
button[aria-label="expand sidebar"] {
display:        flex   !important;
visibility:     visible !important;
opacity:        1      !important;
pointer-events: auto   !important;
}

/* Custom sidebar tab injected by JS below */
#bpSidebarTab {
position: fixed;
top: 50vh;
left: 0;
transform: translateY(-50%);
z-index: 999999;
background: #111827;
border: 1px solid #2D3F55;
border-left: none;
border-radius: 0 10px 10px 0;
padding: 0.6rem 0.45rem;
cursor: pointer;
box-shadow: 4px 0 16px rgba(0,0,0,0.5);
display: flex;
align-items: center;
justify-content: center;
transition: background 0.15s, border-color 0.15s;
}
#bpSidebarTab:hover { background:#1A2332; border-color:#F5A623; }
#bpSidebarTab svg   { width:18px; height:18px; fill:#F5A623; }
.block-container {
padding-top: 1.5rem !important;
padding-bottom: 3rem !important;
max-width: 1280px;
}

/* ── Mobile Responsive ── */
@media (max-width: 768px) {
.block-container {
padding-left: 0.75rem !important;
padding-right: 0.75rem !important;
padding-top: 0.75rem !important;
}
.kpi-card { padding: 1rem 1.1rem; margin-bottom: 0.6rem; }
.kpi-value { font-size: 1.4rem; }
.pricing-grid { flex-direction: column; align-items: center; }
.pricing-card { max-width: 100%; min-width: unset; width: 100%; }
.pricing-card.featured { transform: translateY(0); }
[data-testid="stSidebar"] { width: 240px !important; }
.login-value-grid {
grid-template-columns: 1fr 1fr !important;
gap: 0.6rem !important;
}
.login-feature-strip {
flex-direction: column !important;
gap: 0.5rem !important;
}
}
@media (max-width: 480px) {
.kpi-value { font-size: 1.2rem; }
.login-value-grid { grid-template-columns: 1fr 1fr !important; }
}

/* ── Streamlit input overrides ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stTextArea textarea {
background: var(--surface) !important;
border: 1px solid var(--border2) !important;
border-radius: 10px !important;
color: var(--text-primary) !important;
font-family: var(--font-body) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
border-color: var(--gold) !important;
box-shadow: 0 0 0 3px var(--gold-glow) !important;
}
label, .stRadio label, .stCheckbox label {
color: var(--text-secondary) !important;
font-family: var(--font-body) !important;
font-size: 0.85rem !important;
font-weight: 500 !important;
}
.stRadio > div { gap: 0.5rem; }

/* ── KPI Cards ── */
.kpi-card {
background: var(--surface);
border: 1px solid var(--border);
border-radius: 16px;
padding: 1.4rem 1.6rem;
color: var(--text-primary);
margin-bottom: 1rem;
position: relative;
overflow: hidden;
transition: border-color 0.2s, transform 0.2s;
}
.kpi-card::before {
content: '';
position: absolute;
top: 0; left: 0; right: 0;
height: 2px;
background: linear-gradient(90deg, var(--gold), transparent);
opacity: 0.6;
}
.kpi-card:hover {
border-color: var(--border2);
transform: translateY(-2px);
}
.kpi-label {
font-size: 0.7rem;
font-weight: 600;
letter-spacing: 0.12em;
text-transform: uppercase;
color: var(--text-muted);
margin-bottom: 0.5rem;
font-family: var(--font-body);
}
.kpi-value {
font-size: 1.85rem;
font-weight: 700;
color: var(--text-primary);
font-family: var(--font-mono);
line-height: 1.1;
letter-spacing: -0.02em;
}
.kpi-sub {
font-size: 0.75rem;
color: var(--text-muted);
margin-top: 0.4rem;
font-family: var(--font-body);
}
.kpi-positive { color: var(--jade) !important; }
.kpi-negative { color: var(--ruby) !important; }

/* ── Alert Cards ── */
.alert-low {
background: rgba(245,166,35,0.08);
border: 1px solid rgba(245,166,35,0.25);
border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;
color: #F5A623; font-size: 0.85rem;
}
.alert-critical {
background: var(--ruby-dim);
border: 1px solid rgba(255,77,109,0.3);
border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;
color: #FF4D6D; font-size: 0.85rem;
}
.alert-success {
background: var(--jade-dim);
border: 1px solid rgba(0,200,150,0.3);
border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;
color: var(--jade); font-size: 0.85rem;
}

/* ── Section Headers ── */
.section-header {
font-size: 1rem; font-weight: 700;
font-family: var(--font-display);
color: var(--text-primary);
margin: 1.75rem 0 0.875rem 0;
padding-bottom: 0.5rem;
border-bottom: 1px solid var(--border);
letter-spacing: -0.01em;
}

/* ── Page Title ── */
.page-title {
font-size: 1.75rem; font-weight: 800;
font-family: var(--font-display);
color: var(--text-primary);
margin-bottom: 0.2rem;
letter-spacing: -0.03em;
}
.page-subtitle {
font-size: 0.875rem;
color: var(--text-secondary);
margin-bottom: 1.5rem;
}

/* ── Auth Card ── */
.auth-card {
max-width: 480px; margin: 2rem auto;
background: var(--surface);
border-radius: 20px;
padding: 2.5rem;
box-shadow: 0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px var(--border);
border: 1px solid var(--border2);
}
.auth-logo {
font-size: 1.75rem; font-weight: 800;
font-family: var(--font-display);
color: var(--text-primary);
text-align: center; margin-bottom: 0.25rem;
letter-spacing: -0.04em;
}
.auth-tagline {
text-align: center;
color: var(--text-muted);
font-size: 0.85rem; margin-bottom: 2rem;
}

/* ── Auth form wrap ── */
.auth-form-wrap {
max-width: 480px; margin: 0 auto;
background: var(--surface);
border-radius: 20px;
padding: 2.5rem;
box-shadow: 0 32px 80px rgba(0,0,0,0.5);
border: 1px solid var(--border2);
}

/* ── Stock Status Pills ── */
.stock-ok      { background:var(--jade-dim); color:var(--jade); padding:3px 10px; border-radius:99px; font-size:0.72rem; font-weight:600; border:1px solid rgba(0,200,150,0.2); }
.stock-low     { background:rgba(245,166,35,0.1); color:var(--gold); padding:3px 10px; border-radius:99px; font-size:0.72rem; font-weight:600; border:1px solid rgba(245,166,35,0.2); }
.stock-critical { background:var(--ruby-dim); color:var(--ruby); padding:3px 10px; border-radius:99px; font-size:0.72rem; font-weight:600; border:1px solid rgba(255,77,109,0.2); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
background: var(--obsidian) !important;
border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
color: var(--text-secondary) !important;
font-family: var(--font-body) !important;
}
[data-testid="stSidebar"] .stButton > button {
background: transparent !important;
border: 1px solid var(--border) !important;
color: var(--text-secondary) !important;
text-align: left !important;
border-radius: 10px !important;
font-weight: 500 !important;
transition: all 0.15s !important;
padding: 0.6rem 1rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
border-color: var(--gold) !important;
color: var(--gold) !important;
background: var(--gold-glow) !important;
}

/* ── Buttons ── */
.stButton > button {
border-radius: 10px !important;
font-weight: 600 !important;
font-family: var(--font-body) !important;
transition: all 0.2s !important;
letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"] {
background: var(--gold) !important;
border: none !important;
color: #080B0F !important;
font-weight: 700 !important;
box-shadow: 0 4px 20px rgba(245,166,35,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
background: #FFB83F !important;
box-shadow: 0 6px 28px rgba(245,166,35,0.5) !important;
transform: translateY(-1px) !important;
}
.stLinkButton > a {
background: var(--gold) !important;
color: #080B0F !important;
font-weight: 700 !important;
border-radius: 10px !important;
border: none !important;
box-shadow: 0 4px 20px rgba(245,166,35,0.35) !important;
}
.stLinkButton > a:hover {
background: #FFB83F !important;
box-shadow: 0 6px 28px rgba(245,166,35,0.5) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
background: var(--surface) !important;
border-radius: 12px !important;
border: 1px solid var(--border) !important;
padding: 4px !important;
gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
background: transparent !important;
color: var(--text-muted) !important;
border-radius: 8px !important;
font-family: var(--font-body) !important;
font-weight: 500 !important;
font-size: 0.82rem !important;
}
.stTabs [aria-selected="true"] {
background: var(--surface2) !important;
color: var(--gold) !important;
border: 1px solid var(--border2) !important;
}
.stTabs [data-baseweb="tab-panel"] {
padding-top: 1.25rem !important;
}

/* ── Metrics / dataframes ── */
[data-testid="stMetricValue"] {
color: var(--text-primary) !important;
font-family: var(--font-mono) !important;
}
.stDataFrame {
border: 1px solid var(--border) !important;
border-radius: 12px !important;
overflow: hidden;
}

/* ── Dividers ── */
hr { border-color: var(--border) !important; }

/* ── Pricing Cards ── */
.pricing-grid {
display: flex; gap: 1.25rem;
justify-content: center;
flex-wrap: wrap; margin: 2rem 0;
}
.pricing-card {
background: var(--surface);
border: 1px solid var(--border2);
border-radius: 20px;
padding: 2rem 1.75rem;
flex: 1; min-width: 220px; max-width: 290px;
text-align: center;
transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
position: relative;
}
.pricing-card:hover {
transform: translateY(-4px);
box-shadow: 0 24px 48px rgba(0,0,0,0.4);
border-color: var(--border2);
}
.pricing-card.featured {
border-color: var(--gold);
background: linear-gradient(160deg, #1A1A0A 0%, #1A1505 100%);
transform: translateY(-8px);
box-shadow: 0 32px 64px rgba(245,166,35,0.12), 0 0 0 1px var(--gold);
}
.pricing-badge {
position: absolute; top: -13px; left: 50%; transform: translateX(-50%);
background: var(--gold);
color: #080B0F;
font-size: 0.62rem; font-weight: 800;
padding: 4px 14px; border-radius: 99px;
text-transform: uppercase; letter-spacing: 0.1em;
white-space: nowrap;
font-family: var(--font-body);
}
.pricing-plan-name {
font-size: 0.7rem; font-weight: 700; letter-spacing: 0.15em;
text-transform: uppercase; color: var(--text-muted);
margin-bottom: 0.75rem;
font-family: var(--font-body);
}
.pricing-price {
font-size: 2.2rem; font-weight: 700; color: var(--text-primary);
font-family: var(--font-mono); line-height: 1;
letter-spacing: -0.03em;
}
.pricing-price span {
font-size: 0.9rem; font-weight: 400; color: var(--text-muted);
font-family: var(--font-body);
}
.pricing-desc {
font-size: 0.78rem; color: var(--text-muted);
margin: 0.5rem 0 1.25rem 0;
}
.pricing-features {
list-style: none; padding: 0; margin: 0 0 1.5rem 0; text-align: left;
}
.pricing-features li {
font-size: 0.82rem; color: var(--text-secondary);
padding: 0.4rem 0; border-bottom: 1px solid var(--border);
display: flex; align-items: center; gap: 0.5rem;
}
.pricing-features li:last-child { border-bottom: none; }
.pricing-features li::before {
content: "✓"; color: var(--jade);
font-weight: 700; flex-shrink: 0;
}

/* ── Forgot password ── */
.forgot-link {
font-size: 0.82rem; color: var(--gold);
text-decoration: none; cursor: pointer; font-weight: 500;
}

/* ── Form containers ── */
[data-testid="stForm"] {
background: transparent !important;
border: none !important;
}
.stForm { border: none !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
background: var(--surface) !important;
border: 1px solid var(--border) !important;
border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
color: var(--text-secondary) !important;
font-family: var(--font-body) !important;
}

/* ── Info / Warning / Success / Error boxes ── */
[data-testid="stAlert"] {
border-radius: 12px !important;
border-left-width: 3px !important;
font-family: var(--font-body) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: var(--gold) !important; }

/* ── Plan radio button enhancement ── */
.stRadio > div > label {
background: var(--surface) !important;
border: 1px solid var(--border2) !important;
border-radius: 10px !important;
padding: 0.75rem 1rem !important;
transition: border-color 0.15s !important;
}
.stRadio > div > label:has(input:checked) {
border-color: var(--gold) !important;
background: var(--gold-glow) !important;
}

/* ── Login landing page ── */
.lp-hero { text-align:center; padding:2.5rem 1rem 1.5rem 1rem; }
.lp-logo-wrap {
display:inline-flex; align-items:center; gap:0.75rem;
margin-bottom:1.25rem;
}
.lp-logo-icon {
width:52px; height:52px; border-radius:14px;
background:linear-gradient(135deg,#F5A623,#C4831A);
display:flex; align-items:center; justify-content:center;
font-size:1.6rem; box-shadow:0 8px 28px rgba(245,166,35,0.45);
}
.lp-logo-text {
font-family:'Syne',sans-serif;
font-size:2.2rem; font-weight:800;
color:#F0F4F8; letter-spacing:-0.05em;
}
.lp-badge {
display:inline-flex; align-items:center; gap:0.45rem;
background:rgba(245,166,35,0.1); border:1px solid rgba(245,166,35,0.3);
border-radius:99px; padding:0.35rem 1rem;
font-size:0.75rem; color:#F5A623; font-weight:600;
letter-spacing:0.04em; margin-bottom:1.25rem;
}
.lp-headline {
font-family:'Syne',sans-serif;
font-size:clamp(1.7rem,5vw,2.6rem);
font-weight:800; color:#F0F4F8;
letter-spacing:-0.04em; line-height:1.15; margin-bottom:0.75rem;
}
.lp-headline span { color:#F5A623; }
.lp-sub {
font-size:1rem; color:#8BA0B8;
max-width:520px; margin:0 auto 1.75rem auto; line-height:1.65;
}
.lp-value-grid {
display:grid; grid-template-columns:repeat(4,1fr);
gap:0.75rem; max-width:720px; margin:0 auto 2rem auto;
}
.lp-value-card {
background:#111827; border:1px solid #1F2D3D;
border-radius:14px; padding:1.1rem 1rem;
text-align:center; transition:border-color 0.2s;
}
.lp-value-card:hover { border-color:#F5A623; }
.lp-value-icon { font-size:1.5rem; margin-bottom:0.4rem; }
.lp-value-title {
font-family:'Syne',sans-serif; font-size:0.8rem; font-weight:700;
color:#F0F4F8; margin-bottom:0.2rem;
}
.lp-value-desc { font-size:0.72rem; color:#4A6080; line-height:1.4; }
.lp-divider {
display:flex; align-items:center; gap:1rem;
max-width:480px; margin:0 auto 1.5rem auto;
}
.lp-divider::before, .lp-divider::after {
content:''; flex:1; border-top:1px solid #1F2D3D;
}
.lp-divider span { font-size:0.75rem; color:#4A6080; white-space:nowrap; }
.lp-trust-strip {
display:flex; justify-content:center; align-items:center;
gap:1.5rem; flex-wrap:wrap; padding:1rem 0;
border-top:1px solid #1F2D3D; margin-top:1rem;
}
.lp-trust-item { display:flex; align-items:center; gap:0.4rem; font-size:0.75rem; color:#4A6080; }
.lp-trust-item span { color:#00C896; }
@media (max-width:600px) {
.lp-value-grid { grid-template-columns:1fr 1fr !important; }
.lp-trust-strip { gap:0.75rem; }
}

</style>
    """, unsafe_allow_html=True)


def inject_sidebar_toggle():
    """
    Forces Streamlit's native sidebar toggle to remain visible and functional.
    We do NOT inject a competing custom button — the native toggle is already
    restored via CSS. This function is kept for backward compatibility.
    """
    st.markdown("""
<script>
(function() {
// Ensure Streamlit's own sidebar toggle button stays visible.
// We find it by every known selector and force visibility.
function ensureToggleVisible() {
var selectors = [
'[data-testid="collapsedControl"]',
'[data-testid="stSidebarCollapsedControl"]',
'[data-testid="stSidebarToggle"]',
'[data-testid="stSidebarToggleButton"]',
'button[aria-label="Open sidebar"]',
'button[aria-label="Close sidebar"]',
'button[aria-label="collapse sidebar"]',
'button[aria-label="expand sidebar"]'
];
selectors.forEach(function(sel) {
var el = document.querySelector(sel);
if (el) {
el.style.display    = '';
el.style.visibility = 'visible';
el.style.opacity    = '1';
el.style.pointerEvents = 'auto';
}
});
}
// Run immediately and after a short delay to catch late mounts
ensureToggleVisible();
setTimeout(ensureToggleVisible, 500);
setTimeout(ensureToggleVisible, 1500);
})();
</script>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SUPABASE SERVICE LAYER
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    """Return authenticated Supabase client. Cached for app lifetime."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)


def db_fetch(table: str, filters: dict = None) -> pd.DataFrame:
    """
    SELECT * FROM table WHERE filters.
    filters = {"column": "value"} — all AND equality conditions.
    Returns DataFrame, empty on error.
    """
    try:
        sb    = get_supabase()
        query = sb.table(table).select("*")
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        res = query.execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error reading {table}: {e}")
        return pd.DataFrame()


def db_insert(table: str, row: dict) -> bool:
    """INSERT a single row dict into table. Returns True on success."""
    try:
        sb  = get_supabase()
        res = sb.table(table).insert(row).execute()
        st.cache_data.clear()
        return bool(res.data)
    except Exception as e:
        st.error(f"❌ Error inserting into {table}: {e}")
        return False


def db_update(table: str, id_col: str, id_val: str, updates: dict) -> bool:
    """UPDATE table SET updates WHERE id_col = id_val."""
    try:
        sb = get_supabase()
        sb.table(table).update(updates).eq(id_col, id_val).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error updating {table}: {e}")
        return False


def db_delete(table: str, id_col: str, id_val: str) -> bool:
    """DELETE FROM table WHERE id_col = id_val."""
    try:
        sb = get_supabase()
        sb.table(table).delete().eq(id_col, id_val).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error deleting from {table}: {e}")
        return False


def log_payment(user_id: str, business_name: str, email: str,
                plan_type: str, amount: float, note: str = "") -> bool:
    """Insert a payment record — ground-truth revenue ledger for the platform."""
    try:
        return db_insert(TBL_PAYMENTS, {
            "payment_id":    gen_id("PAY"),
            "user_id":       user_id,
            "business_name": business_name,
            "email":         email,
            "plan_type":     plan_type,
            "amount":        amount,
            "payment_date":  datetime.now().isoformat(),
            "note":          note,
        })
    except Exception:
        return False


@st.cache_data(ttl=30, show_spinner=False)
def get_payments_df() -> pd.DataFrame:
    """Read payments table. Returns empty DataFrame on error."""
    try:
        df = db_fetch(TBL_PAYMENTS)
        if df.empty:
            return pd.DataFrame()
        df["amount"]       = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        # Supabase returns timezone-aware timestamps — parse as UTC then strip tz
        # so all comparisons stay naive-datetime consistent with the rest of the app
        df["payment_date"] = pd.to_datetime(
            df["payment_date"], errors="coerce", utc=True
        ).dt.tz_localize(None)
        return df
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────
#  UTILITY HELPERS
# ─────────────────────────────────────────────

def gen_id(prefix=""):
    """Generate a short unique ID."""
    return f"{prefix}{uuid.uuid4().hex[:10].upper()}"


def fmt_naira(amount):
    """Format a number as Nigerian Naira."""
    try:
        return f"₦{float(amount):,.2f}"
    except:
        return "₦0.00"


def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default


def parse_date(val):
    """Parse a date string to datetime, return None on failure."""
    try:
        return dateparser.parse(str(val))
    except:
        return None


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email))


# ─────────────────────────────────────────────
#  AUTH FUNCTIONS
# ─────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except:
        return False


def get_user_by_email(email: str):
    """Return user dict or None."""
    try:
        sb  = get_supabase()
        res = sb.table(TBL_USERS).select("*").ilike("email", email).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Error fetching user: {e}")
        return None


def is_subscription_active(user: dict) -> bool:
    """Check if user has active, non-expired subscription."""
    if user.get("plan_status") != "active":
        return False
    end = parse_date(user.get("subscription_end", ""))
    if end is None:
        return False
    return datetime.now() <= end


def login_user(email: str, password: str):
    """
    Validate credentials. Returns (success, user_dict, message).
    Handles admin login separately.
    """
    # Admin shortcut
    if email.lower() == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
        admin_user = {
            "user_id":      "ADMIN",
            "business_id":  ADMIN_BIZ_ID,
            "business_name":"BizPulse Admin",
            "full_name":    "Administrator",
            "email":        ADMIN_EMAIL,
            "role":         "admin",
            "plan_status":  "active",
            "subscription_end": (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d"),
        }
        return True, admin_user, "Welcome, Admin!"

    user = get_user_by_email(email)
    if not user:
        return False, None, "No account found with that email."
    if not check_password(password, str(user.get("password_hash", ""))):
        return False, None, "Incorrect password."
    return True, user, "Login successful."


def signup_user(business_name, full_name, email, password, plan_type):
    """
    Create a new user. Returns (success, message).
    Trial → active immediately. Paid plans → pending_payment.
    """
    if not validate_email(email):
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if get_user_by_email(email):
        return False, "An account with this email already exists."

    user_id     = gen_id("USR")
    business_id = gen_id("BIZ")
    now         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if plan_type == "trial":
        status = "active"
        start  = datetime.now().strftime("%Y-%m-%d")
        end    = (datetime.now() + timedelta(days=PAYMENT_DETAILS["trial_days"])).strftime("%Y-%m-%d")
    else:
        status = "pending_payment"
        start  = ""
        end    = ""

    success = db_insert(TBL_USERS, {
        "user_id":                  user_id,
        "business_id":              business_id,
        "business_name":            business_name,
        "full_name":                full_name,
        "email":                    email,
        "password_hash":            hash_password(password),
        "role":                     "owner",
        "plan_type":                plan_type,
        "plan_status":              status,
        "subscription_start":       start if start else None,
        "subscription_end":         end   if end   else None,
        "created_at":               now,
        "password_reset_requested": "no",
        "reset_requested_at":       None,
        "must_change_password":     "no",
    })
    if success:
        return True, "Account created successfully."
    return False, "Failed to create account. Please try again."


# ─────────────────────────────────────────────
#  ANALYTICS FUNCTIONS
# ─────────────────────────────────────────────

def get_sales_df(business_id: str) -> pd.DataFrame:
    """Return sales DataFrame for this business with typed columns."""
    df = db_fetch(TBL_SALES, {"business_id": business_id})
    if df.empty:
        return pd.DataFrame()
    # Supabase returns tz-aware timestamps — strip tz for naive datetime comparisons
    df["sale_date"]    = pd.to_datetime(
        df["sale_date"], errors="coerce", utc=True
    ).dt.tz_localize(None)
    df["total_amount"] = pd.to_numeric(df["total_amount"],  errors="coerce").fillna(0)
    df["gross_profit"] = pd.to_numeric(df["gross_profit"],  errors="coerce").fillna(0)
    df["quantity"]     = pd.to_numeric(df["quantity"],      errors="coerce").fillna(0)
    df["cost_total"]   = pd.to_numeric(df["cost_total"],    errors="coerce").fillna(0)
    return df



def get_products_df(business_id: str) -> pd.DataFrame:
    df = db_fetch(TBL_PRODUCTS, {"business_id": business_id})
    if df.empty:
        return pd.DataFrame()
    df["selling_price"]  = pd.to_numeric(df["selling_price"],  errors="coerce").fillna(0)
    df["cost_price"]     = pd.to_numeric(df["cost_price"],     errors="coerce").fillna(0)
    df["stock_quantity"] = pd.to_numeric(df["stock_quantity"], errors="coerce").fillna(0)
    df["reorder_level"]  = pd.to_numeric(df["reorder_level"],  errors="coerce").fillna(0)
    return df


def get_expenses_df(business_id: str) -> pd.DataFrame:
    df = db_fetch(TBL_EXPENSES, {"business_id": business_id})
    if df.empty:
        return pd.DataFrame()
    df["amount"]       = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["expense_date"] = pd.to_datetime(
        df["expense_date"], errors="coerce", utc=True
    ).dt.tz_localize(None)
    return df


def compute_kpis(sales_df: pd.DataFrame, expenses_df: pd.DataFrame):
    """Return dict of key performance metrics."""
    now   = datetime.now()
    today = now.date()

    kpis = {
        "today_revenue":   0, "week_revenue":    0, "month_revenue":  0,
        "today_profit":    0, "week_profit":     0, "month_profit":   0,
        "today_txn":       0, "week_txn":        0, "month_txn":      0,
        "week_growth":     0, "month_expenses":  0, "net_profit":     0,
        # Extended metrics
        "year_revenue":    0, "year_profit":     0, "year_txn":       0,
        "alltime_revenue": 0, "alltime_profit":  0, "alltime_txn":    0,
        "avg_daily_revenue": 0,
    }

    if sales_df.empty:
        return kpis

    df = sales_df.dropna(subset=["sale_date"])

    # Date buckets
    today_df  = df[df["sale_date"].dt.date == today]
    week_df   = df[df["sale_date"] >= (now - timedelta(days=7))]
    month_df  = df[df["sale_date"] >= (now - timedelta(days=30))]
    prev_week = df[
        (df["sale_date"] >= (now - timedelta(days=14))) &
        (df["sale_date"] <  (now - timedelta(days=7)))
    ]

    kpis["today_revenue"]  = today_df["total_amount"].sum()
    kpis["week_revenue"]   = week_df["total_amount"].sum()
    kpis["month_revenue"]  = month_df["total_amount"].sum()
    kpis["today_profit"]   = today_df["gross_profit"].sum()
    kpis["week_profit"]    = week_df["gross_profit"].sum()
    kpis["month_profit"]   = month_df["gross_profit"].sum()
    kpis["today_txn"]      = len(today_df)
    kpis["week_txn"]       = len(week_df)
    kpis["month_txn"]      = len(month_df)

    # Week-on-week growth
    prev_rev = prev_week["total_amount"].sum()
    curr_rev = kpis["week_revenue"]
    if prev_rev > 0:
        kpis["week_growth"] = ((curr_rev - prev_rev) / prev_rev) * 100

    # Expenses & net profit
    if not expenses_df.empty:
        m_exp = expenses_df[expenses_df["expense_date"] >= (now - timedelta(days=30))]
        kpis["month_expenses"] = m_exp["amount"].sum()
    kpis["net_profit"] = kpis["month_profit"] - kpis["month_expenses"]

    # Year-to-date (current calendar year Jan 1 → now)
    year_start = datetime(now.year, 1, 1)
    year_df    = df[df["sale_date"] >= year_start]
    kpis["year_revenue"] = year_df["total_amount"].sum()
    kpis["year_profit"]  = year_df["gross_profit"].sum()
    kpis["year_txn"]     = len(year_df)

    # All-time totals
    kpis["alltime_revenue"] = df["total_amount"].sum()
    kpis["alltime_profit"]  = df["gross_profit"].sum()
    kpis["alltime_txn"]     = len(df)

    # Average daily revenue — total revenue ÷ number of distinct days with sales
    active_days = df["sale_date"].dt.date.nunique()
    kpis["avg_daily_revenue"] = (
        kpis["alltime_revenue"] / active_days if active_days > 0 else 0
    )

    return kpis


def compute_insights(sales_df, products_df, expenses_df):
    """Return structured insights dict for the Insights page."""
    insights = {
        "top_products_revenue":  pd.DataFrame(),
        "top_products_qty":      pd.DataFrame(),
        "slow_movers":           pd.DataFrame(),
        "daily_trend":           pd.DataFrame(),
        "weekday_performance":   pd.DataFrame(),
        "category_revenue":      pd.DataFrame(),
        "low_stock":             pd.DataFrame(),
        "stockout_projection":   pd.DataFrame(),
        "payment_split":         pd.DataFrame(),
        "avg_daily_revenue":     0,
        "best_day":              "",
        "worst_day":             "",
    }

    if sales_df.empty:
        return insights

    df = sales_df.dropna(subset=["sale_date"]).copy()

    # Top products by revenue
    top_rev = (
        df.groupby("product_name")["total_amount"]
        .sum().reset_index()
        .sort_values("total_amount", ascending=False)
        .head(10)
    )
    insights["top_products_revenue"] = top_rev

    # Top products by quantity
    top_qty = (
        df.groupby("product_name")["quantity"]
        .sum().reset_index()
        .sort_values("quantity", ascending=False)
        .head(10)
    )
    insights["top_products_qty"] = top_qty

    # Daily trend (last 30 days)
    df["date"] = df["sale_date"].dt.date
    daily = (
        df.groupby("date")["total_amount"]
        .sum().reset_index()
        .sort_values("date")
    )
    insights["daily_trend"]        = daily
    insights["avg_daily_revenue"]  = daily["total_amount"].mean() if not daily.empty else 0

    # Weekday performance
    df["weekday"] = df["sale_date"].dt.day_name()
    wd_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    wd = (
        df.groupby("weekday")["total_amount"]
        .sum().reindex(wd_order, fill_value=0)
        .reset_index()
    )
    wd.columns = ["weekday", "revenue"]
    insights["weekday_performance"] = wd
    if not wd.empty:
        insights["best_day"]  = wd.loc[wd["revenue"].idxmax(), "weekday"]
        insights["worst_day"] = wd.loc[wd["revenue"].idxmin(), "weekday"]

    # Category revenue
    if "category" in df.columns:
        cat = (
            df.groupby("category")["total_amount"]
            .sum().reset_index()
            .sort_values("total_amount", ascending=False)
        )
        insights["category_revenue"] = cat

    # Payment split
    if "payment_method" in df.columns:
        pm = df.groupby("payment_method")["total_amount"].sum().reset_index()
        insights["payment_split"] = pm

    # Slow movers (products sold less than average in last 30 days)
    last30 = df[df["sale_date"] >= (datetime.now() - timedelta(days=30))]
    if not last30.empty:
        prod_sales = last30.groupby("product_name")["quantity"].sum().reset_index()
        avg_qty    = prod_sales["quantity"].mean()
        slow       = prod_sales[prod_sales["quantity"] < avg_qty * 0.5].sort_values("quantity")
        insights["slow_movers"] = slow

    # Low stock & stockout projection
    if not products_df.empty:
        low = products_df[
            products_df["stock_quantity"] <= products_df["reorder_level"]
        ][["product_name","stock_quantity","reorder_level","category"]].copy()
        insights["low_stock"] = low

        # Stockout projection: days_left = current_stock / avg_daily_sales
        proj_rows = []
        for _, prod in products_df.iterrows():
            prod_sales_df = df[df["product_name"] == prod["product_name"]]
            if not prod_sales_df.empty:
                days_range  = max((df["sale_date"].max() - df["sale_date"].min()).days, 1)
                avg_per_day = prod_sales_df["quantity"].sum() / days_range
                if avg_per_day > 0:
                    days_left = prod["stock_quantity"] / avg_per_day
                    proj_rows.append({
                        "product_name": prod["product_name"],
                        "stock_quantity": prod["stock_quantity"],
                        "days_until_stockout": round(days_left, 1),
                        "avg_daily_sales": round(avg_per_day, 2),
                    })
        if proj_rows:
            proj_df = pd.DataFrame(proj_rows).sort_values("days_until_stockout")
            insights["stockout_projection"] = proj_df

    return insights


# ─────────────────────────────────────────────
#  UI COMPONENT HELPERS
# ─────────────────────────────────────────────

def kpi_card(label, value, sub="", positive=None):
    sub_class = ""
    if positive is True:
        sub_class = "kpi-positive"
    elif positive is False:
        sub_class = "kpi-negative"
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">{label}</div>
<div class="kpi-value">{value}</div>
{f'<div class="kpi-sub {sub_class}">{sub}</div>' if sub else ""}
</div>
    """, unsafe_allow_html=True)


def section_header(title):
    st.markdown(f"""
<div style="
font-family:'Syne',sans-serif;
font-size:0.95rem;font-weight:700;
color:#F0F4F8;letter-spacing:-0.01em;
margin:1.75rem 0 0.875rem 0;
padding-bottom:0.5rem;
border-bottom:1px solid #1F2D3D;
display:flex;align-items:center;gap:0.5rem;
">
<span style="
display:inline-block;width:3px;height:16px;
background:#F5A623;border-radius:2px;flex-shrink:0;
"></span>
{title}
</div>
    """, unsafe_allow_html=True)


def page_header(title, subtitle=""):
    now_str = datetime.now().strftime("%A, %d %B %Y")
    st.markdown(f"""
<div style="
display:flex;justify-content:space-between;align-items:flex-start;
margin-bottom:1.5rem;padding-bottom:1rem;
border-bottom:1px solid #1F2D3D;
">
<div>
<div style="
font-family:'Syne',sans-serif;
font-size:1.6rem;font-weight:800;
color:#F0F4F8;letter-spacing:-0.04em;
line-height:1.1;margin-bottom:0.25rem;
">{title}</div>
{f'<div style="font-size:0.85rem;color:#4A6080;">{subtitle}</div>' if subtitle else ""}
</div>
<div style="
font-size:0.75rem;color:#4A6080;text-align:right;
font-family:'DM Mono',monospace;margin-top:0.35rem;
">{now_str}</div>
</div>
    """, unsafe_allow_html=True)


def stock_pill(qty, reorder):
    qty     = safe_int(qty)
    reorder = safe_int(reorder)
    if qty <= 0:
        return '<span class="stock-critical">Out of Stock</span>'
    elif qty <= reorder:
        return f'<span class="stock-low">Low — {qty} left</span>'
    else:
        return f'<span class="stock-ok">{qty} in stock</span>'


# ─────────────────────────────────────────────
#  PAGE: LOGIN
# ─────────────────────────────────────────────

def page_login():
    inject_styles()

    # ── Premium landing hero above the fold ──
    st.markdown("""
<div class="lp-hero">
<div class="lp-logo-wrap">
<div class="lp-logo-icon">📊</div>
<div class="lp-logo-text">BizPulse</div>
</div>
<div class="lp-badge">
<span>&#9679;</span> Built for Nigerian SMEs &middot; Powered by real-time data
</div>
<div class="lp-headline">
Run your business<br>like you <span>know your numbers.</span>
</div>
<div class="lp-sub">
Sales tracking, inventory control, expense management and profit analytics &#8212;
all in one dashboard designed for the way Nigerian businesses actually work.
</div>

<div class="lp-value-grid">
<div class="lp-value-card">
<div class="lp-value-icon">🛒</div>
<div class="lp-value-title">Sales Tracking</div>
<div class="lp-value-desc">Record every sale instantly. See today, weekly &amp; monthly revenue at a glance.</div>
</div>
<div class="lp-value-card">
<div class="lp-value-icon">📦</div>
<div class="lp-value-title">Inventory Control</div>
<div class="lp-value-desc">Track stock levels, get low-stock alerts and never run out of top sellers.</div>
</div>
<div class="lp-value-card">
<div class="lp-value-icon">💸</div>
<div class="lp-value-title">Expense Manager</div>
<div class="lp-value-desc">Log every expense, see where your money goes and protect your profit margins.</div>
</div>
<div class="lp-value-card">
<div class="lp-value-icon">🧠</div>
<div class="lp-value-title">Profit Insights</div>
<div class="lp-value-desc">Gross profit, net profit, best-selling products and trend reports &#8212; all automatic.</div>
</div>
</div>
</div>

<div class="lp-divider"><span>Sign in to your account</span></div>
    """, unsafe_allow_html=True)

    # ── Login form — centred, clean ──
    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        with st.form("login_form"):
            email    = st.text_input("Email address", placeholder="you@business.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Sign In →", use_container_width=True, type="primary"
            )

        if submitted:
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                with st.spinner("Authenticating…"):
                    ok, user, msg = login_user(email.strip(), password)
                if ok:
                    st.session_state.user         = user
                    st.session_state.logged_in    = True
                    if str(user.get("must_change_password", "")).lower() == "yes":
                        st.session_state.current_page = "change_password"
                    else:
                        st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error(msg)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Forgot password?", key="goto_forgot",
                         use_container_width=True):
                st.session_state.current_page = "forgot_password"
                st.rerun()
        with col_b:
            if st.button("Create account →", key="goto_signup",
                         use_container_width=True):
                st.session_state.current_page = "signup"
                st.rerun()

    # ── Trust strip ──
    st.markdown("""
<div class="lp-trust-strip">
<div class="lp-trust-item"><span>✓</span> 256-bit encrypted</div>
<div class="lp-trust-item"><span>✓</span> Your data is never shared</div>
<div class="lp-trust-item"><span>✓</span> 14-day free trial</div>
<div class="lp-trust-item"><span>✓</span> No credit card required</div>
<div class="lp-trust-item"><span>✓</span> Cancel anytime</div>
</div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PAGE: SIGNUP
# ─────────────────────────────────────────────

def page_signup():
    inject_styles()

    # ── Hero ──
    st.markdown("""
<div style="text-align:center;padding:2.5rem 1rem 0.5rem 1rem;">
<div style="display:inline-flex;align-items:center;gap:0.7rem;margin-bottom:1.25rem;">
<div style="
width:48px;height:48px;border-radius:14px;
background:linear-gradient(135deg,#F5A623,#C4831A);
display:flex;align-items:center;justify-content:center;
font-size:1.4rem;
box-shadow:0 6px 24px rgba(245,166,35,0.4);
">📊</div>
<div style="
font-family:'Syne',sans-serif;
font-size:2rem;font-weight:800;
color:#F0F4F8;letter-spacing:-0.05em;
">BizPulse</div>
</div>
<div style="
font-family:'Syne',sans-serif;
font-size:1.5rem;font-weight:700;
color:#F0F4F8;letter-spacing:-0.03em;
margin-bottom:0.6rem;line-height:1.2;
">
Know your numbers.<br>
<span style="color:#F5A623;">Grow your business.</span>
</div>
<div style="
font-size:0.9rem;color:#4A6080;
max-width:460px;margin:0 auto;line-height:1.6;
">
Sales tracking · Inventory management · Expense control ·
Profit analytics — built for Nigerian SMEs.
</div>
<div style="
display:inline-flex;align-items:center;gap:0.5rem;
margin-top:1.25rem;
background:#0D1117;border:1px solid #1F2D3D;
border-radius:99px;padding:0.4rem 1rem;
font-size:0.78rem;color:#8BA0B8;
">
<span style="color:#F5A623;">●</span>
14-day free trial · No card required · Cancel anytime
</div>
</div>
    """, unsafe_allow_html=True)

    # ── Pricing Cards ──
    st.markdown("""
<div class="pricing-grid">
<div class="pricing-card">
<div class="pricing-plan-name">Free Trial</div>
<div class="pricing-price">₦0<span>/14 days</span></div>
<div class="pricing-desc">No card required. Full access.</div>
<ul class="pricing-features">
<li>Sales recording</li>
<li>Inventory management</li>
<li>Expense tracking</li>
<li>Dashboard analytics</li>
<li>Up to 50 products</li>
</ul>
</div>

<div class="pricing-card featured">
<div class="pricing-badge">Most Popular</div>
<div class="pricing-plan-name">Monthly</div>
<div class="pricing-price">₦1,500<span>/mo</span></div>
<div class="pricing-desc">Billed monthly. Cancel anytime.</div>
<ul class="pricing-features">
<li>Everything in Trial</li>
<li>Unlimited products</li>
<li>Business insights</li>
<li>Sales trend reports</li>
<li>Low stock alerts</li>
</ul>
</div>

<div class="pricing-card">
<div class="pricing-badge" style="background:#00C896;color:#080B0F;">Save ₦3,000</div>
<div class="pricing-plan-name">Yearly</div>
<div class="pricing-price">₦15,000<span>/yr</span></div>
<div class="pricing-desc">₦1,250/month · 2 months free</div>
<ul class="pricing-features">
<li>Everything in Monthly</li>
<li>Best value plan</li>
<li>Priority activation</li>
<li>Full year coverage</li>
<li>2 months free</li>
</ul>
</div>

</div>
    """, unsafe_allow_html=True)

    # ── Signup Form ──
    st.markdown("---")
    st.markdown("### Create your account")

    # Plan selector outside the form so it shows clearly
    plan = st.radio(
        "Choose your plan",
        options=["trial", "monthly", "yearly"],
        format_func=lambda x: {
            "trial":   f"🎁 Free Trial — 14 days free, no payment",
            "monthly": f"📅 Monthly — ₦1,500/month",
            "yearly":  f"🏆 Yearly — ₦15,000/year  (save ₦3,000!)",
        }[x],
        horizontal=True,
        key="signup_plan_select",
    )

    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            business_name = st.text_input("Business name", placeholder="Mama Put Express")
            email         = st.text_input("Email address", placeholder="you@business.com")
            password      = st.text_input("Password (min 6 chars)", type="password")
        with col2:
            full_name  = st.text_input("Your full name", placeholder="Adaeze Okafor")
            confirm_pw = st.text_input("Confirm password", type="password")

        btn_label = {
            "trial":   "Start Free Trial →",
            "monthly": "Create Account & Pay Monthly →",
            "yearly":  "Create Account & Pay Yearly →",
        }.get(plan, "Create Account →")

        submitted = st.form_submit_button(btn_label, use_container_width=True, type="primary")

    if submitted:
        _plan = st.session_state.get("signup_plan_select", plan)
        if not all([business_name, full_name, email, password, confirm_pw]):
            st.error("Please fill in all fields.")
        elif password != confirm_pw:
            st.error("Passwords do not match.")
        else:
            with st.spinner("Creating your account…"):
                ok, msg = signup_user(business_name.strip(), full_name.strip(),
                                      email.strip(), password, _plan)
            if ok:
                if _plan == "trial":
                    st.success("🎉 Your 14-day free trial is active! Sign in to get started.")
                    if st.button("Go to Sign In →"):
                        st.session_state.current_page = "login"
                        st.rerun()
                else:
                    st.session_state.pending_email = email.strip()
                    st.session_state.pending_plan  = _plan
                    st.session_state.current_page  = "pending_payment"
                    st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    if st.button("Already have an account? Sign in →", use_container_width=True):
        st.session_state.current_page = "login"
        st.rerun()


# ─────────────────────────────────────────────
#  PAGE: PENDING PAYMENT
# ─────────────────────────────────────────────

def page_pending_payment():
    inject_styles()
    user   = st.session_state.get("user", {})
    plan   = user.get("plan_type") or st.session_state.get("pending_plan", "monthly")
    email  = user.get("email")    or st.session_state.get("pending_email", "")
    amount = (PAYMENT_DETAILS["yearly_price"]
              if plan == "yearly"
              else PAYMENT_DETAILS["monthly_price"])
    fw_link = (PAYMENT_DETAILS["flutterwave_yearly"]
               if plan == "yearly"
               else PAYMENT_DETAILS["flutterwave_monthly"])
    savings_note = " — save ₦3,000!" if plan == "yearly" else ""

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            "<div style='text-align:center;font-size:2rem;font-weight:800;"
            "color:#0f172a;margin-bottom:0.25rem;'>📊 BizPulse</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            "<div style='text-align:center;font-size:2.5rem;'>🎉</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='text-align:center;font-size:1.4rem;font-weight:800;"
            "color:#0f172a;margin-bottom:0.25rem;'>Account created!</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='text-align:center;color:#64748b;font-size:0.9rem;"
            "margin-bottom:1rem;'>One last step — complete your payment to activate "
            "full access.</div>",
            unsafe_allow_html=True,
        )

        # Summary box using native elements
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Plan**")
                st.markdown("**Amount**")
                st.markdown("**Email**")
            with c2:
                st.markdown(f":{plan.capitalize()}{savings_note}")
                st.markdown(f"**₦{amount:,}**")
                st.markdown(f"`{email}`")

        st.caption("🔒 Secure payment via Flutterwave. Your account will be "
                   "activated within **24 hours** after payment is confirmed.")

        st.link_button(
            f"💳 Pay ₦{amount:,} via Flutterwave →",
            url=fw_link,
            use_container_width=True,
            type="primary",
        )
        if st.button("← Back to Sign In", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()

        st.caption("Already paid? Your account will be activated shortly. "
                   "Contact support if you don't hear back within 24 hours.")



# ─────────────────────────────────────────────
#  PAGE: FORGOT PASSWORD
# ─────────────────────────────────────────────

def page_forgot_password():
    inject_styles()
    st.markdown("""
<div style="max-width:440px;margin:2.5rem auto;text-align:center;margin-bottom:1rem;">
<div style="font-size:2rem;font-weight:800;color:#0f172a;">📊 BizPulse</div>
</div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown('<div class="auth-form-wrap">', unsafe_allow_html=True)
        st.markdown("### Reset your password")
        st.markdown(
            '<div style="color:#64748b;font-size:0.875rem;margin-bottom:1.25rem;">'
            'Enter your email and we will flag your account for a password reset. '
            'You will be able to log in with a new password once it has been processed.'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.form("forgot_pw_form"):
            email     = st.text_input("Email address", placeholder="you@business.com")
            submitted = st.form_submit_button("Request Password Reset →",
                                              use_container_width=True, type="primary")

        if submitted:
            if not email:
                st.error("Please enter your email address.")
            else:
                email = email.strip().lower()
                users_df = db_fetch(TBL_USERS)
                match = users_df[users_df["email"].str.lower() == email] if not users_df.empty else pd.DataFrame()

                if match.empty:
                    # Deliberately vague — do not reveal whether email exists
                    st.success(
                        "If that email is registered, a reset request has been submitted. "
                        "You will be contacted within 24 hours."
                    )
                else:
                    user_id = match.iloc[0]["user_id"]
                    ok = db_update(TBL_USERS, "user_id", user_id, {"password_reset_requested": "yes",
                         "reset_requested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    st.cache_data.clear()
                    if ok:
                        st.success(
                            "✅ Reset request submitted! Your password will be reset within 24 hours. "
                            "You will receive a new temporary password via the contact you provided."
                        )
                    else:
                        st.error("Something went wrong. Please try again.")

        st.markdown("---")
        if st.button("← Back to Sign In", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)



# ─────────────────────────────────────────────
#  PAGE: FORCE CHANGE PASSWORD (temp password used)
# ─────────────────────────────────────────────

def page_change_password(forced=True):
    inject_styles()
    user = st.session_state.get("user", {})

    _, col, _ = st.columns([1, 2, 1])
    with col:
        if forced:
            st.markdown(
                "<div style='text-align:center;font-size:2rem;'>🔐</div>"
                "<div style='text-align:center;font-size:1.3rem;font-weight:800;"
                "color:#0f172a;margin-bottom:0.25rem;'>Set your new password</div>"
                "<div style='text-align:center;color:#64748b;font-size:0.875rem;"
                "margin-bottom:1.5rem;'>Your account was accessed with a temporary password. "
                "You must set a permanent password before continuing.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🔑 Change Password")

        with st.form("change_pw_form"):
            if not forced:
                current_pw = st.text_input("Current password", type="password")
            new_pw     = st.text_input("New password (min 6 chars)", type="password")
            confirm_pw = st.text_input("Confirm new password", type="password")
            submitted  = st.form_submit_button(
                "Set New Password →", use_container_width=True, type="primary"
            )

        if submitted:
            # Verify current password if not forced
            if not forced:
                if not check_password(current_pw, str(user.get("password_hash", ""))):
                    st.error("Current password is incorrect.")
                    st.stop()
            if not new_pw or len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            else:
                hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                ok = db_update(TBL_USERS, "user_id", user["user_id"], {
                        "password_hash":        hashed,
                        "must_change_password": "no",
                    })
                st.cache_data.clear()
                if ok:
                    # Update session so the flag is cleared
                    st.session_state.user["password_hash"]        = hashed
                    st.session_state.user["must_change_password"] = "no"
                    st.success("✅ Password updated successfully!")
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("Failed to update password. Please try again.")

        if not forced:
            if st.button("← Back", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()


# ─────────────────────────────────────────────
#  PAGE: DASHBOARD
# ─────────────────────────────────────────────

def page_dashboard():
    user        = st.session_state.user
    business_id = user["business_id"]
    now         = datetime.now()
    hour        = now.hour
    greeting    = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    first_name  = user.get("full_name", "there").split()[0]

    st.markdown(f"""
<div style="
background:linear-gradient(135deg,#0D1117 0%,#111827 100%);
border:1px solid #1F2D3D;border-radius:18px;
padding:1.75rem 2rem;margin-bottom:1.5rem;
position:relative;overflow:hidden;
">
<div style="
position:absolute;top:-40px;right:-40px;
width:200px;height:200px;border-radius:50%;
background:rgba(245,166,35,0.06);
"></div>
<div style="font-size:0.7rem;color:#4A6080;text-transform:uppercase;
letter-spacing:0.12em;font-weight:600;margin-bottom:0.4rem;
font-family:'DM Mono',monospace;">
{now.strftime("%A, %d %B %Y")}
</div>
<div style="
font-family:'Syne',sans-serif;
font-size:1.55rem;font-weight:800;color:#F0F4F8;
letter-spacing:-0.04em;margin-bottom:0.25rem;
">{greeting}, {first_name} 👋</div>
<div style="font-size:0.875rem;color:#4A6080;">
Here's your business snapshot for
<strong style="color:#8BA0B8;">{user.get("business_name","your business")}</strong>
</div>
</div>
    """, unsafe_allow_html=True)

    with st.spinner("Loading your data…"):
        sales_df    = get_sales_df(business_id)
        products_df = get_products_df(business_id)
        expenses_df = get_expenses_df(business_id)
        kpis        = compute_kpis(sales_df, expenses_df)

    # ── 4 Core KPIs ──
    if not products_df.empty:
        low_count = len(products_df[
            products_df["stock_quantity"] <= products_df["reorder_level"]
        ])
    else:
        low_count = 0

    growth = kpis["week_growth"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Today's Revenue", fmt_naira(kpis["today_revenue"]),
                 f"{kpis['today_txn']} transactions today")
    with c2:
        kpi_card("This Week", fmt_naira(kpis["week_revenue"]),
                 f"{'\u25b2' if growth >= 0 else '\u25bc'} {abs(growth):.1f}% vs last week",
                 positive=(growth >= 0))
    with c3:
        kpi_card("Net Profit (Month)", fmt_naira(kpis["net_profit"]),
                 f"After \u20a6{kpis['month_expenses']:,.0f} expenses",
                 positive=(kpis["net_profit"] >= 0))
    with c4:
        kpi_card("Low Stock Alerts", str(low_count),
                 "Products need restocking" if low_count > 0 else "All products stocked",
                 positive=(low_count == 0))
    # ── Charts ──
    if not sales_df.empty:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            section_header("Revenue Trend — Last 30 Days")
            trend_df = sales_df.copy()
            trend_df["date"] = trend_df["sale_date"].dt.date
            # Fill every day in the last 30 days so missing days show as 0
            last30 = trend_df[trend_df["sale_date"] >= (datetime.now() - timedelta(days=30))]
            daily = last30.groupby("date")["total_amount"].sum().reset_index()
            all_dates = pd.date_range(
                end=datetime.now().date(),
                periods=30, freq="D"
            ).date
            daily = (
                daily.set_index("date")
                .reindex(all_dates, fill_value=0)
                .reset_index()
                .rename(columns={"index": "date"})
            )
            daily["date_str"] = pd.to_datetime(daily["date"]).dt.strftime("%d %b")
            if not daily.empty:
                avg_rev = daily["total_amount"].mean()
                fig = go.Figure()
                # Bar for each day
                fig.add_trace(go.Bar(
                    x=daily["date_str"],
                    y=daily["total_amount"],
                    marker_color=[
                        "#F5A623" if v >= avg_rev else "#6366f1"
                        for v in daily["total_amount"]
                    ],
                    hovertemplate="%{x}<br>₦%{y:,.0f}<extra></extra>",
                ))
                # Average line
                fig.add_hline(
                    y=avg_rev,
                    line_dash="dot",
                    line_color="#00C896",
                    line_width=1.5,
                    annotation_text=f"Avg ₦{avg_rev:,.0f}",
                    annotation_position="top right",
                    annotation_font_size=11,
                    annotation_font_color="#00C896",
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=20, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(
                        tickprefix="₦",
                        gridcolor="rgba(255,255,255,0.06)",
                        tickfont=dict(size=11),
                        tickformat=",.0f",
                    ),
                    xaxis=dict(
                        type="category",
                        tickangle=-45,
                        tickfont=dict(size=10),
                        gridcolor="rgba(0,0,0,0)",
                        nticks=10,
                    ),
                    height=240,
                    bargap=0.25,
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption("■ Gold bars = above average days  ■ Purple = below average")

        with col_right:
            section_header("Sales by Payment Method")
            pm_df = (
                sales_df.groupby("payment_method")["total_amount"]
                .sum().reset_index()
            )
            if not pm_df.empty:
                fig2 = px.pie(
                    pm_df, values="total_amount", names="payment_method",
                    color_discrete_sequence=["#6366f1","#10b981","#f59e0b","#ef4444"],
                    hole=0.55,
                )
                fig2.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=280,
                    legend=dict(orientation="h", y=-0.1),
                )
                st.plotly_chart(fig2, use_container_width=True)

        # Top products
        section_header("Top Selling Products (by Revenue)")
        top_df = (
            sales_df.groupby("product_name")["total_amount"]
            .sum().reset_index()
            .sort_values("total_amount", ascending=True)
            .tail(8)
        )
        if not top_df.empty:
            fig3 = px.bar(
                top_df, x="total_amount", y="product_name",
                orientation="h",
                labels={"total_amount": "Revenue (₦)", "product_name": ""},
                color_discrete_sequence=["#6366f1"],
            )
            fig3.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickprefix="₦", gridcolor="#f1f5f9"),
                height=300,
            )
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("📭 No sales data yet. Record your first sale to see analytics here.")

    # ── Low Stock Alerts ──
    if not products_df.empty:
        low_stock = products_df[
            products_df["stock_quantity"] <= products_df["reorder_level"]
        ]
        if not low_stock.empty:
            section_header("⚠️ Low Stock Alerts")
            for _, row in low_stock.iterrows():
                qty = safe_int(row["stock_quantity"])
                lvl = safe_int(row["reorder_level"])
                css = "alert-critical" if qty <= 0 else "alert-low"
                st.markdown(
                    f'<div class="{css}">🔔 <strong>{row["product_name"]}</strong> — '
                    f'{qty} units left (reorder level: {lvl})</div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────
#  PAGE: RECORD SALE
# ─────────────────────────────────────────────

def page_record_sale():
    user        = st.session_state.user
    business_id = user["business_id"]

    page_header("🛒 Record a Sale", "Log a transaction and update inventory automatically")

    products_df = get_products_df(business_id)

    if products_df.empty:
        st.warning("You have no products yet. Add products first before recording sales.")
        if st.button("→ Go to Product Management"):
            st.session_state.current_page = "products"
            st.rerun()
        return

    # Only show in-stock products
    available = products_df[products_df["stock_quantity"] > 0].copy()
    if available.empty:
        st.error("All products are out of stock. Please restock before recording sales.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        # ── Product selector OUTSIDE the form so it re-renders reactively ──
        # When the user changes the product, Streamlit re-runs and max_qty updates immediately.
        product_options = {
            f"{r['product_name']} (Stock: {int(r['stock_quantity'])} | ₦{r['selling_price']:,.0f})": r
            for _, r in available.iterrows()
        }
        selected_label   = st.selectbox("Select product", list(product_options.keys()),
                                        key="sale_product_select")
        selected_product = product_options[selected_label]
        max_qty          = int(selected_product["stock_quantity"])

        # ── Payment method also outside so it's always current ──
        payment_method = st.selectbox(
            "Payment method", ["Cash", "Bank Transfer", "POS", "Mobile Money"],
            key="sale_payment_method"
        )

        # ── Only quantity + submit inside the form ──
        with st.form("record_sale_form", clear_on_submit=True):
            # Key is required so we can read the submitted value from
            # st.session_state — clear_on_submit resets the widget to value=1
            # on the rerun AFTER submit, but session_state still holds the
            # value that was present at the moment the button was clicked.
            quantity = st.number_input(
                f"Quantity (max {max_qty} available)",
                min_value=1,
                value=1, step=1,
                key="sale_quantity",
            )

            # Live calculation display
            unit_price   = safe_float(selected_product["selling_price"])
            cost_price   = safe_float(selected_product["cost_price"])
            total        = unit_price * quantity
            cost_total   = cost_price * quantity
            gross_profit = total - cost_total

            st.markdown(f"""
<div class="kpi-card" style="margin-top:1rem;">
<div class="kpi-label">Sale Summary</div>
<div style="display:flex; gap:2rem; margin-top:0.5rem; flex-wrap:wrap;">
<div>
<div class="kpi-label">Unit Price</div>
<div style="font-weight:700;font-size:1.1rem;color:#f1f5f9">{fmt_naira(unit_price)}</div>
</div>
<div>
<div class="kpi-label">Quantity</div>
<div style="font-weight:700;font-size:1.1rem;color:#f1f5f9">{quantity}</div>
</div>
<div>
<div class="kpi-label">Total Amount</div>
<div style="font-weight:800;font-size:1.4rem;color:#34d399">{fmt_naira(total)}</div>
</div>
<div>
<div class="kpi-label">Gross Profit</div>
<div style="font-weight:700;font-size:1.1rem;color:#a5b4fc">{fmt_naira(gross_profit)}</div>
</div>
</div>
</div>
            """, unsafe_allow_html=True)

            submitted = st.form_submit_button(
                f"✅ Record Sale — {fmt_naira(total)}", use_container_width=True, type="primary"
            )

            if submitted:
                # Read ALL widget values from session_state at the moment of
                # submission. clear_on_submit resets the widgets visually on
                # the next rerun, but session_state retains the submitted values
                # throughout the current execution — so this is always correct.
                _label    = st.session_state.get("sale_product_select", selected_label)
                _product  = product_options.get(_label, selected_product)
                _payment  = st.session_state.get("sale_payment_method", payment_method)
                _quantity = int(st.session_state.get("sale_quantity", quantity))

                # Re-read current stock from sheet to avoid race condition with stale cache
                fresh_products = get_products_df(business_id)
                fresh_row      = fresh_products[
                    fresh_products["product_id"] == _product["product_id"]
                ]
                if fresh_row.empty:
                    st.error("Product not found. Please refresh and try again.")
                    st.stop()

                current_stock = int(fresh_row.iloc[0]["stock_quantity"])
                if _quantity > current_stock:
                    st.error(
                        f"Only {current_stock} units available right now. "
                        f"Please reduce the quantity."
                    )
                    st.stop()

                sale_id = gen_id("SAL")
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Snapshot values at time of sale
                snap_unit_price   = safe_float(fresh_row.iloc[0]["selling_price"])
                snap_cost_price   = safe_float(fresh_row.iloc[0]["cost_price"])
                snap_total        = snap_unit_price * _quantity
                snap_cost_total   = snap_cost_price * _quantity
                snap_gross_profit = snap_total - snap_cost_total

                # Write sale record to Supabase
                sale_ok = db_insert(TBL_SALES, {
                    "sale_id":        sale_id,
                    "business_id":    business_id,
                    "product_id":     _product["product_id"],
                    "product_name":   _product["product_name"],
                    "quantity":       _quantity,
                    "unit_price":     snap_unit_price,
                    "total_amount":   snap_total,
                    "cost_total":     snap_cost_total,
                    "gross_profit":   snap_gross_profit,
                    "payment_method": _payment,
                    "sale_date":      datetime.now().isoformat(),
                    "recorded_by":    user.get("full_name", user.get("email", "")),
                })

                if sale_ok:
                    # Deduct stock immediately after confirmed write
                    new_stock = current_stock - _quantity
                    stock_ok  = db_update(TBL_PRODUCTS, "product_id", _product["product_id"], {"stock_quantity": new_stock})
                    # Clear cache so next page load reads fresh data
                    st.cache_data.clear()

                    if stock_ok:
                        st.success(
                            f"✅ Sale recorded! {fmt_naira(snap_total)} — "
                            f"{_product['product_name']} × {_quantity} | "
                            f"Stock remaining: {new_stock} units"
                        )
                        if new_stock <= safe_int(_product["reorder_level"]):
                            st.warning(
                                f"⚠️ Low stock: {_product['product_name']} "
                                f"is at or below reorder level ({safe_int(_product['reorder_level'])} units)."
                            )
                    else:
                        st.warning("✅ Sale recorded but stock count failed to update. "
                                   "Please manually adjust stock in Product Management.")
                else:
                    st.error("❌ Failed to write sale to database. Check your Google Sheets "
                             "connection and that the SALES tab headers match exactly.")

    with col2:
        section_header("Today's Sales")
        sales_df_today = get_sales_df(business_id)
        if not sales_df_today.empty:
            today = datetime.now().date()
            today_sales = sales_df_today[sales_df_today["sale_date"].dt.date == today]
            kpi_card("Today's Revenue",
                     fmt_naira(today_sales["total_amount"].sum()),
                     f"{len(today_sales)} transactions")

            if not today_sales.empty:
                st.markdown("**Recent transactions:**")
                recent = today_sales.sort_values("sale_date", ascending=False).head(5)
                for _, r in recent.iterrows():
                    st.markdown(
                        f"• **{r['product_name']}** × {int(r['quantity'])} "
                        f"= {fmt_naira(r['total_amount'])} _{r['payment_method']}_"
                    )
        else:
            kpi_card("Today's Revenue", "₦0.00", "No sales yet today")


def page_sales_history():
    """Sales History page: date filter, edit, delete with inventory reconciliation."""
    user        = st.session_state.user
    business_id = user["business_id"]

    page_header("📋 Sales History", "View, edit or void past transactions")

    # Force fresh fetch if a sale was just edited/voided
    if st.session_state.get("sale_feedback"):
        st.cache_data.clear()

    sales_df = get_sales_df(business_id)
    if sales_df.empty:
        st.info("📭 No sales recorded yet.")
        return

    products_df = get_products_df(business_id)

    # ── Filters ──
    fc1, fc2, fc3 = st.columns(3)
    start_date  = fc1.date_input("From", value=(datetime.now() - timedelta(days=30)).date(), key="sh_from")
    end_date    = fc2.date_input("To",   value=datetime.now().date(), key="sh_to")
    search_sale = fc3.text_input("🔍 Search product", key="sh_search", placeholder="Product name…")

    # Safely parse sale_date — drop any rows where it couldn't be parsed
    sales_df = sales_df.dropna(subset=["sale_date"])
    sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"], errors="coerce", utc=True).dt.tz_localize(None)
    sales_df = sales_df.dropna(subset=["sale_date"])

    filtered = sales_df[
        (sales_df["sale_date"].dt.date >= start_date) &
        (sales_df["sale_date"].dt.date <= end_date)
    ]
    if search_sale:
        filtered = filtered[filtered["product_name"].str.contains(search_sale, case=False, na=False)]

    filtered = filtered.sort_values("sale_date", ascending=False)

    # ── Summary KPIs ──
    sk1, sk2, sk3 = st.columns(3)
    with sk1:
        kpi_card("Revenue (filtered)", fmt_naira(filtered["total_amount"].sum()), f"{len(filtered)} transactions")
    with sk2:
        kpi_card("Profit (filtered)", fmt_naira(filtered["gross_profit"].sum()), "Gross margin")
    with sk3:
        kpi_card("Avg Sale Value", fmt_naira(filtered["total_amount"].mean() if not filtered.empty else 0), "Per transaction")

    st.markdown("---")

    if filtered.empty:
        st.info("No sales match the current filters.")
        return

    # ── Pagination ──
    SH_PAGE_SIZE = 15
    sh_total_pages = max(1, -(-len(filtered) // SH_PAGE_SIZE))
    if "sh_page" not in st.session_state:
        st.session_state.sh_page = 1
    sh_pg = st.session_state.sh_page
    page_df = filtered.iloc[(sh_pg - 1) * SH_PAGE_SIZE: sh_pg * SH_PAGE_SIZE]
    st.caption(f"Showing {len(page_df)} of {len(filtered)} sales  •  Page {sh_pg} of {sh_total_pages}")

    # ── Global feedback banner (outside expanders) ──
    if "sale_feedback" in st.session_state:
        msg = st.session_state.pop("sale_feedback")
        if msg.startswith("✅"):
            st.success(msg)
        else:
            st.error(msg)

    # ── Sale rows ──
    for _, r in page_df.iterrows():
        sale_id  = r["sale_id"]
        sale_dt  = r["sale_date"].strftime("%d %b %Y %H:%M") if pd.notna(r["sale_date"]) else "—"
        # Keep expander open if this sale was just edited
        is_expanded = st.session_state.get("last_edited_sale") == sale_id
        with st.expander(
            f"**{r['product_name']}** × {int(r['quantity'])}  |  "
            f"{fmt_naira(r['total_amount'])}  |  {r['payment_method']}  |  {sale_dt}",
            expanded=is_expanded
        ):
            # ── Edit form ──
            with st.form(f"edit_sale_{sale_id}"):
                sf1, sf2 = st.columns(2)

                # Product selector
                prod_names = products_df["product_name"].tolist() if not products_df.empty else [r["product_name"]]
                try:
                    prod_idx = prod_names.index(r["product_name"])
                except ValueError:
                    prod_idx = 0
                new_product_name = sf1.selectbox("Product", prod_names, index=prod_idx)
                new_payment      = sf2.selectbox(
                    "Payment Method",
                    ["Cash", "Bank Transfer", "POS", "Mobile Money"],
                    index=["Cash","Bank Transfer","POS","Mobile Money"].index(r["payment_method"])
                    if r["payment_method"] in ["Cash","Bank Transfer","POS","Mobile Money"] else 0
                )
                new_qty  = sf1.number_input("Quantity", min_value=1, value=int(r["quantity"]), step=1)
                new_date = sf2.date_input(
                    "Sale Date",
                    value=r["sale_date"].date() if pd.notna(r["sale_date"]) else datetime.now().date()
                )
                save_sale = st.form_submit_button("💾 Save Changes", type="primary")

            if save_sale:
                # Resolve new product details
                if not products_df.empty:
                    prod_row = products_df[products_df["product_name"] == new_product_name]
                    if not prod_row.empty:
                        new_unit_price = safe_float(prod_row.iloc[0]["selling_price"])
                        new_cost_price = safe_float(prod_row.iloc[0]["cost_price"])
                        new_product_id = prod_row.iloc[0]["product_id"]
                    else:
                        new_unit_price = safe_float(r["unit_price"])
                        new_cost_price = new_unit_price
                        new_product_id = r.get("product_id", "")
                else:
                    new_unit_price = safe_float(r["unit_price"])
                    new_cost_price = new_unit_price
                    new_product_id = r.get("product_id", "")

                old_qty        = int(r["quantity"])
                old_product_id = r.get("product_id", "")
                product_changed = (new_product_id != old_product_id)

                new_total  = new_unit_price * new_qty
                new_cost_t = new_cost_price * new_qty
                new_profit = new_total - new_cost_t

                # ── Fetch LIVE stock before any check or update ──
                live_products = get_products_df(business_id)

                # If product changed: fully restore old product stock, fully deduct new
                if product_changed:
                    # Check new product has enough stock
                    if not live_products.empty:
                        new_prod_live = live_products[live_products["product_id"] == new_product_id]
                        if not new_prod_live.empty:
                            avail = int(new_prod_live.iloc[0]["stock_quantity"])
                            if new_qty > avail:
                                st.error(f"Not enough stock for {new_product_name}. Only {avail} units available.")
                                st.stop()
                else:
                    # Same product — only check the extra qty needed
                    qty_delta = new_qty - old_qty
                    if qty_delta > 0 and not live_products.empty:
                        same_prod_live = live_products[live_products["product_id"] == new_product_id]
                        if not same_prod_live.empty:
                            avail = int(same_prod_live.iloc[0]["stock_quantity"])
                            if qty_delta > avail:
                                st.error(f"Not enough stock. Only {avail} extra units available.")
                                st.stop()

                # ── Update the sale record ──
                ok = db_update(TBL_SALES, "sale_id", sale_id, {
                    "product_id":     new_product_id,
                    "product_name":   new_product_name,
                    "quantity":       new_qty,
                    "unit_price":     new_unit_price,
                    "total_amount":   new_total,
                    "cost_total":     new_cost_t,
                    "gross_profit":   new_profit,
                    "payment_method": new_payment,
                    "sale_date":      datetime.combine(new_date, datetime.now().time()).isoformat(),
                })

                if ok:
                    # ── Reconcile stock using LIVE values ──
                    if not live_products.empty:
                        if product_changed:
                            # Restore full old_qty to old product
                            old_prod_live = live_products[live_products["product_id"] == old_product_id]
                            if not old_prod_live.empty:
                                restored = int(old_prod_live.iloc[0]["stock_quantity"]) + old_qty
                                db_update(TBL_PRODUCTS, "product_id", old_product_id, {"stock_quantity": restored})
                            # Deduct full new_qty from new product
                            new_prod_live = live_products[live_products["product_id"] == new_product_id]
                            if not new_prod_live.empty:
                                deducted = int(new_prod_live.iloc[0]["stock_quantity"]) - new_qty
                                db_update(TBL_PRODUCTS, "product_id", new_product_id, {"stock_quantity": max(0, deducted)})
                        else:
                            # Same product — apply qty delta only
                            qty_delta = new_qty - old_qty
                            same_prod_live = live_products[live_products["product_id"] == new_product_id]
                            if not same_prod_live.empty:
                                adjusted = int(same_prod_live.iloc[0]["stock_quantity"]) - qty_delta
                                db_update(TBL_PRODUCTS, "product_id", new_product_id, {"stock_quantity": max(0, adjusted)})

                    st.cache_data.clear()
                    st.session_state["sale_feedback"]   = "✅ Sale updated and inventory reconciled."
                    st.session_state["last_edited_sale"] = sale_id
                    st.rerun()
                else:
                    st.session_state["sale_feedback"]   = "❌ Failed to update sale. Please try again."
                    st.session_state["last_edited_sale"] = sale_id
                    st.rerun()

            # ── Delete / Void ──
            confirm_void_key = f"confirm_void_{sale_id}"
            if not st.session_state.get(confirm_void_key, False):
                if st.button("🗑️ Void / Delete this sale", key=f"void_{sale_id}"):
                    st.session_state[confirm_void_key] = True
                    st.rerun()
            else:
                st.warning(
                    f"⚠️ Void **{r['product_name']} × {int(r['quantity'])}** "
                    f"({fmt_naira(r['total_amount'])})? "
                    f"This will restore {int(r['quantity'])} units to stock."
                )
                vd1, vd2 = st.columns(2)
                if vd1.button("✅ Yes, void sale", key=f"yes_void_{sale_id}", type="primary"):
                    ok = db_delete(TBL_SALES, "sale_id", sale_id)
                    if ok:
                        # Fetch LIVE stock before restoring
                        live_products = get_products_df(business_id)
                        if not live_products.empty:
                            prod_live = live_products[live_products["product_id"] == r.get("product_id", "")]
                            if prod_live.empty:
                                # fallback: match by name
                                prod_live = live_products[live_products["product_name"] == r["product_name"]]
                            if not prod_live.empty:
                                restored = int(prod_live.iloc[0]["stock_quantity"]) + int(r["quantity"])
                                db_update(TBL_PRODUCTS, "product_id", prod_live.iloc[0]["product_id"], {"stock_quantity": restored})
                        st.cache_data.clear()
                        st.session_state.pop(confirm_void_key, None)
                        st.session_state["sale_feedback"] = f"✅ Sale voided. {int(r['quantity'])} units restored to stock."
                        st.rerun()
                    else:
                        st.session_state["sale_feedback"] = "❌ Failed to void sale. Please try again."
                        st.rerun()
                if vd2.button("❌ Cancel", key=f"no_void_{sale_id}"):
                    st.session_state.pop(confirm_void_key, None)
                    st.rerun()

    # ── Pagination controls ──
    if sh_total_pages > 1:
        st.markdown("---")
        pp1, pp2, pp3 = st.columns([1, 3, 1])
        if pp1.button("◀ Prev", disabled=(sh_pg <= 1), key="sh_prev"):
            st.session_state.sh_page = max(1, sh_pg - 1)
            st.rerun()
        pp2.markdown(f"<div style='text-align:center;padding-top:0.5rem;color:#8BA0B8;'>Page {sh_pg} of {sh_total_pages}</div>", unsafe_allow_html=True)
        if pp3.button("Next ▶", disabled=(sh_pg >= sh_total_pages), key="sh_next"):
            st.session_state.sh_page = min(sh_total_pages, sh_pg + 1)
            st.rerun()


# ─────────────────────────────────────────────
#  PAGE: PRODUCT MANAGEMENT
# ─────────────────────────────────────────────

def page_products():
    user        = st.session_state.user
    business_id = user["business_id"]

    page_header("📦 Product Management", "Add, edit and manage your inventory")

    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Products", "➕ Add Product", "🔄 Restock", "📜 Restock History"])

    # ── Tab 1: View All ──
    with tab1:
        products_df = get_products_df(business_id)
        if products_df.empty:
            st.info("No products yet. Add your first product in the 'Add Product' tab.")
        else:
            # Summary metrics
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                kpi_card("Total Products", str(len(products_df)), "In your catalog")
            with c2:
                total_stock_val = (products_df["stock_quantity"] * products_df["selling_price"]).sum()
                kpi_card("Inventory Value", fmt_naira(total_stock_val), "At selling price")
            with c3:
                total_cost_val = (products_df["stock_quantity"] * products_df["cost_price"]).sum()
                kpi_card("Inventory Cost", fmt_naira(total_cost_val), "At cost price")
            with c4:
                low_count = len(products_df[products_df["stock_quantity"] <= products_df["reorder_level"]])
                kpi_card("Low Stock", str(low_count), "Need restocking", positive=(low_count == 0))

            st.markdown("---")

            # Category filter + search
            search_q = st.text_input("🔍 Search products", key="prod_search", placeholder="Type product name…")
            cats = ["All"] + sorted(products_df["category"].unique().tolist())
            selected_cat = st.selectbox("Filter by category", cats)
            disp = products_df if selected_cat == "All" else products_df[products_df["category"] == selected_cat]
            if search_q:
                disp = disp[disp["product_name"].str.contains(search_q, case=False, na=False)]

            # Pagination
            PAGE_SIZE = 15
            total_pages = max(1, -(-len(disp) // PAGE_SIZE))  # ceiling division
            if "prod_page" not in st.session_state:
                st.session_state.prod_page = 1
            # Reset page if filter changes
            if st.session_state.get("_last_prod_search") != search_q or st.session_state.get("_last_prod_cat") != selected_cat:
                st.session_state.prod_page = 1
            st.session_state["_last_prod_search"] = search_q
            st.session_state["_last_prod_cat"] = selected_cat

            pg = st.session_state.prod_page
            start_idx = (pg - 1) * PAGE_SIZE
            disp_page = disp.iloc[start_idx: start_idx + PAGE_SIZE]

            st.caption(f"Showing {len(disp_page)} of {len(disp)} products  •  Page {pg} of {total_pages}")

            # Display product cards
            for _, row in disp_page.iterrows():
                with st.expander(
                    f"**{row['product_name']}** | {row['category']} | "
                    f"Stock: {int(row['stock_quantity'])} | {fmt_naira(row['selling_price'])}",
                    expanded=False
                ):
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        st.markdown(f"**Cost Price:** {fmt_naira(row['cost_price'])}")
                        st.markdown(f"**Selling Price:** {fmt_naira(row['selling_price'])}")
                        margin = safe_float(row['selling_price']) - safe_float(row['cost_price'])
                        st.markdown(f"**Margin/unit:** {fmt_naira(margin)}")
                    with ec2:
                        st.markdown(f"**Stock:** {int(row['stock_quantity'])} units")
                        st.markdown(f"**Reorder Level:** {int(row['reorder_level'])} units")
                        st.markdown(f"**Category:** {row['category']}")
                    with ec3:
                        st.markdown(
                            stock_pill(row["stock_quantity"], row["reorder_level"]),
                            unsafe_allow_html=True
                        )

                    # Edit form
                    with st.form(f"edit_{row['product_id']}"):
                        st.markdown("**Edit Product**")
                        f1, f2 = st.columns(2)
                        new_name     = f1.text_input("Product Name", value=row["product_name"])
                        new_cat      = f2.text_input("Category",     value=row["category"])
                        new_cost     = f1.number_input("Cost Price",    value=safe_float(row["cost_price"]),    min_value=0.0, step=50.0)
                        new_sell     = f2.number_input("Selling Price", value=safe_float(row["selling_price"]), min_value=0.0, step=50.0)
                        new_reorder  = f1.number_input("Reorder Level", value=safe_int(row["reorder_level"]),   min_value=0,   step=1)
                        save = st.form_submit_button("💾 Save Changes", type="primary")

                    if save:
                        ok = db_update(TBL_PRODUCTS, "product_id", row["product_id"], {
                                "product_name": new_name, "category": new_cat,
                                "cost_price": new_cost, "selling_price": new_sell,
                                "reorder_level": new_reorder,
                            })
                        st.success("Product updated!") if ok else st.error("Update failed.")
                        st.rerun()

                    confirm_key = f"confirm_del_{row['product_id']}"
                    if not st.session_state.get(confirm_key, False):
                        if st.button(f"🗑️ Delete {row['product_name']}", key=f"del_{row['product_id']}"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning(f"⚠️ Are you sure you want to delete **{row['product_name']}**? This cannot be undone.")
                        c_yes, c_no = st.columns(2)
                        if c_yes.button("✅ Yes, delete", key=f"yes_del_{row['product_id']}", type="primary"):
                            ok = db_delete(TBL_PRODUCTS, "product_id", row["product_id"])
                            st.cache_data.clear()
                            st.session_state.pop(confirm_key, None)
                            st.session_state["prod_del_msg"] = (
                                f"✅ {row['product_name']} deleted successfully."
                                if ok else "❌ Failed to delete product. Please try again."
                            )
                            st.rerun()
                        if c_no.button("❌ Cancel", key=f"no_del_{row['product_id']}"):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()

            # Show product delete feedback
            if "prod_del_msg" in st.session_state:
                msg = st.session_state.pop("prod_del_msg")
                if msg.startswith("✅"):
                    st.success(msg)
                else:
                    st.error(msg)

            # Pagination controls
            if total_pages > 1:
                st.markdown("---")
                pc1, pc2, pc3 = st.columns([1, 3, 1])
                if pc1.button("◀ Prev", disabled=(pg <= 1), key="prod_prev"):
                    st.session_state.prod_page = max(1, pg - 1)
                    st.rerun()
                pc2.markdown(f"<div style='text-align:center;padding-top:0.5rem;color:#8BA0B8;'>Page {pg} of {total_pages}</div>", unsafe_allow_html=True)
                if pc3.button("Next ▶", disabled=(pg >= total_pages), key="prod_next"):
                    st.session_state.prod_page = min(total_pages, pg + 1)
                    st.rerun()

    # ── Tab 2: Add Product ──
    with tab2:
        with st.form("add_product_form", clear_on_submit=True):
            st.markdown("#### New Product Details")
            f1, f2 = st.columns(2)
            prod_name   = f1.text_input("Product Name *",     placeholder="e.g. Indomie Chicken 70g")
            category    = f2.text_input("Category *",         placeholder="e.g. Noodles, Beverages")
            cost_price  = f1.number_input("Cost Price (₦) *",    min_value=0.0, step=50.0,
                                          help="What you paid per unit")
            sell_price  = f2.number_input("Selling Price (₦) *", min_value=0.0, step=50.0,
                                          help="What the customer pays")
            stock_qty   = f1.number_input("Opening Stock *",  min_value=0, step=1,
                                          help="How many units you have right now")
            reorder_lvl = f2.number_input("Reorder Level *",  min_value=0, step=1,
                                          help="Alert me when stock falls to this level")

            if cost_price > 0 and sell_price > 0:
                margin  = sell_price - cost_price
                margin_pct = (margin / sell_price) * 100
                st.info(f"💡 Profit margin: **{fmt_naira(margin)}** per unit ({margin_pct:.1f}%)")

            submitted = st.form_submit_button("➕ Add Product", use_container_width=True, type="primary")

        if submitted:
            if not all([prod_name, category]) or sell_price <= 0:
                st.error("Please fill in all required fields and ensure selling price > 0.")
            else:
                product_id = gen_id("PRD")
                ok = db_insert(TBL_PRODUCTS, {
                    "product_id":     product_id,
                    "business_id":    business_id,
                    "product_name":   prod_name.strip(),
                    "category":       category.strip(),
                    "cost_price":     cost_price,
                    "selling_price":  sell_price,
                    "stock_quantity": stock_qty,
                    "reorder_level":  reorder_lvl,
                    "created_at":     datetime.now().isoformat(),
                })
                if ok:
                    st.success(f"✅ '{prod_name}' added to your inventory!")
                    st.rerun()
                else:
                    st.error("Failed to add product. Please try again.")

    # ── Tab 3: Restock ──
    with tab3:
        products_df = get_products_df(business_id)
        if products_df.empty:
            st.info("No products found. Add products first.")
        else:
            st.markdown("#### Add Stock to Existing Product")
            with st.form("restock_form", clear_on_submit=True):
                product_options = {
                    f"{r['product_name']} (Current: {int(r['stock_quantity'])} units)": r
                    for _, r in products_df.iterrows()
                }
                selected_label   = st.selectbox("Select product", list(product_options.keys()))
                selected_product = product_options[selected_label]

                add_qty = st.number_input("Units to add", min_value=1, step=1, value=10)
                restock_note = st.text_input("Note (optional)", placeholder="e.g. Weekly supplier delivery")
                submitted = st.form_submit_button("🔄 Update Stock", use_container_width=True, type="primary")

            if submitted:
                new_qty = int(selected_product["stock_quantity"]) + add_qty
                ok = db_update(TBL_PRODUCTS, "product_id", selected_product["product_id"], {"stock_quantity": new_qty})
                if ok:
                    # Log the restock event for audit trail
                    db_insert(TBL_RESTOCK, {
                        "restock_id":   gen_id("RST"),
                        "business_id":  business_id,
                        "product_id":   selected_product["product_id"],
                        "product_name": selected_product["product_name"],
                        "qty_added":    add_qty,
                        "qty_before":   int(selected_product["stock_quantity"]),
                        "qty_after":    new_qty,
                        "note":         restock_note.strip() if restock_note else "",
                        "recorded_by":  user.get("full_name", user.get("email", "")),
                        "restock_date": datetime.now().isoformat(),
                    })
                    st.success(
                        f"✅ Stock updated! {selected_product['product_name']}: "
                        f"{int(selected_product['stock_quantity'])} → {new_qty} units"
                    )
                    st.rerun()
                else:
                    st.error("Failed to update stock.")

    # ── Tab 4: Restock History ──
    with tab4:
        section_header("📜 Restock History")
        restock_df = db_fetch(TBL_RESTOCK, {"business_id": business_id})
        if restock_df.empty:
            st.info("No restock history yet. Every restock will be logged here automatically.")
        else:
            restock_df["restock_date"] = pd.to_datetime(restock_df["restock_date"], errors="coerce", utc=True).dt.tz_localize(None)
            restock_df = restock_df.sort_values("restock_date", ascending=False)

            # Search
            search_rst = st.text_input("🔍 Search by product name", key="restock_search", placeholder="Type to filter…")
            if search_rst:
                restock_df = restock_df[restock_df["product_name"].str.contains(search_rst, case=False, na=False)]

            display_cols = [c for c in ["restock_date","product_name","qty_before","qty_added","qty_after","note","recorded_by"] if c in restock_df.columns]
            st.dataframe(
                restock_df[display_cols].rename(columns={
                    "restock_date":  "Date",
                    "product_name":  "Product",
                    "qty_before":    "Stock Before",
                    "qty_added":     "Units Added",
                    "qty_after":     "Stock After",
                    "note":          "Note",
                    "recorded_by":   "Recorded By",
                }),
                use_container_width=True,
            )


# ─────────────────────────────────────────────
#  PAGE: EXPENSES
# ─────────────────────────────────────────────

def page_expenses():
    user        = st.session_state.user
    business_id = user["business_id"]

    page_header("💸 Expense Tracker", "Log and monitor your business expenses")

    tab1, tab2 = st.tabs(["📋 View Expenses", "➕ Log Expense"])

    with tab1:
        expenses_df = get_expenses_df(business_id)
        if expenses_df.empty:
            st.info("No expenses logged yet.")
        else:
            # Date filter
            col1, col2 = st.columns(2)
            start_date = col1.date_input("From", value=(datetime.now() - timedelta(days=30)).date())
            end_date   = col2.date_input("To",   value=datetime.now().date())

            filtered = expenses_df[
                (expenses_df["expense_date"].dt.date >= start_date) &
                (expenses_df["expense_date"].dt.date <= end_date)
            ]

            c1, c2, c3 = st.columns(3)
            with c1:
                kpi_card("Total Expenses", fmt_naira(filtered["amount"].sum()),
                         f"In selected period")
            with c2:
                kpi_card("Transactions", str(len(filtered)), "Expense entries")
            with c3:
                avg = filtered["amount"].mean() if not filtered.empty else 0
                kpi_card("Average Expense", fmt_naira(avg), "Per entry")

            if not filtered.empty:
                # Category breakdown chart
                cat_breakdown = (
                    filtered.groupby("category")["amount"]
                    .sum().reset_index()
                    .sort_values("amount", ascending=False)
                )
                if not cat_breakdown.empty:
                    fig = px.bar(
                        cat_breakdown, x="category", y="amount",
                        labels={"amount": "Amount (₦)", "category": "Category"},
                        color_discrete_sequence=["#ef4444"],
                        title="Expenses by Category"
                    )
                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=40, b=0),
                        height=280,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Search
                exp_search = st.text_input("🔍 Search expenses", key="exp_search", placeholder="Filter by description…")
                if exp_search:
                    filtered = filtered[filtered["expense_name"].str.contains(exp_search, case=False, na=False)]

                # Pagination
                EXP_PAGE_SIZE = 20
                exp_total_pages = max(1, -(-len(filtered) // EXP_PAGE_SIZE))
                if "exp_page" not in st.session_state:
                    st.session_state.exp_page = 1
                exp_pg = st.session_state.exp_page
                filtered_sorted = filtered.sort_values("expense_date", ascending=False)
                exp_page_df = filtered_sorted.iloc[(exp_pg - 1) * EXP_PAGE_SIZE: exp_pg * EXP_PAGE_SIZE]

                st.caption(f"Showing {len(exp_page_df)} of {len(filtered)} entries  •  Page {exp_pg} of {exp_total_pages}")
                st.markdown("---")

                # Editable rows
                for _, r in exp_page_df.iterrows():
                    exp_id = r["expense_id"]
                    edit_key = f"exp_edit_{exp_id}"
                    with st.expander(
                        f"**{r['expense_name']}** | {r['category']} | "
                        f"{fmt_naira(r['amount'])} | {r['expense_date'].strftime('%d %b %Y') if pd.notna(r['expense_date']) else ''}",
                        expanded=False
                    ):
                        with st.form(f"edit_exp_{exp_id}"):
                            ef1, ef2 = st.columns(2)
                            new_exp_name = ef1.text_input("Description", value=r["expense_name"])
                            new_exp_cat  = ef2.selectbox("Category", [
                                "Rent","Utilities","Salaries","Supplies","Transport",
                                "Marketing","Maintenance","Taxes","Miscellaneous"
                            ], index=["Rent","Utilities","Salaries","Supplies","Transport",
                                      "Marketing","Maintenance","Taxes","Miscellaneous"].index(r["category"])
                                if r["category"] in ["Rent","Utilities","Salaries","Supplies","Transport",
                                                     "Marketing","Maintenance","Taxes","Miscellaneous"] else 0)
                            new_exp_amt  = ef1.number_input("Amount (₦)", value=safe_float(r["amount"]), min_value=0.0, step=100.0)
                            new_exp_date = ef2.date_input("Date", value=r["expense_date"].date() if pd.notna(r["expense_date"]) else datetime.now().date())
                            save_exp = st.form_submit_button("💾 Save Changes", type="primary")

                        if save_exp:
                            ok = db_update(TBL_EXPENSES, "expense_id", exp_id, {
                                "expense_name": new_exp_name.strip(),
                                "category":     new_exp_cat,
                                "amount":       new_exp_amt,
                                "expense_date": str(new_exp_date),
                            })
                            st.cache_data.clear()
                            st.session_state[f"exp_msg_{exp_id}"] = (
                                "✅ Expense updated successfully."
                                if ok else "❌ Failed to update expense. Please try again."
                            )
                            st.rerun()

                        # Show feedback message
                        exp_msg_key = f"exp_msg_{exp_id}"
                        if exp_msg_key in st.session_state:
                            msg = st.session_state.pop(exp_msg_key)
                            if msg.startswith("✅"):
                                st.success(msg)
                            else:
                                st.error(msg)

                        # Delete with confirmation
                        confirm_exp_key = f"confirm_del_exp_{exp_id}"
                        if not st.session_state.get(confirm_exp_key, False):
                            if st.button("🗑️ Delete this expense", key=f"del_exp_{exp_id}"):
                                st.session_state[confirm_exp_key] = True
                                st.rerun()
                        else:
                            st.warning("⚠️ Delete this expense entry permanently?")
                            ce1, ce2 = st.columns(2)
                            if ce1.button("✅ Yes, delete", key=f"yes_del_exp_{exp_id}", type="primary"):
                                ok = db_delete(TBL_EXPENSES, "expense_id", exp_id)
                                st.cache_data.clear()
                                st.session_state.pop(confirm_exp_key, None)
                                st.session_state["exp_del_msg"] = (
                                    "✅ Expense deleted." if ok else "❌ Failed to delete expense."
                                )
                                st.rerun()
                            if ce2.button("❌ Cancel", key=f"no_del_exp_{exp_id}"):
                                st.session_state.pop(confirm_exp_key, None)
                                st.rerun()

                        if "exp_del_msg" in st.session_state:
                            msg = st.session_state.pop("exp_del_msg")
                            if msg.startswith("✅"):
                                st.success(msg)
                            else:
                                st.error(msg)

                # Pagination controls
                if exp_total_pages > 1:
                    st.markdown("---")
                    ep1, ep2, ep3 = st.columns([1, 3, 1])
                    if ep1.button("◀ Prev", disabled=(exp_pg <= 1), key="exp_prev"):
                        st.session_state.exp_page = max(1, exp_pg - 1)
                        st.rerun()
                    ep2.markdown(f"<div style='text-align:center;padding-top:0.5rem;color:#8BA0B8;'>Page {exp_pg} of {exp_total_pages}</div>", unsafe_allow_html=True)
                    if ep3.button("Next ▶", disabled=(exp_pg >= exp_total_pages), key="exp_next"):
                        st.session_state.exp_page = min(exp_total_pages, exp_pg + 1)
                        st.rerun()

    with tab2:
        with st.form("log_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            exp_name = col1.text_input("Description *", placeholder="e.g. Generator fuel")
            category = col2.selectbox("Category", [
                "Rent", "Utilities", "Salaries", "Supplies", "Transport",
                "Marketing", "Maintenance", "Taxes", "Miscellaneous"
            ])
            amount      = col1.number_input("Amount (₦) *", min_value=0.0, step=100.0)
            expense_date = col2.date_input("Date", value=datetime.now().date())
            submitted = st.form_submit_button("Log Expense", use_container_width=True, type="primary")

        if submitted:
            if not exp_name or amount <= 0:
                st.error("Please fill in description and a valid amount.")
            else:
                expense_id = gen_id("EXP")
                ok = db_insert(TBL_EXPENSES, {
                    "expense_id":   expense_id,
                    "business_id":  business_id,
                    "expense_name": exp_name.strip(),
                    "category":     category,
                    "amount":       amount,
                    "expense_date": str(expense_date),
                    "recorded_by":  user.get("full_name", user.get("email", "")),
                })
                if ok:
                    st.success(f"✅ Expense logged: {exp_name} — {fmt_naira(amount)}")
                    st.rerun()
                else:
                    st.error("Failed to log expense.")


# ─────────────────────────────────────────────
#  PAGE: BUSINESS INSIGHTS
# ─────────────────────────────────────────────

def page_insights():
    user        = st.session_state.user
    business_id = user["business_id"]

    page_header("🧠 Business Insights", "Data-driven intelligence for smarter decisions")

    with st.spinner("Crunching your numbers…"):
        sales_df    = get_sales_df(business_id)
        products_df = get_products_df(business_id)
        expenses_df = get_expenses_df(business_id)
        insights    = compute_insights(sales_df, products_df, expenses_df)

    if sales_df.empty:
        st.info("📭 No data yet. Record some sales to unlock insights.")
        return

    # ── Summary Stats ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Avg Daily Revenue",
                 fmt_naira(insights["avg_daily_revenue"]), "Based on all recorded days")
    with c2:
        kpi_card("Best Sales Day", insights.get("best_day", "N/A"), "Highest revenue weekday")
    with c3:
        kpi_card("Slowest Day", insights.get("worst_day", "N/A"), "Lowest revenue weekday")
    with c4:
        if not insights["top_products_revenue"].empty:
            best = insights["top_products_revenue"].iloc[0]["product_name"]
        else:
            best = "N/A"
        kpi_card("Best Seller", best, "By total revenue")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends", "🏆 Products", "📦 Inventory", "📅 Weekday", "📊 Export"
    ])

    # ── Tab 1: Trends ──
    with tab1:
        section_header("Daily Revenue Trend")
        if not insights["daily_trend"].empty:
            fig = px.line(
                insights["daily_trend"], x="date", y="total_amount",
                labels={"total_amount": "Revenue (₦)", "date": ""},
                color_discrete_sequence=["#6366f1"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(tickprefix="₦", gridcolor="#f1f5f9"),
                height=320,
            )
            fig.update_traces(line_width=2.5, mode="lines+markers")
            st.plotly_chart(fig, use_container_width=True)

        section_header("Category Performance")
        if not insights["category_revenue"].empty:
            fig2 = px.bar(
                insights["category_revenue"], x="category", y="total_amount",
                labels={"total_amount": "Revenue (₦)", "category": ""},
                color_discrete_sequence=["#10b981"],
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0), height=280,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 2: Products ──
    with tab2:
        col_l, col_r = st.columns(2)
        with col_l:
            section_header("Top Products by Revenue")
            if not insights["top_products_revenue"].empty:
                fig = px.bar(
                    insights["top_products_revenue"].sort_values("total_amount"),
                    x="total_amount", y="product_name", orientation="h",
                    labels={"total_amount": "Revenue (₦)", "product_name": ""},
                    color_discrete_sequence=["#6366f1"],
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=0), height=350,
                    xaxis=dict(tickprefix="₦"),
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_r:
            section_header("Top Products by Quantity Sold")
            if not insights["top_products_qty"].empty:
                fig2 = px.bar(
                    insights["top_products_qty"].sort_values("quantity"),
                    x="quantity", y="product_name", orientation="h",
                    labels={"quantity": "Units Sold", "product_name": ""},
                    color_discrete_sequence=["#10b981"],
                )
                fig2.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=0), height=350,
                )
                st.plotly_chart(fig2, use_container_width=True)

        section_header("⚠️ Slow-Moving Products (Last 30 Days)")
        if not insights["slow_movers"].empty:
            st.dataframe(
                insights["slow_movers"].rename(
                    columns={"product_name":"Product","quantity":"Units Sold (30d)"}
                ),
                use_container_width=True,
            )
        else:
            st.markdown('<div class="alert-success">✅ All products are selling at healthy rates.</div>',
                        unsafe_allow_html=True)

    # ── Tab 3: Inventory ──
    with tab3:
        section_header("🔴 Low Stock Products")
        if not insights["low_stock"].empty:
            for _, r in insights["low_stock"].iterrows():
                qty = safe_int(r["stock_quantity"])
                css = "alert-critical" if qty <= 0 else "alert-low"
                st.markdown(
                    f'<div class="{css}">⚠️ <strong>{r["product_name"]}</strong> '
                    f'— {qty} units left (reorder at {safe_int(r["reorder_level"])})</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<div class="alert-success">✅ All products have sufficient stock.</div>',
                        unsafe_allow_html=True)

        section_header("📅 Projected Stockout Dates")
        if not insights["stockout_projection"].empty:
            proj = insights["stockout_projection"].copy()
            proj["stockout_date"] = proj["days_until_stockout"].apply(
                lambda d: (datetime.now() + timedelta(days=d)).strftime("%d %b %Y")
            )
            proj["urgency"] = proj["days_until_stockout"].apply(
                lambda d: "🔴 Critical" if d <= 3 else ("🟡 Soon" if d <= 7 else "🟢 OK")
            )
            st.dataframe(
                proj[["product_name","stock_quantity","avg_daily_sales",
                       "days_until_stockout","stockout_date","urgency"]]
                .rename(columns={
                    "product_name":       "Product",
                    "stock_quantity":     "Current Stock",
                    "avg_daily_sales":    "Avg Daily Sales",
                    "days_until_stockout":"Days Left",
                    "stockout_date":      "Est. Stockout Date",
                    "urgency":            "Status",
                }),
                use_container_width=True,
            )
        else:
            st.info("Not enough sales history to project stockout dates.")

    # ── Tab 4: Weekday ──
    with tab4:
        section_header("Revenue by Day of Week")
        if not insights["weekday_performance"].empty:
            wd = insights["weekday_performance"]
            colors = ["#ef4444" if r == wd["revenue"].min()
                      else ("#10b981" if r == wd["revenue"].max() else "#6366f1")
                      for r in wd["revenue"]]
            fig = go.Figure(go.Bar(
                x=wd["weekday"], y=wd["revenue"],
                marker_color=colors,
                text=[fmt_naira(v) for v in wd["revenue"]],
                textposition="outside",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(tickprefix="₦", gridcolor="#f1f5f9"),
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

            if insights["best_day"] and insights["worst_day"]:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f'<div class="alert-success">🏆 <strong>Best day:</strong> '
                        f'{insights["best_day"]} — schedule more staff and stock up.</div>',
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f'<div class="alert-low">💡 <strong>Slowest day:</strong> '
                        f'{insights["worst_day"]} — consider promotions or discounts.</div>',
                        unsafe_allow_html=True
                    )

    # ── Tab 5: Export ──
    with tab5:
        section_header("📥 Download Your Data")
        col1, col2, col3 = st.columns(3)

        with col1:
            if not sales_df.empty:
                csv = sales_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Sales CSV",
                    data=csv, file_name="sales_export.csv",
                    mime="text/csv", use_container_width=True,
                )

        with col2:
            if not products_df.empty:
                csv = products_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Products CSV",
                    data=csv, file_name="products_export.csv",
                    mime="text/csv", use_container_width=True,
                )

        with col3:
            if not expenses_df.empty:
                csv = expenses_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Expenses CSV",
                    data=csv, file_name="expenses_export.csv",
                    mime="text/csv", use_container_width=True,
                )


# ─────────────────────────────────────────────
#  PAGE: ADMIN PANEL
# ─────────────────────────────────────────────

def page_admin():
    page_header("🛡️ Admin Panel", "BizPulse platform management")

    users_df = db_fetch(TBL_USERS)

    if users_df.empty:
        st.info("No users found.")
        return

    # Platform stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Businesses", str(len(users_df)), "Registered accounts")
    with c2:
        active = len(users_df[users_df["plan_status"] == "active"])
        kpi_card("Active Subscriptions", str(active), "Paying or trial users")
    with c3:
        pending = len(users_df[users_df["plan_status"] == "pending_payment"])
        kpi_card("Pending Payment", str(pending), "Awaiting manual activation")
    with c4:
        monthly_rev = len(users_df[
            (users_df["plan_type"] == "monthly") &
            (users_df["plan_status"] == "active")
        ]) * PAYMENT_DETAILS["monthly_price"]
        yearly_rev = len(users_df[
            (users_df["plan_type"] == "yearly") &
            (users_df["plan_status"] == "active")
        ]) * (PAYMENT_DETAILS["yearly_price"] / 12)  # normalise yearly to monthly
        kpi_card("Est. MRR",
                 fmt_naira(monthly_rev + yearly_rev), "From active paid plans")

    # ── Real revenue KPIs from PAYMENTS ledger ──
    payments_df = get_payments_df()
    if not payments_df.empty:
        now_dt      = datetime.now()
        month_start = datetime(now_dt.year, now_dt.month, 1)
        year_start  = datetime(now_dt.year, 1, 1)

        total_collected      = payments_df["amount"].sum()
        month_collected      = payments_df[
            payments_df["payment_date"] >= month_start
        ]["amount"].sum()
        year_collected       = payments_df[
            payments_df["payment_date"] >= year_start
        ]["amount"].sum()
        total_transactions   = len(payments_df)

        st.markdown("---")
        st.markdown("#### 💰 Platform Revenue — Actual Collected")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            kpi_card("All-Time Revenue", fmt_naira(total_collected),
                     f"{total_transactions} payments received")
        with r2:
            kpi_card("This Month", fmt_naira(month_collected),
                     now_dt.strftime("%B %Y"))
        with r3:
            kpi_card("This Year", fmt_naira(year_collected),
                     str(now_dt.year))
        with r4:
            avg_per_payment = total_collected / total_transactions if total_transactions else 0
            kpi_card("Avg. per Payment", fmt_naira(avg_per_payment),
                     "Across all activations & renewals")
    else:
        st.info("💡 No payment records yet. Revenue will appear here as you activate users.")

    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "⏳ Pending Activation",
        "✅ Active Users",
        "📈 MRR & Growth",
        "🚨 Churn Alerts",
        "🔑 Password Resets",
        "👥 All Users",
        "⛔ Deactivated",
    ])

    # ── Pending ──
    with tab1:
        pending_df = users_df[users_df["plan_status"] == "pending_payment"]
        if pending_df.empty:
            st.success("No pending activations.")
        else:
            for _, u in pending_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                        st.caption(f"📧 {u['email']} | Plan: {u['plan_type']} | Signed up: {u['created_at']}")
                    with col2:
                        plan   = u["plan_type"]
                        days   = 30 if plan == "monthly" else 365
                        end_dt = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                        if st.button(f"✅ Activate", key=f"act_{u['user_id']}"):
                            ok = db_update(TBL_USERS, "user_id", u["user_id"], {
                                    "plan_status":       "active",
                                    "subscription_start": datetime.now().strftime("%Y-%m-%d"),
                                    "subscription_end":   end_dt,
                                })
                            if ok:
                                pay_amount = (PAYMENT_DETAILS["yearly_price"]
                                              if plan == "yearly"
                                              else PAYMENT_DETAILS["monthly_price"])
                                log_payment(
                                    u["user_id"], u["business_name"], u["email"],
                                    plan, pay_amount, "Initial activation"
                                )
                                st.cache_data.clear()
                                st.success(f"✅ {u['business_name']} activated until {end_dt}")
                                st.rerun()
                    with col3:
                        confirm_del_key = f"confirm_del_user_{u['user_id']}"
                        if not st.session_state.get(confirm_del_key, False):
                            if st.button("🗑️ Delete", key=f"del_u_{u['user_id']}"):
                                st.session_state[confirm_del_key] = True
                                st.rerun()
                        else:
                            st.warning("Delete this user?")
                            if st.button("✅ Confirm", key=f"confirm_yes_u_{u['user_id']}", type="primary"):
                                db_delete(TBL_USERS, "user_id", u["user_id"])
                                st.session_state.pop(confirm_del_key, None)
                                st.rerun()
                            if st.button("❌ Cancel", key=f"confirm_no_u_{u['user_id']}"):
                                st.session_state.pop(confirm_del_key, None)
                                st.rerun()
                    st.markdown("---")

    # ── Active ──
    with tab2:
        active_df = users_df[users_df["plan_status"] == "active"]
        if active_df.empty:
            st.info("No active users.")
        else:
            for _, u in active_df.iterrows():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                    st.caption(f"📧 {u['email']} | {u['plan_type']} | Expires: {u.get('subscription_end','?')}")
                with col2:
                    ext_days  = 365 if u.get("plan_type") == "yearly" else 30
                    ext_label = "1 year" if ext_days == 365 else "30 days"
                    if st.button(f"🔁 Renew ({ext_label})", key=f"ext_{u['user_id']}"):
                        curr_end = parse_date(u.get("subscription_end", ""))
                        base     = curr_end if (curr_end and curr_end > datetime.now()) else datetime.now()
                        new_end  = (base + timedelta(days=ext_days)).strftime("%Y-%m-%d")
                        db_update(TBL_USERS, "user_id", u["user_id"], {"subscription_end": new_end})
                        pay_amount = (PAYMENT_DETAILS["yearly_price"]
                                      if ext_days == 365
                                      else PAYMENT_DETAILS["monthly_price"])
                        log_payment(
                            u["user_id"], u["business_name"], u["email"],
                            u.get("plan_type", "monthly"), pay_amount, "Renewal"
                        )
                        st.cache_data.clear()
                        st.success(f"✅ Renewed to {new_end}")
                        st.rerun()
                with col3:
                    if st.button("⛔ Deactivate", key=f"deact_{u['user_id']}"):
                        db_update(TBL_USERS, "user_id", u["user_id"], {"plan_status": "expired"})
                        st.rerun()
                st.markdown("---")

    # ── MRR & Growth ──
    with tab3:
        st.markdown("### 📈 Monthly Recurring Revenue")

        # ── Real collected revenue section (from PAYMENTS ledger) ──
        payments_df = get_payments_df()
        if not payments_df.empty:
            st.markdown("#### 💰 Actual Collected Revenue by Month")
            pay_chart = payments_df.copy()
            pay_chart["month"] = pay_chart["payment_date"].dt.to_period("M")
            monthly_collected = (
                pay_chart.groupby("month")
                .agg(collected=("amount", "sum"), count=("amount", "count"))
                .reset_index()
            )
            monthly_collected["month_str"] = monthly_collected["month"].dt.strftime("%b %Y")

            fig_collected = go.Figure()
            fig_collected.add_trace(go.Bar(
                x=monthly_collected["month_str"],
                y=monthly_collected["collected"],
                name="Collected",
                marker_color="#10b981",
                text=[fmt_naira(v) for v in monthly_collected["collected"]],
                textposition="outside",
            ))
            fig_collected.update_layout(
                title="Cash Collected per Month",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(tickprefix="₦", gridcolor="#f1f5f9"),
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
                showlegend=False,
            )
            st.plotly_chart(fig_collected, use_container_width=True)

            # Plan type breakdown
            plan_totals = (
                pay_chart.groupby("plan_type")["amount"]
                .sum().reset_index()
                .rename(columns={"amount": "total"})
            )
            col_l, col_r = st.columns(2)
            with col_l:
                fig_pie = px.pie(
                    plan_totals, values="total", names="plan_type",
                    title="Revenue by Plan Type",
                    color_discrete_sequence=["#6366f1", "#10b981", "#f59e0b"],
                    hole=0.45,
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=40, b=0),
                    height=280,
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_r:
                st.markdown("**Payment breakdown**")
                for _, row in plan_totals.iterrows():
                    pct = row["total"] / payments_df["amount"].sum() * 100
                    st.markdown(
                        f"**{row['plan_type'].capitalize()}** — "
                        f"{fmt_naira(row['total'])} ({pct:.1f}%)"
                    )
                st.markdown("---")
                st.markdown(f"**Total payments received:** {len(payments_df)}")
                st.markdown(
                    f"**Latest payment:** "
                    f"{payments_df['payment_date'].max().strftime('%d %b %Y')}"
                )

            st.markdown("---")
            with st.expander("📋 Full payment ledger"):
                show = payments_df[[c for c in
                    ["payment_id","business_name","email","plan_type",
                     "amount","payment_date","note"]
                    if c in payments_df.columns
                ]].sort_values("payment_date", ascending=False)
                st.dataframe(show, use_container_width=True)
                csv = show.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Export Payment Ledger CSV", data=csv,
                    file_name="bizpulse_payments.csv", mime="text/csv",
                )
            st.markdown("---")
        else:
            st.info("💡 No payment records yet. They'll appear here as you activate users.")
            st.markdown("---")

        st.markdown("#### 📊 Estimated MRR (Active Users)")

        # Build a month-by-month activation history from created_at + plan_type
        import calendar

        paid_df = users_df[
            (users_df["plan_status"].isin(["active", "expired"])) &
            (users_df["plan_type"].isin(["monthly", "yearly"]))
        ].copy()

        if paid_df.empty:
            st.info("No paid user data yet. MRR chart will appear once users activate.")
        else:
            # Parse activation dates
            paid_df["activation_date"] = pd.to_datetime(
                paid_df["subscription_start"], errors="coerce", utc=True
            ).dt.tz_localize(None)
            paid_df = paid_df.dropna(subset=["activation_date"])

            if paid_df.empty:
                st.info("No activation dates found. Activate users to start tracking MRR.")
            else:
                # Build monthly cohort: for each calendar month, count active paid users
                # and their contribution to MRR
                min_month = paid_df["activation_date"].dt.to_period("M").min()
                max_month = pd.Timestamp.now().to_period("M")
                periods   = pd.period_range(min_month, max_month, freq="M")

                mrr_rows = []
                for period in periods:
                    period_end = pd.Timestamp(period.to_timestamp("M"))
                    # User is "active" in this month if activated on or before month end
                    # and subscription_end is after month start
                    month_start = pd.Timestamp(period.to_timestamp())
                    active_mask = paid_df["activation_date"] <= period_end
                    # Check subscription_end if available
                    if "subscription_end" in paid_df.columns:
                        sub_end = pd.to_datetime(paid_df["subscription_end"], errors="coerce", utc=True).dt.tz_localize(None)
                        active_mask = active_mask & (
                            sub_end.isna() | (sub_end >= month_start)
                        )
                    cohort   = paid_df[active_mask]
                    monthly_c = len(cohort[cohort["plan_type"] == "monthly"])
                    yearly_c  = len(cohort[cohort["plan_type"] == "yearly"])
                    mrr       = (monthly_c * PAYMENT_DETAILS["monthly_price"] +
                                 yearly_c  * (PAYMENT_DETAILS["yearly_price"] / 12))
                    mrr_rows.append({
                        "month":   period.strftime("%b %Y"),
                        "mrr":     mrr,
                        "monthly": monthly_c,
                        "yearly":  yearly_c,
                        "total":   monthly_c + yearly_c,
                    })

                mrr_df = pd.DataFrame(mrr_rows)

                # ── KPIs ──
                current_mrr  = mrr_df["mrr"].iloc[-1]  if not mrr_df.empty else 0
                previous_mrr = mrr_df["mrr"].iloc[-2]  if len(mrr_df) > 1  else 0
                arr          = current_mrr * 12
                mrr_growth   = ((current_mrr - previous_mrr) / previous_mrr * 100
                                if previous_mrr > 0 else 0)

                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    kpi_card("Current MRR", fmt_naira(current_mrr),
                             "This month's recurring revenue")
                with k2:
                    kpi_card("ARR (projected)", fmt_naira(arr),
                             "MRR × 12")
                with k3:
                    direction = "▲" if mrr_growth >= 0 else "▼"
                    kpi_card("MRR Growth", f"{direction} {abs(mrr_growth):.1f}%",
                             "vs last month", positive=(mrr_growth >= 0))
                with k4:
                    kpi_card("Paid Users", str(int(mrr_df["total"].iloc[-1])),
                             f"{int(mrr_df['monthly'].iloc[-1])} monthly · "
                             f"{int(mrr_df['yearly'].iloc[-1])} yearly")

                st.markdown("---")

                # ── MRR Bar Chart ──
                fig_mrr = go.Figure()
                fig_mrr.add_trace(go.Bar(
                    x=mrr_df["month"], y=mrr_df["mrr"],
                    name="MRR",
                    marker_color="#6366f1",
                    text=[fmt_naira(v) for v in mrr_df["mrr"]],
                    textposition="outside",
                ))
                fig_mrr.update_layout(
                    title="Monthly Recurring Revenue",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(tickprefix="₦", gridcolor="#f1f5f9"),
                    margin=dict(l=0, r=0, t=40, b=0),
                    height=350,
                    showlegend=False,
                )
                st.plotly_chart(fig_mrr, use_container_width=True)

                # ── User count stacked bar ──
                fig_users = go.Figure()
                fig_users.add_trace(go.Bar(
                    x=mrr_df["month"], y=mrr_df["monthly"],
                    name="Monthly plan", marker_color="#6366f1",
                ))
                fig_users.add_trace(go.Bar(
                    x=mrr_df["month"], y=mrr_df["yearly"],
                    name="Yearly plan", marker_color="#10b981",
                ))
                fig_users.update_layout(
                    title="Active Paid Users by Plan",
                    barmode="stack",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(gridcolor="#f1f5f9"),
                    margin=dict(l=0, r=0, t=40, b=0),
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                st.plotly_chart(fig_users, use_container_width=True)

    # ── Churn Alerts ──
    with tab4:
        st.markdown("### 🚨 Churn Alerts")
        st.caption(
            "Users whose subscription expires within 7 days. "
            "Reach out before they lapse."
        )

        if "subscription_end" not in users_df.columns:
            st.info("No subscription data available.")
        else:
            now      = datetime.now()
            soon     = now + timedelta(days=7)
            active_u = users_df[users_df["plan_status"] == "active"].copy()

            if active_u.empty:
                st.info("No active users yet.")
            else:
                active_u["sub_end_dt"] = pd.to_datetime(
                    active_u["subscription_end"], errors="coerce", utc=True
                ).dt.tz_localize(None)
                expiring = active_u[
                    (active_u["sub_end_dt"] >= pd.Timestamp(now)) &
                    (active_u["sub_end_dt"] <= pd.Timestamp(soon))
                ].sort_values("sub_end_dt")

                already_expired = users_df[
                    users_df["plan_status"] == "expired"
                ].copy()

                # ── Summary KPIs ──
                k1, k2, k3 = st.columns(3)
                with k1:
                    kpi_card("Expiring in 7 days", str(len(expiring)),
                             "Need immediate attention", positive=(len(expiring) == 0))
                with k2:
                    kpi_card("Already Expired", str(len(already_expired)),
                             "Lapsed — potential win-back")
                with k3:
                    trial_u = users_df[
                        (users_df["plan_type"] == "trial") &
                        (users_df["plan_status"] == "active")
                    ]
                    kpi_card("Active Trials", str(len(trial_u)),
                             "Potential conversions")

                st.markdown("---")

                # ── Expiring soon list ──
                st.markdown("#### ⏰ Expiring within 7 days")
                if expiring.empty:
                    st.success("✅ No subscriptions expiring in the next 7 days.")
                else:
                    for _, u in expiring.iterrows():
                        days_left = (u["sub_end_dt"] - pd.Timestamp(now)).days
                        color     = "#ef4444" if days_left <= 2 else "#f59e0b"
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([3, 2, 2])
                            with col1:
                                st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                                st.caption(f"📧 {u['email']} | {u['plan_type'].capitalize()} plan")
                            with col2:
                                st.markdown(
                                    f"<span style='color:{color};font-weight:700;'>"
                                    f"⏳ {days_left} day{'s' if days_left != 1 else ''} left</span>"
                                    f"<br><small style='color:#64748b;'>"
                                    f"Expires {u['sub_end_dt'].strftime('%d %b %Y')}</small>",
                                    unsafe_allow_html=True,
                                )
                            with col3:
                                ext_days  = 365 if u.get("plan_type") == "yearly" else 30
                                ext_label = "1 year" if ext_days == 365 else "30 days"
                                if st.button(f"🔁 Renew ({ext_label})",
                                             key=f"churn_ext_{u['user_id']}"):
                                    base    = u["sub_end_dt"] if u["sub_end_dt"] > pd.Timestamp(now) else pd.Timestamp(now)
                                    new_end = (base + timedelta(days=ext_days)).strftime("%Y-%m-%d")
                                    db_update(TBL_USERS, "user_id", u["user_id"], {"subscription_end": new_end})
                                    pay_amount = (PAYMENT_DETAILS["yearly_price"]
                                                  if ext_days == 365
                                                  else PAYMENT_DETAILS["monthly_price"])
                                    log_payment(
                                        u["user_id"], u["business_name"], u["email"],
                                        u.get("plan_type", "monthly"), pay_amount,
                                        "Renewal — churn prevention"
                                    )
                                    st.cache_data.clear()
                                    st.success(f"✅ Renewed to {new_end}")
                                    st.rerun()

                # ── Trial users expiring ──
                st.markdown("---")
                st.markdown("#### 🎁 Trials expiring within 7 days")
                trial_expiring = active_u[
                    (active_u["plan_type"] == "trial") &
                    (active_u["sub_end_dt"] >= pd.Timestamp(now)) &
                    (active_u["sub_end_dt"] <= pd.Timestamp(soon))
                ].sort_values("sub_end_dt")

                if trial_expiring.empty:
                    st.success("✅ No trials expiring soon.")
                else:
                    st.info(f"{len(trial_expiring)} trial(s) ending soon — "
                            "good time to reach out and convert them.")
                    for _, u in trial_expiring.iterrows():
                        days_left = (u["sub_end_dt"] - pd.Timestamp(now)).days
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 2])
                            with col1:
                                st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                                st.caption(
                                    f"📧 {u['email']} | "
                                    f"Trial ends in {days_left} day{'s' if days_left != 1 else ''} "
                                    f"({u['sub_end_dt'].strftime('%d %b %Y')})"
                                )
                            with col2:
                                st.caption("Send them your Flutterwave link to convert.")

                # ── Recently expired (win-back) ──
                st.markdown("---")
                st.markdown("#### 💔 Recently expired (last 30 days)")
                if already_expired.empty:
                    st.success("✅ No expired users.")
                else:
                    already_expired["sub_end_dt"] = pd.to_datetime(
                        already_expired["subscription_end"], errors="coerce", utc=True
                    ).dt.tz_localize(None)
                    recent_expired = already_expired[
                        already_expired["sub_end_dt"] >= pd.Timestamp(now - timedelta(days=30))
                    ].sort_values("sub_end_dt", ascending=False)

                    if recent_expired.empty:
                        st.success("✅ No users expired in the last 30 days.")
                    else:
                        st.warning(f"{len(recent_expired)} user(s) lapsed recently — "
                                   "consider a win-back message.")
                        for _, u in recent_expired.iterrows():
                            with st.container(border=True):
                                col1, col2, col3 = st.columns([3, 2, 2])
                                with col1:
                                    st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                                    st.caption(
                                        f"📧 {u['email']} | {u.get('plan_type','').capitalize()} | "
                                        f"Expired: {u['sub_end_dt'].strftime('%d %b %Y') if pd.notna(u['sub_end_dt']) else 'unknown'}"
                                    )
                                with col2:
                                    ext_days  = 365 if u.get("plan_type") == "yearly" else 30
                                    ext_label = "1 year" if ext_days == 365 else "30 days"
                                    if st.button(f"🔁 Reactivate ({ext_label})",
                                                 key=f"react_{u['user_id']}"):
                                        new_end = (datetime.now() + timedelta(days=ext_days)).strftime("%Y-%m-%d")
                                        db_update(TBL_USERS, "user_id", u["user_id"], {
                                                "plan_status":      "active",
                                                "subscription_start": datetime.now().strftime("%Y-%m-%d"),
                                                "subscription_end": new_end,
                                            })
                                        pay_amount = (PAYMENT_DETAILS["yearly_price"]
                                                      if ext_days == 365
                                                      else PAYMENT_DETAILS["monthly_price"])
                                        log_payment(
                                            u["user_id"], u["business_name"], u["email"],
                                            u.get("plan_type", "monthly"), pay_amount,
                                            "Reactivation — win-back"
                                        )
                                        st.cache_data.clear()
                                        st.success(f"✅ Reactivated until {new_end}")
                                        st.rerun()
                                with col3:
                                    st.caption("📤 Send Flutterwave link to renew")

    # ── Password Resets ──
    with tab5:
        if "password_reset_requested" not in users_df.columns:
            st.info("No password reset requests yet.")
        else:
            reset_df = users_df[users_df["password_reset_requested"] == "yes"]
            if reset_df.empty:
                st.success("✅ No pending password reset requests.")
            else:
                st.warning(f"{len(reset_df)} pending reset request(s)")
                for _, u in reset_df.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 2])
                        with col1:
                            st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                            st.caption(
                                f"📧 {u['email']} | "
                                f"Requested: {u.get('reset_requested_at', 'unknown')}"
                            )
                        with col2:
                            btn_key  = f"genpw_{u['user_id']}"
                            show_key = f"show_temp_{u['user_id']}"

                            if st.button("🔑 Generate Temp Password", key=btn_key):
                                # Generate a cryptographically random 10-char password
                                # Admin never types it — system creates it and shows it once
                                alphabet = string.ascii_letters + string.digits + "!@#$"
                                temp_pw  = "".join(secrets.choice(alphabet) for _ in range(10))
                                hashed   = bcrypt.hashpw(
                                    temp_pw.encode(), bcrypt.gensalt()
                                ).decode()
                                ok = db_update(TBL_USERS, "user_id", u["user_id"], {
                                        "password_hash":            hashed,
                                        "password_reset_requested": "no",
                                        "reset_requested_at":       None,
                                        "must_change_password":     "yes",
                                    })
                                st.cache_data.clear()
                                if ok:
                                    # Store in session_state so it survives the rerun
                                    st.session_state[show_key] = temp_pw

                            # Show temp password if just generated — copy and send to user
                            if show_key in st.session_state:
                                st.success("✅ Password generated! Send this to the user:")
                                st.code(st.session_state[show_key], language=None)
                                st.caption(
                                    "⚠️ Copy it now — it won't be shown again. "
                                    "The user will be forced to change it on first login."
                                )
                                if st.button("✔ Done — clear", key=f"clear_{u['user_id']}"):
                                    del st.session_state[show_key]
                                    st.rerun()

                        with col3:
                            if st.button("✖ Dismiss", key=f"dismis_{u['user_id']}"):
                                db_update(TBL_USERS, "user_id", u["user_id"], {"password_reset_requested": "no",
                                     "reset_requested_at": None})
                                st.cache_data.clear()
                                st.rerun()
                    st.markdown("---")

    # ── All Users ──
    with tab6:
        show_cols = ["business_name","full_name","email","plan_type","plan_status","subscription_end","created_at"]
        display   = users_df[[c for c in show_cols if c in users_df.columns]]

        admin_search = st.text_input("🔍 Search users", key="admin_user_search", placeholder="Name, email or business…")
        if admin_search:
            mask = (
                display["business_name"].str.contains(admin_search, case=False, na=False) |
                display["full_name"].str.contains(admin_search, case=False, na=False) |
                display["email"].str.contains(admin_search, case=False, na=False)
            )
            display = display[mask]

        AU_PAGE = 25
        au_total = max(1, -(-len(display) // AU_PAGE))
        if "au_page" not in st.session_state:
            st.session_state.au_page = 1
        au_pg = st.session_state.au_page
        display_page = display.iloc[(au_pg - 1) * AU_PAGE: au_pg * AU_PAGE]
        st.caption(f"Showing {len(display_page)} of {len(display)} users  •  Page {au_pg} of {au_total}")
        st.dataframe(display_page, use_container_width=True)

        if au_total > 1:
            au1, au2, au3 = st.columns([1, 3, 1])
            if au1.button("◀ Prev", disabled=(au_pg <= 1), key="au_prev"):
                st.session_state.au_page = max(1, au_pg - 1)
                st.rerun()
            au2.markdown(f"<div style='text-align:center;padding-top:0.5rem;color:#8BA0B8;'>Page {au_pg} of {au_total}</div>", unsafe_allow_html=True)
            if au3.button("Next ▶", disabled=(au_pg >= au_total), key="au_next"):
                st.session_state.au_page = min(au_total, au_pg + 1)
                st.rerun()

        csv = users_df[[c for c in show_cols if c in users_df.columns]].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export All Users CSV", data=csv,
                           file_name="bizpulse_users.csv", mime="text/csv")

    # ── Deactivated ──
    with tab7:
        deactivated_df = users_df[users_df["plan_status"] == "expired"]
        if deactivated_df.empty:
            st.success("✅ No deactivated accounts.")
        else:
            st.info(f"{len(deactivated_df)} deactivated account(s). Choose a plan and reactivate.")
            for _, u in deactivated_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.markdown(f"**{u['business_name']}** — {u['full_name']}")
                        st.caption(
                            f"📧 {u['email']} | "
                            f"Was: {u.get('plan_type','?')} | "
                            f"Expired: {u.get('subscription_end','?')}"
                        )
                    with col2:
                        plan_choice = st.selectbox(
                            "Plan",
                            options=["monthly", "yearly"],
                            format_func=lambda x: "Monthly (30d)" if x == "monthly" else "Yearly (365d)",
                            key=f"react_plan_{u['user_id']}",
                        )
                    with col3:
                        if st.button("✅ Reactivate", key=f"reactivate_{u['user_id']}"):
                            days    = 365 if plan_choice == "yearly" else 30
                            new_end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                            ok = db_update(TBL_USERS, "user_id", u["user_id"], {
                                "plan_status":        "active",
                                "plan_type":          plan_choice,
                                "subscription_start": datetime.now().strftime("%Y-%m-%d"),
                                "subscription_end":   new_end,
                            })
                            if ok:
                                pay_amount = (
                                    PAYMENT_DETAILS["yearly_price"]
                                    if plan_choice == "yearly"
                                    else PAYMENT_DETAILS["monthly_price"]
                                )
                                log_payment(
                                    u["user_id"], u["business_name"], u["email"],
                                    plan_choice, pay_amount, "Reactivation"
                                )
                                st.cache_data.clear()
                                st.success(f"✅ {u['business_name']} reactivated until {new_end}")
                                st.rerun()
                    st.markdown("---")


# ─────────────────────────────────────────────
#  SIDEBAR NAVIGATION
# ─────────────────────────────────────────────

def render_sidebar():
    inject_sidebar_toggle()   # inject custom toggle tab on every logged-in render
    user     = st.session_state.get("user", {})
    is_admin = user.get("role") == "admin"
    current  = st.session_state.get("current_page", "dashboard")

    with st.sidebar:
        # ── Logo ──
        st.markdown("""
<div style="padding:1.25rem 0.5rem 1.5rem 0.5rem;">
<div style="display:flex;align-items:center;gap:0.6rem;">
<div style="
width:32px;height:32px;border-radius:8px;
background:linear-gradient(135deg,#F5A623,#C4831A);
display:flex;align-items:center;justify-content:center;
font-size:0.95rem;flex-shrink:0;
box-shadow:0 3px 10px rgba(245,166,35,0.4);
">📊</div>
<div style="
font-family:'Syne',sans-serif;
font-size:1.25rem;font-weight:800;
color:#F0F4F8;letter-spacing:-0.04em;
">BizPulse</div>
</div>
</div>
        """, unsafe_allow_html=True)

        # ── User card ──
        plan_status = user.get("plan_status","")
        plan_type   = user.get("plan_type","")
        sub_end     = user.get("subscription_end","")
        if plan_status == "active":
            end_dt    = parse_date(sub_end)
            days_left = (end_dt - datetime.now()).days if end_dt else 0
            status_color = "#F5A623" if days_left > 7 else "#FF4D6D"
            status_text  = f"{days_left}d remaining"
        else:
            status_color = "#FF4D6D"
            status_text  = "Inactive"

        st.markdown(f"""
<div style="
background:#0D1117;border:1px solid #1F2D3D;
border-radius:12px;padding:0.875rem 1rem;
margin-bottom:1.5rem;
">
<div style="font-size:0.65rem;color:#4A6080;text-transform:uppercase;
letter-spacing:0.1em;font-weight:600;margin-bottom:0.3rem;">
Active Business
</div>
<div style="font-size:0.95rem;font-weight:700;
color:#F0F4F8;font-family:'Syne',sans-serif;
letter-spacing:-0.02em;margin-bottom:0.1rem;">
{user.get('business_name','—')}
</div>
<div style="font-size:0.75rem;color:#4A6080;margin-bottom:0.5rem;">
{user.get('full_name','')}
</div>
<div style="display:flex;align-items:center;gap:0.4rem;">
<div style="width:6px;height:6px;border-radius:50%;
background:{status_color};flex-shrink:0;
box-shadow:0 0 6px {status_color};"></div>
<div style="font-size:0.7rem;color:{status_color};font-weight:600;">
{plan_type.capitalize()} · {status_text}
</div>
</div>
</div>
        """, unsafe_allow_html=True)

        # ── Navigation ──
        nav_items = [
            ("dashboard",      "🏠", "Dashboard"),
            ("record_sale",    "🛒", "Record Sale"),
            ("sales_history",  "📋", "Sales History"),
            ("products",       "📦", "Products"),
            ("expenses",       "💸", "Expenses"),
            ("insights",       "🧠", "Insights"),
        ]
        if is_admin:
            nav_items.append(("admin", "🛡️", "Admin Panel"))

        for page_key, icon, label in nav_items:
            is_active = current == page_key
            btn_style = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type=btn_style,
            ):
                st.session_state.current_page = page_key
                st.rerun()

        # ── Bottom actions ──
        st.markdown("""
<div style="position:fixed;bottom:0;left:0;width:260px;
padding:1rem;background:#080B0F;
border-top:1px solid #1F2D3D;">
</div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
        if st.button("🔑  Change Password", use_container_width=True):
            st.session_state.current_page = "change_password"
            st.rerun()
        if st.button("🚪  Sign Out", use_container_width=True):
            for key in ["user", "logged_in", "current_page"]:
                st.session_state.pop(key, None)
            st.rerun()


# ─────────────────────────────────────────────
#  SUBSCRIPTION GUARD
# ─────────────────────────────────────────────

def check_access():
    """
    Returns True if user can access the app.
    Handles pending payment and expired subscriptions.
    """
    user = st.session_state.get("user", {})
    role = user.get("role", "")

    # Admin always has access
    if role == "admin":
        return True

    status = user.get("plan_status", "")

    if status == "pending_payment":
        page_pending_payment()
        return False

    if status == "expired":
        inject_styles()
        email = user.get("email", "")
        st.markdown(f"""
<div style="max-width:560px;margin:3rem auto;background:white;border-radius:20px;
padding:2.5rem;box-shadow:0 20px 60px rgba(0,0,0,0.08);
border:1px solid #e2e8f0;text-align:center;">
<div style="font-size:2.5rem;margin-bottom:0.5rem;">⏰</div>
<div style="font-size:1.4rem;font-weight:800;color:#0f172a;margin-bottom:0.5rem;">
Subscription Expired
</div>
<div style="color:#64748b;font-size:0.9rem;margin-bottom:2rem;">
Your access period has ended. Renew to continue using BizPulse.
</div>
<div style="background:#f8fafc;border-radius:14px;padding:1.25rem;
border:1px solid #e2e8f0;margin-bottom:1.75rem;text-align:left;">
<div style="display:flex;justify-content:space-between;margin-bottom:0.6rem;">
<span style="font-weight:600;color:#334155;">Monthly</span>
<span style="font-weight:700;color:#0f172a;">
₦{PAYMENT_DETAILS['monthly_price']:,}/month
</span>
</div>
<div style="display:flex;justify-content:space-between;">
<span style="font-weight:600;color:#334155;">Yearly</span>
<span style="font-weight:700;color:#10b981;">
₦{PAYMENT_DETAILS['yearly_price']:,}/year — save ₦3,000
</span>
</div>
</div>
<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:1.5rem;">
🔒 Secure payment via Flutterwave. Reactivated within 24 hours.
</div>
</div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.link_button(
                f"💳 Renew Monthly — ₦{PAYMENT_DETAILS['monthly_price']:,}",
                url=PAYMENT_DETAILS["flutterwave_monthly"],
                use_container_width=True,
                type="primary",
            )
            st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
            st.link_button(
                f"🏆 Renew Yearly — ₦{PAYMENT_DETAILS['yearly_price']:,} (best value)",
                url=PAYMENT_DETAILS["flutterwave_yearly"],
                use_container_width=True,
            )
            st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
            if st.button("Sign Out", use_container_width=True):
                for key in ["user", "logged_in", "current_page"]:
                    st.session_state.pop(key, None)
                st.rerun()
        return False

    if not is_subscription_active(user):
        # Auto-mark as expired
        db_update(TBL_USERS, "user_id", user["user_id"], {"plan_status": "expired"})
        st.session_state.user["plan_status"] = "expired"
        st.rerun()

    return True


# ─────────────────────────────────────────────
#  MAIN ROUTER
# ─────────────────────────────────────────────

def main():
    inject_styles()

    # Initialise session state keys
    if "logged_in"    not in st.session_state: st.session_state.logged_in    = False
    if "current_page" not in st.session_state: st.session_state.current_page = "login"
    if "user"         not in st.session_state: st.session_state.user         = {}

    # ── Not logged in ──
    if not st.session_state.logged_in:
        if st.session_state.current_page == "signup":
            page_signup()
        elif st.session_state.current_page == "pending_payment":
            page_pending_payment()
        elif st.session_state.current_page == "forgot_password":
            page_forgot_password()
        else:
            page_login()
        return

    # ── Logged in: intercept forced password change BEFORE check_access ──
    if (st.session_state.get("logged_in") and
            str(st.session_state.get("user", {}).get("must_change_password", "")).lower() == "yes"):
        page_change_password(forced=True)
        return

    # ── Logged in: check access ──
    if not check_access():
        return

    # ── Render sidebar + route to page ──
    render_sidebar()
    page = st.session_state.get("current_page", "dashboard")

    if   page == "dashboard":        page_dashboard()
    elif page == "record_sale":      page_record_sale()
    elif page == "sales_history":    page_sales_history()
    elif page == "products":         page_products()
    elif page == "expenses":         page_expenses()
    elif page == "insights":         page_insights()
    elif page == "change_password":  page_change_password(forced=False)
    elif page == "admin":
        if st.session_state.user.get("role") == "admin":
            page_admin()
        else:
            st.error("Access denied.")
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
