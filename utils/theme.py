"""
utils/theme.py
══════════════════════════════════════════════════════════════════════
Crea8it — Shared CSS + UI Component Library
══════════════════════════════════════════════════════════════════════

Exports:
  apply_css()              → inject full CSS (call once per page)
  kpi_card(...)            → gold-accented metric card
  section_label(text)      → uppercase section divider label
  page_header(title, sub)  → full-width heading with cohort badge
  task_card(...)           → premium task row (done / pending state)
  week_badge(week, active) → LIVE / DONE / LOCKED pill HTML
  material_card(icon, label) → material row card HTML
  reflection_box(prompt)   → styled reflection prompt callout
  feedback_box(text)       → admin feedback callout
"""

from __future__ import annotations
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

def apply_css():
    """Inject unified Crea8it dark-theme CSS. Safe to call multiple times."""
    st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Variables ── */
:root {
  --obsidian:   #080B0F;
  --deep:       #0D1117;
  --surface:    #111827;
  --surface2:   #1A2332;
  --border:     #1F2D3D;
  --border2:    #2D3F55;
  --gold:       #F5A623;
  --gold-dim:   #C4831A;
  --gold-glow:  rgba(245,166,35,0.15);
  --teal:       #00B4D8;
  --jade:       #00C896;
  --jade-dim:   rgba(0,200,150,0.10);
  --ruby:       #FF4D6D;
  --text-1:     #F0F4F8;
  --text-2:     #8BA0B8;
  --text-3:     #4A6080;
  --font-d: 'Syne', sans-serif;
  --font-b: 'DM Sans', sans-serif;
  --font-m: 'DM Mono', monospace;
}

/* ── Base ── */
html, body, [class*="css"], .stApp {
  font-family: var(--font-b) !important;
  background-color: var(--obsidian) !important;
  color: var(--text-1) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background-color: var(--deep) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] { padding: 0.5rem 0.75rem; }

/* Sidebar collapse button — keep visible, don't touch */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}

[data-testid="stHeader"] {
    background: #080B0F !important;
    
    height: 36px !important;
    min-height: 36px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}


/* Hide only the auto-page-list, not the toggle */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Main container ── */
[data-testid="stAppViewContainer"] > .main { background: var(--obsidian); }
[data-testid="block-container"] { padding-top: 1.5rem !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Buttons ── */
.stButton > button {
  background: var(--gold) !important;
  color: var(--obsidian) !important;
  font-family: var(--font-b) !important;
  font-weight: 700 !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 0.5rem 1.25rem !important;
  transition: background 0.2s, box-shadow 0.2s !important;
}
.stButton > button:hover {
  background: var(--gold-dim) !important;
  box-shadow: 0 4px 16px var(--gold-glow) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface) !important;
  color: var(--text-2) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--border2) !important;
  color: var(--text-1) !important;
  box-shadow: none !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
  background: var(--surface) !important;
  color: var(--text-1) !important;
  border-color: var(--border) !important;
  border-radius: 8px !important;
  font-family: var(--font-b) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--teal) !important;
  box-shadow: 0 0 0 2px rgba(0,180,216,0.12) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label {
  color: var(--text-3) !important;
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
[data-testid="stSelectbox"] > div {
  background: var(--surface) !important;
  color: var(--text-1) !important;
  border-color: var(--border) !important;
}

/* ── Tabs — underline style (sidebar toggle safe) ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-3) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  border-bottom: 2px solid transparent !important;
  padding: 8px 16px !important;
  border-radius: 0 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--gold) !important;
  border-bottom-color: var(--gold) !important;
  font-weight: 700 !important;
  background: transparent !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] > div {
  color: var(--text-3) !important;
  font-size: 0.7rem !important;
  font-family: var(--font-m) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}
[data-testid="stMetricValue"] > div {
  color: var(--gold) !important;
  font-family: var(--font-d) !important;
  font-size: 1.6rem !important;
  font-weight: 800 !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div {
  background: var(--surface2) !important;
  border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--teal), var(--gold)) !important;
  border-radius: 4px !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"]:hover { border-color: var(--border2) !important; }
[data-testid="stExpander"] summary { color: var(--text-2) !important; }

/* ── Dataframes ── */
[data-testid="stDataFrame"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 10px !important; border: none !important; }

/* ── Checkbox ── */
.stCheckbox label { color: var(--text-2) !important; font-size: 0.9rem !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.25rem 0 !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── Custom component classes ── */

/* KPI card */
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.125rem 1.25rem;
  margin-bottom: 0.75rem;
  transition: border-color 0.2s;
}
.kpi-card:hover { border-color: var(--border2); }
.kpi-header { display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem; }
.kpi-icon  { font-size:1.1rem; }
.kpi-label {
  font-size:0.7rem; font-weight:600; color:var(--text-3);
  text-transform:uppercase; letter-spacing:0.1em; font-family:var(--font-m);
}
.kpi-value {
  font-family:var(--font-d); font-size:1.55rem; font-weight:800;
  color:var(--text-1); letter-spacing:-0.04em; line-height:1.1;
}
.kpi-sub { font-size:0.78rem; color:var(--text-2); margin-top:0.25rem; }
.kpi-positive { color:var(--jade) !important; }
.kpi-negative { color:var(--ruby) !important; }

/* Task card */
.task-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
  transition: border-color 0.2s;
}
.task-card:hover { border-color: var(--border2); }
.task-card.done {
  background: var(--jade-dim);
  border-color: rgba(0,200,150,0.2);
}
.task-icon {
  width: 28px; height: 28px; flex-shrink: 0;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem;
  margin-top: 1px;
}
.task-icon.pending {
  background: var(--surface2);
  border: 1.5px solid var(--border2);
  color: var(--text-3);
}
.task-icon.complete {
  background: rgba(0,200,150,0.15);
  border: 1.5px solid var(--jade);
  color: var(--jade);
}
.task-body { flex: 1; }
.task-text {
  font-size: 0.9rem;
  color: var(--text-1);
  line-height: 1.5;
  font-family: var(--font-b);
}
.task-text.muted { color: var(--text-3); }
.task-status {
  font-size: 0.72rem;
  font-family: var(--font-m);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 4px;
}
.task-status.done-label { color: var(--jade); }
.task-status.pending-label { color: var(--text-3); }

/* Material card */
.mat-card {
  display: flex; align-items: center; gap: 12px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 11px 14px; margin-bottom: 6px;
  font-size: 0.88rem; color: var(--text-2);
  transition: border-color 0.2s;
}
.mat-card:hover { border-color: var(--border2); color: var(--text-1); }
.mat-icon { font-size: 1.1rem; }

/* Section label */
.section-label {
  font-family: var(--font-m);
  font-size: 0.68rem; font-weight: 600;
  color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.12em;
  margin: 1.25rem 0 0.6rem 0;
  display: flex; align-items: center; gap: 8px;
}
.section-label::after {
  content: ""; flex: 1;
  height: 1px; background: var(--border);
}

/* Week badge pills */
.badge {
  display: inline-block;
  border-radius: 20px; padding: 2px 10px;
  font-size: 0.68rem; font-weight: 700;
  font-family: var(--font-m); letter-spacing: 0.06em;
  text-transform: uppercase;
}
.badge-live   { background:rgba(245,166,35,0.12); color:var(--gold);  border:1px solid rgba(245,166,35,0.3); }
.badge-done   { background:var(--jade-dim);        color:var(--jade);  border:1px solid rgba(0,200,150,0.3); }
.badge-locked { background:rgba(255,255,255,0.03); color:var(--text-3);border:1px solid var(--border); }

/* Reflection callout */
.reflection-prompt {
  background: rgba(245,166,35,0.05);
  border: 1px solid rgba(245,166,35,0.18);
  border-left: 3px solid var(--gold);
  border-radius: 0 10px 10px 0;
  padding: 14px 18px;
  margin-bottom: 14px;
  font-size: 0.9rem;
  color: #C4A060;
  font-style: italic;
  line-height: 1.65;
}

/* Feedback callout */
.feedback-box {
  background: rgba(0,180,216,0.05);
  border: 1px solid rgba(0,180,216,0.18);
  border-left: 3px solid var(--teal);
  border-radius: 0 10px 10px 0;
  padding: 14px 18px;
  font-size: 0.88rem;
  color: #80B4C8;
  line-height: 1.65;
}

/* Landing page */
.lp-hero { text-align:center; padding:2.5rem 1rem 1.5rem; max-width:820px; margin:0 auto; }
.lp-wordmark {
  font-family: var(--font-d);
  font-size: 3rem; font-weight: 800;
  letter-spacing: -0.05em; line-height: 1;
  margin-bottom: 0.5rem;
}
.lp-wordmark .c8-8 { color: var(--gold); }
.lp-wordmark .c8-teal { color: var(--teal); }
.lp-wordmark .c8-white { color: var(--text-1); }
.lp-tagline {
  font-size: 0.72rem; color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.15em;
  margin-bottom: 1.5rem; font-family: var(--font-m);
}
.lp-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 99px; padding: 0.3rem 1rem;
  font-size: 0.75rem; color: var(--text-2);
  margin-bottom: 2rem;
}
.lp-badge .dot { color: var(--jade); font-size: 0.5rem; }
.lp-value-grid { display:flex; gap:0.75rem; flex-wrap:wrap; justify-content:center; margin-bottom:2rem; }
.lp-value-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1.1rem 1rem; text-align:left;
  flex:1; min-width:170px; max-width:210px;
  transition: border-color 0.2s;
}
.lp-value-card:hover { border-color: var(--border2); }
.lp-value-icon  { font-size:1.4rem; margin-bottom:0.4rem; }
.lp-value-title { font-weight:700; color:var(--text-1); font-size:0.85rem; margin-bottom:0.25rem; }
.lp-value-desc  { font-size:0.75rem; color:var(--text-2); line-height:1.5; }
.lp-trust-strip {
  display:flex; flex-wrap:wrap; justify-content:center; gap:1rem;
  padding:1rem 0 0.5rem; border-top:1px solid var(--border); margin-top:1.5rem;
}
.lp-trust-item { font-size:0.75rem; color:var(--text-3); }
.lp-trust-item .check { color:var(--jade); margin-right:0.3rem; }

/* Alert custom */
.alert-info {
  background:rgba(0,180,216,0.07); border:1px solid rgba(0,180,216,0.2);
  border-radius:10px; padding:12px 16px; color:#6BAEC8; font-size:0.85rem;
  margin-bottom:0.5rem;
}
.alert-success {
  background:var(--jade-dim); border:1px solid rgba(0,200,150,0.25);
  border-radius:10px; padding:12px 16px; color:#50C896; font-size:0.85rem;
  margin-bottom:0.5rem;
}
.alert-warn {
  background:rgba(245,166,35,0.07); border:1px solid rgba(245,166,35,0.2);
  border-radius:10px; padding:12px 16px; color:#C4A060; font-size:0.85rem;
  margin-bottom:0.5rem;
}
</style>
""")


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def kpi_card(label: str, value, sub: str = "",
             positive: bool | None = None, icon: str = ""):
    sub_class = ""
    if positive is True:  sub_class = "kpi-positive"
    elif positive is False: sub_class = "kpi-negative"
    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""
    st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-header">{icon_html}<div class="kpi-label">{label}</div></div>
  <div class="kpi-value">{value}</div>
  {f'<div class="kpi-sub {sub_class}">{sub}</div>' if sub else ""}
</div>""", unsafe_allow_html=True)


def section_label(text: str, color: str = ""):
    accent = f"color:{color};" if color else ""
    st.markdown(f'<div class="section-label" style="{accent}">{text}</div>',
                unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
<div style="margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid var(--border);">
  <div style="font-family:var(--font-d);font-size:1.7rem;font-weight:800;
              color:var(--text-1);letter-spacing:-0.04em;line-height:1.1;">
    {title}
  </div>
  {f'<div style="font-size:0.82rem;color:var(--text-3);margin-top:4px;">{subtitle}</div>' if subtitle else ""}
</div>""", unsafe_allow_html=True)


def week_badge(week_num: int, active_week: int) -> str:
    if week_num < active_week:
        return '<span class="badge badge-done">Done</span>'
    elif week_num == active_week:
        return '<span class="badge badge-live">Live</span>'
    else:
        return '<span class="badge badge-locked">Locked</span>'


import re as _re


def _render_links(text: str) -> str:
    """Convert markdown [label](url) and bare URLs into clickable <a> tags.
    Safe to call on plain text — returns it unchanged if no links found.
    """
    ls = "color:var(--teal);text-decoration:underline;"
    # [label](url) pattern
    text = _re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        lambda m: '<a href="{u}" target="_blank" rel="noopener" style="{s}">{l}</a>'.format(
            u=m.group(2), l=m.group(1), s=ls),
        text
    )
    # bare URLs not already inside href="..."
    text = _re.sub(
        r'(?<!href=")(https?://\S+)',
        lambda m: '<a href="{u}" target="_blank" rel="noopener" style="{s}">{u}</a>'.format(
            u=m.group(1), s=ls),
        text
    )
    return text


def task_card(text: str, done: bool):
    """Render a styled task card. Markdown links in text become clickable."""
    rendered = _render_links(text)
    if done:
        st.markdown(f"""
<div class="task-card done">
  <div class="task-icon complete">&#10003;</div>
  <div class="task-body">
    <div class="task-text muted">{rendered}</div>
    <div class="task-status done-label">Completed</div>
  </div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="task-card">
  <div class="task-icon pending">&#9675;</div>
  <div class="task-body">
    <div class="task-text">{rendered}</div>
    <div class="task-status pending-label">Pending</div>
  </div>
</div>""", unsafe_allow_html=True)


def material_card(icon: str, label: str):
    """Render a material card. Markdown links in label become clickable."""
    rendered = _render_links(label)
    st.markdown(f"""
<div class="mat-card">
  <span class="mat-icon">{icon}</span>
  <span>{rendered}</span>
</div>""", unsafe_allow_html=True)


def reflection_box(prompt: str):
    st.markdown(f'<div class="reflection-prompt">{prompt}</div>',
                unsafe_allow_html=True)


def feedback_box(text: str):
    st.markdown(f'<div class="feedback-box">{text}</div>',
                unsafe_allow_html=True)
