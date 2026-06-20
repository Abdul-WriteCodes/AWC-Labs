import streamlit as st
from datetime import datetime
from utils.auth import get_current_participant, logout
from utils.sheets import (
    get_progress_from_sheet, mark_task_done, get_active_week_live,
    get_reflection, submit_reflection, get_feedback, get_prompt,
)
from data.content import PROGRAM_WEEKS, AI_CAREER_PATHS
from config import PROGRAM_NAME, TOTAL_WEEKS
import time


def get_progress(email: str) -> dict:
    if "progress" not in st.session_state or st.session_state.get("progress_email") != email:
        st.session_state["progress"] = get_progress_from_sheet(email)
        st.session_state["progress_email"] = email
    return st.session_state["progress"]


def get_active_week_cached() -> int:
    now = time.time()
    last_check = st.session_state.get("active_week_last_check", 0)
    if now - last_check > 60 or "active_week" not in st.session_state:
        st.session_state["active_week"] = get_active_week_live()
        st.session_state["active_week_last_check"] = now
    return st.session_state["active_week"]


def get_reflection_cached(email: str, week: int) -> dict | None:
    key = f"reflection_{week}"
    if key not in st.session_state:
        st.session_state[key] = get_reflection(email, week)
    return st.session_state[key]


def week_badge(week_num: int, active_week: int) -> str:
    if week_num < active_week:
        return '<span style="background:rgba(0,200,120,0.12);color:#00C878;border:1px solid rgba(0,200,120,0.25);border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:600;">DONE</span>'
    elif week_num == active_week:
        return '<span style="background:rgba(244,160,34,0.12);color:#F4A022;border:1px solid rgba(244,160,34,0.25);border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:600;">LIVE</span>'
    else:
        return '<span style="background:rgba(255,255,255,0.04);color:#4A6478;border:1px solid #1A3A52;border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:600;">LOCKED</span>'


def show():
    participant = get_current_participant()
    first_name  = participant["full_name"].split()[0]
    email       = participant["email"]

    # ── Header ────────────────────────────────────────────────
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
            <div style="padding: 8px 0 4px 0;">
                <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; font-weight: 700; color: #E8EDF2;">
                    Welcome back, <span style="color: #F4A022;">{first_name}</span> 👋
                </div>
                <div style="font-size: 0.8rem; color: #4A6478; margin-top: 3px;">
                    {PROGRAM_NAME} · {participant['cohort_type']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Log out", type="secondary"):
            logout()
            st.rerun()

    st.divider()

    # ── Progress summary ──────────────────────────────────────
    active_week = get_active_week_cached()
    progress    = get_progress(email)

    total_tasks     = sum(len(PROGRAM_WEEKS[w]["tasks"]) for w in range(1, active_week + 1))
    completed_tasks = sum(len(v) for v in progress.values())
    pct             = min(100, int((completed_tasks / total_tasks * 100) if total_tasks else 0))

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Current week", f"Week {active_week}")
    col_b.metric("Tasks done", f"{completed_tasks} / {total_tasks}")
    col_c.metric("Progress", f"{pct}%")

    st.markdown("<div style='margin: 8px 0 4px 0; font-size: 0.72rem; color: #4A6478; text-transform: uppercase; letter-spacing: 0.08em;'>Overall completion</div>", unsafe_allow_html=True)
    st.progress(pct / 100)
    st.markdown("")

    # ── Week tabs ─────────────────────────────────────────────
    week_labels = [f"Week {w}" for w in range(1, TOTAL_WEEKS + 1)]
    tabs        = st.tabs(week_labels)

    for i, tab in enumerate(tabs):
        week_num  = i + 1
        week_data = PROGRAM_WEEKS[week_num]
        locked    = week_num > active_week

        with tab:
            # Week header
            st.markdown(f"""
                <div style="display:flex; align-items:center; gap:12px; padding: 4px 0 12px 0;">
                    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.2rem; font-weight:700; color:#E8EDF2;">
                        {week_data['title']}
                    </div>
                    {week_badge(week_num, active_week)}
                </div>
                <div style="font-size:0.83rem; color:#4A6478; margin-bottom:20px; font-style:italic;">
                    {week_data['theme']}
                </div>
            """, unsafe_allow_html=True)

            if locked:
                st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.02); border:1px dashed #1A3A52;
                                border-radius:12px; padding:32px; text-align:center; margin:12px 0;">
                        <div style="font-size:2rem; margin-bottom:10px;">🔒</div>
                        <div style="color:#4A6478; font-size:0.88rem;">
                            This week unlocks when the cohort progresses.<br>
                            Keep up with your current tasks.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                continue

            # Materials
            st.markdown("""
                <div style="font-size:0.72rem; color:#00B4D8; text-transform:uppercase;
                            letter-spacing:0.1em; font-weight:600; margin-bottom:10px;">
                    This week's materials
                </div>
            """, unsafe_allow_html=True)

            icon_map = {"book": "📖", "video": "🎥", "article": "📄", "worksheet": "📝", "template": "🗂️"}
            for mat in week_data["materials"]:
                icon = icon_map.get(mat["type"], "•")
                st.markdown(f"""
                    <div style="background:#0A1520; border:1px solid #1A3A52; border-radius:8px;
                                padding:10px 14px; margin-bottom:6px; font-size:0.88rem; color:#C8D6E0;">
                        {icon} &nbsp; {mat['label']}
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            # Tasks
            st.markdown("""
                <div style="font-size:0.72rem; color:#F4A022; text-transform:uppercase;
                            letter-spacing:0.1em; font-weight:600; margin-bottom:10px;">
                    Your tasks
                </div>
            """, unsafe_allow_html=True)

            week_done = progress.get(week_num, [])

            for idx, task in enumerate(week_data["tasks"]):
                done = idx in week_done
                col_check, col_task = st.columns([1, 11])
                with col_check:
                    checked = st.checkbox("", value=done, key=f"task_{week_num}_{idx}", disabled=done)
                with col_task:
                    if done:
                        st.markdown(f"<div style='padding:6px 0; color:#4A6478; text-decoration:line-through; font-size:0.9rem;'>{task} ✓</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='padding:6px 0; color:#C8D6E0; font-size:0.9rem;'>{task}</div>", unsafe_allow_html=True)

                if checked and not done:
                    mark_task_done(email, week_num, idx, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.toast("Task marked complete!", icon="✅")
                    st.rerun()

            st.divider()

            # ── Reflection ────────────────────────────────────
            all_tasks_done = len(week_done) == len(week_data["tasks"])
            reflection     = get_reflection_cached(email, week_num)

            if not all_tasks_done:
                remaining = len(week_data["tasks"]) - len(week_done)
                st.markdown(f"""
                    <div style="background:rgba(0,180,216,0.05); border:1px solid rgba(0,180,216,0.15);
                                border-radius:10px; padding:14px 18px; font-size:0.85rem; color:#5A8A9A;">
                        ✏️ Complete <strong style="color:#00B4D8;">{remaining} more task{"s" if remaining > 1 else ""}</strong>
                        to unlock this week's reflection.
                    </div>
                """, unsafe_allow_html=True)

            elif reflection:
                st.markdown(f"""
                    <div style="background:rgba(0,200,120,0.06); border:1px solid rgba(0,200,120,0.2);
                                border-radius:10px; padding:14px 18px; margin-bottom:12px;">
                        <div style="font-size:0.88rem; font-weight:600; color:#00C878;">
                            ✅ Week {week_num} complete — great work, {first_name}!
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander("📝 Your reflection"):
                    st.markdown(f"<div style='color:#A0B4C8; font-size:0.88rem; line-height:1.6;'>{reflection.get('response', '')}</div>", unsafe_allow_html=True)

                feedback = get_feedback(email, week_num)
                if feedback:
                    st.markdown("""
                        <div style="font-size:0.72rem; color:#F4A022; text-transform:uppercase;
                                    letter-spacing:0.1em; font-weight:600; margin: 16px 0 8px 0;">
                            Feedback from Abdul
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="background:rgba(244,160,34,0.06); border:1px solid rgba(244,160,34,0.2);
                                    border-left:3px solid #F4A022; border-radius:0 10px 10px 0;
                                    padding:14px 18px; font-size:0.88rem; color:#C4A060; line-height:1.6;">
                            {feedback}
                        </div>
                    """, unsafe_allow_html=True)

            else:
                prompt = get_prompt(week_num)
                if prompt:
                    st.markdown("""
                        <div style="font-size:0.72rem; color:#F4A022; text-transform:uppercase;
                                    letter-spacing:0.1em; font-weight:600; margin-bottom:10px;">
                            Weekly reflection
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="background:rgba(244,160,34,0.05); border:1px solid rgba(244,160,34,0.15);
                                    border-radius:10px; padding:14px 18px; margin-bottom:14px;
                                    font-size:0.9rem; color:#C4A060; font-style:italic; line-height:1.6;">
                            {prompt}
                        </div>
                    """, unsafe_allow_html=True)

                    response = st.text_area(
                        "Your response",
                        placeholder="Write your reflection here — be honest, specific, and thoughtful...",
                        key=f"reflection_input_{week_num}",
                        height=150,
                    )
                    if st.button("Submit reflection →", key=f"submit_reflection_{week_num}", type="primary"):
                        if response.strip():
                            submit_reflection(
                                email, week_num, response.strip(),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            st.toast("Reflection submitted!", icon="📝")
                            st.rerun()
                        else:
                            st.warning("Please write something before submitting.")
                else:
                    st.markdown(f"""
                        <div style="background:rgba(0,200,120,0.06); border:1px solid rgba(0,200,120,0.2);
                                    border-radius:10px; padding:14px 18px; font-size:0.88rem; color:#60A880;">
                            ✅ All tasks done! Your reflection prompt will appear here shortly.
                        </div>
                    """, unsafe_allow_html=True)

    st.divider()

    # ── Footer actions ────────────────────────────────────────
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Refresh my progress", use_container_width=True, type="secondary"):
            if "progress" in st.session_state:
                del st.session_state["progress"]
            st.rerun()
    with col_r2:
        if st.button("🔄 Check for new weeks", use_container_width=True, type="secondary"):
            for key in ["active_week", "active_week_last_check"]:
                st.session_state.pop(key, None)
            st.rerun()

    # ── AI career paths ───────────────────────────────────────
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    with st.expander("🧭 AI career paths — quick reference"):
        for path in AI_CAREER_PATHS:
            st.markdown(f"""
                <div style="padding: 8px 0; border-bottom: 1px solid #1A3A52;">
                    <span style="color:#F4A022; font-weight:600; font-size:0.88rem;">{path['title']}</span>
                    <span style="color:#7A94A8; font-size:0.85rem;"> — {path['desc']}</span>
                </div>
            """, unsafe_allow_html=True)
