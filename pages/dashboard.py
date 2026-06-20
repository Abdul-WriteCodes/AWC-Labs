import streamlit as st
from datetime import datetime
from utils.auth import get_current_participant, logout
from utils.sheets import get_progress, mark_task_done, get_active_week
from data.content import PROGRAM_WEEKS, AI_CAREER_PATHS
from config import PROGRAM_NAME, TOTAL_WEEKS


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
    active_week = get_active_week()
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
                    mark_task_done(email, week_num, idx, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.toast(f"Task marked complete!", icon="✅")
                    st.rerun()

            # Week completion badge
            if len(week_done) == len(week_data["tasks"]):
                st.success(f"✅ Week {week_num} complete! Great work, {first_name}.")

    st.divider()

    # ── AI Career Paths reference ─────────────────────────────
    with st.expander("AI career paths — quick reference"):
        for path in AI_CAREER_PATHS:
            st.markdown(f"**{path['title']}** — {path['desc']}")
