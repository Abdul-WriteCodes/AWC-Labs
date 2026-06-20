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
    """Load from sheet once per session, keep in memory after."""
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


def show():
    participant = get_current_participant()
    first_name  = participant["full_name"].split()[0]
    email       = participant["email"]

    # ── Header ────────────────────────────────────────────────
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"## Welcome back, {first_name} 👋")
        st.caption(f"{PROGRAM_NAME} · {participant['cohort_type']}")
    with col2:
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()

    st.divider()

    # ── Progress summary ──────────────────────────────────────
    active_week = get_active_week_cached()
    progress    = get_progress(email)

    total_tasks     = sum(len(PROGRAM_WEEKS[w]["tasks"]) for w in range(1, active_week + 1))
    completed_tasks = sum(len(v) for v in progress.values())
    pct             = int((completed_tasks / total_tasks * 100) if total_tasks else 0)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Current week", f"Week {active_week}")
    col_b.metric("Tasks completed", f"{completed_tasks} / {total_tasks}")
    col_c.metric("Overall progress", f"{pct}%")

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
            if locked:
                st.info(f"🔒 Week {week_num} — **{week_data['title']}** unlocks when the cohort reaches it.")
                continue

            st.markdown(f"### {week_data['title']}")
            st.caption(week_data["theme"])
            st.markdown("")

            # Materials
            st.markdown("**This week's materials**")
            for mat in week_data["materials"]:
                icon = {"book": "📖", "video": "🎥", "article": "📄", "worksheet": "📝", "template": "🗂️"}.get(mat["type"], "•")
                st.markdown(f"{icon} {mat['label']}")

            st.markdown("")

            # Tasks
            st.markdown("**Your tasks this week**")
            week_done = progress.get(week_num, [])

            for idx, task in enumerate(week_data["tasks"]):
                done = idx in week_done
                col_check, col_task = st.columns([1, 10])
                with col_check:
                    checked = st.checkbox("", value=done, key=f"task_{week_num}_{idx}", disabled=done)
                with col_task:
                    if done:
                        st.markdown(f"~~{task}~~ ✓")
                    else:
                        st.markdown(task)

                if checked and not done:
                    mark_task_done(
                        email, week_num, idx,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    st.toast("Task marked complete!", icon="✅")
                    st.rerun()

            st.markdown("")
            st.divider()

            # ── Reflection ────────────────────────────────────
            all_tasks_done = len(week_done) == len(week_data["tasks"])
            reflection     = get_reflection_cached(email, week_num)

            if not all_tasks_done:
                st.info("✏️ Complete all tasks above to unlock this week's reflection.")
            elif reflection:
                st.success(f"✅ Week {week_num} complete! Great work, {first_name}.")
                with st.expander("📝 Your reflection", expanded=False):
                    st.markdown(reflection.get("response", ""))

                # Feedback from admin
                feedback = get_feedback(email, week_num)
                if feedback:
                    st.markdown("**Feedback from Abdul:**")
                    st.info(feedback)
            else:
                # All tasks done but no reflection yet — show the prompt
                prompt = get_prompt(week_num)
                if prompt:
                    st.markdown("**Weekly reflection**")
                    st.markdown(f"_{prompt}_")
                    response = st.text_area(
                        "Your response",
                        placeholder="Write your reflection here...",
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
                    st.success(f"✅ All tasks done! Reflection prompt coming soon.")

    st.divider()

    # ── Manual refresh ────────────────────────────────────────
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Refresh my progress"):
            if "progress" in st.session_state:
                del st.session_state["progress"]
            st.rerun()
    with col_r2:
        if st.button("🔄 Check for new weeks"):
            if "active_week" in st.session_state:
                del st.session_state["active_week"]
            if "active_week_last_check" in st.session_state:
                del st.session_state["active_week_last_check"]
            st.rerun()

    # ── AI Career Paths reference ─────────────────────────────
    with st.expander("AI career paths — quick reference"):
        for path in AI_CAREER_PATHS:
            st.markdown(f"**{path['title']}** — {path['desc']}")
