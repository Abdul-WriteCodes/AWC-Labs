import streamlit as st
from datetime import datetime
from utils.auth import get_current_participant, logout
from utils.theme import (
    apply_css, page_header, section_label, week_badge,
    task_card, material_card, reflection_box, feedback_box, kpi_card,
)
from utils.sheets import (
    get_progress_from_sheet, mark_task_done, get_active_week_live,
    get_reflection, submit_reflection, get_feedback, get_prompt,
    get_program_weeks, get_active_program_id_live, get_active_unit_label_live,
)
from config import PROGRAM_NAME
import time


def get_progress(email: str) -> dict:
    if "progress" not in st.session_state or st.session_state.get("progress_email") != email:
        st.session_state["progress"] = get_progress_from_sheet(email)
        st.session_state["progress_email"] = email
    return st.session_state["progress"]


def get_active_week_cached() -> int:
    now = time.time()
    if now - st.session_state.get("active_week_last_check", 0) > 60 \
            or "active_week" not in st.session_state:
        st.session_state["active_week"] = get_active_week_live()
        st.session_state["active_week_last_check"] = now
    return st.session_state["active_week"]


def get_reflection_cached(email: str, week: int) -> dict | None:
    key = f"reflection_{week}"
    if key not in st.session_state:
        st.session_state[key] = get_reflection(email, week)
    return st.session_state[key]


def show():
    apply_css()

    # Load active program content
    active_pid   = get_active_program_id_live()
    PROGRAM_WEEKS = get_program_weeks(active_pid) if active_pid else {}
    TOTAL_WEEKS   = len(PROGRAM_WEEKS)
    unit_label    = get_active_unit_label_live() or "Week"

    # ── Celebration handler (runs at top of next rerun) ───────
    celebrate = st.session_state.pop("celebrate", None)
    if celebrate == "tasks":
        w = st.session_state.pop("celebrate_week", "")
        st.toast(f"{unit_label} {w} tasks complete! Now write your reflection 🎉", icon="🏅")
        st.balloons()
    elif celebrate == "reflection":
        w = st.session_state.pop("celebrate_week", "")
        st.toast(f"{unit_label} {w} reflection submitted — great work! 🙌", icon="📝")
        st.balloons()
    elif celebrate == "task_single":
        st.toast("Task marked complete!", icon="✅")

    participant = get_current_participant()
    first_name  = participant["full_name"].split()[0]
    email       = participant["email"]

    # ── Header ────────────────────────────────────────────────
    col1, col2 = st.columns([5, 1])
    with col1:
        page_header(
            f"Welcome back, {first_name}",
            f"{PROGRAM_NAME} · {participant['cohort_type']}"
        )
    with col2:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Log out", type="secondary"):
            logout()
            st.rerun()

    # ── KPI row ───────────────────────────────────────────────
    active_week = get_active_week_cached()
    progress    = get_progress(email)

    week_keys       = sorted(PROGRAM_WEEKS.keys())
    total_tasks     = sum(len(PROGRAM_WEEKS[w]["tasks"]) for w in week_keys if w <= active_week)
    completed_tasks = sum(len(v) for v in progress.values())
    pct             = min(100, int((completed_tasks / total_tasks * 100) if total_tasks else 0))

    col_a, col_b, col_c = st.columns(3)
    with col_a: kpi_card("Current unit",   f"{unit_label} {active_week}", icon="🗓")
    with col_b: kpi_card("Tasks done",     f"{completed_tasks}/{total_tasks}", icon="✅")
    with col_c: kpi_card("Progress",       f"{pct}%", icon="📈")

    section_label("Overall completion")
    st.progress(pct / 100)
    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Week tabs ─────────────────────────────────────────────
    tabs = st.tabs([f"{unit_label} {w}" for w in week_keys])

    for tab, week_num in zip(tabs, week_keys):
        week_data = PROGRAM_WEEKS[week_num]
        locked    = week_num > active_week

        with tab:
            # Week title + badge
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:6px 0 4px;">
  <div style="font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;color:#F0F4F8;">
    {week_data['title']}
  </div>
  {week_badge(week_num, active_week)}
</div>
<div style="font-size:0.82rem;color:#4A6080;margin-bottom:1.25rem;font-style:italic;">
  {week_data['theme']}
</div>""", unsafe_allow_html=True)

            # Locked state
            if locked:
                st.markdown("""
<div style="background:rgba(255,255,255,0.02);border:1px dashed #1F2D3D;
            border-radius:14px;padding:36px;text-align:center;margin:8px 0;">
  <div style="font-size:2rem;margin-bottom:10px;">🔒</div>
  <div style="color:#4A6080;font-size:0.88rem;line-height:1.6;">
    This week unlocks when the cohort progresses.<br>Keep up with your current tasks.
  </div>
</div>""", unsafe_allow_html=True)
                continue

            # Materials
            section_label("This week's materials", color="var(--teal)")
            icon_map = {"book":"📖","video":"🎥","article":"📄","worksheet":"📝","template":"🗂️"}
            for mat in week_data["materials"]:
                material_card(icon_map.get(mat["type"], "•"), mat["label"])

            # Tasks
            section_label("Your tasks", color="var(--gold)")
            week_done = progress.get(week_num, [])

            for idx, task in enumerate(week_data["tasks"]):
                done = idx in week_done
                if done:
                    task_card(task, done=True)
                else:
                    # Show card + a checkbox below it to mark complete
                    task_card(task, done=False)
                    checked = st.checkbox(
                        "Mark as complete",
                        key=f"task_{week_num}_{idx}",
                        value=False,
                    )
                    if checked:
                        mark_task_done(
                            email, week_num, idx,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        if len(week_done) + 1 == len(week_data["tasks"]):
                            st.session_state["celebrate"] = "tasks"
                            st.session_state["celebrate_week"] = week_num
                        else:
                            st.session_state["celebrate"] = "task_single"
                        st.rerun()

            st.divider()

            # ── Reflection ────────────────────────────────────
            all_tasks_done = len(week_done) == len(week_data["tasks"])
            reflection     = get_reflection_cached(email, week_num)

            if not all_tasks_done:
                remaining = len(week_data["tasks"]) - len(week_done)
                st.markdown(f"""
<div class="alert-info">
  ✏️ Complete <strong>{remaining} more task{"s" if remaining > 1 else ""}</strong>
  to unlock this unit's reflection.
</div>""", unsafe_allow_html=True)

            elif reflection:
                st.markdown(f"""
<div class="alert-success">
  ✅ {unit_label} {week_num} complete — great work, {first_name}!
</div>""", unsafe_allow_html=True)

                with st.expander("📝 Your reflection"):
                    st.markdown(
                        f'<div style="color:#8BA0B8;font-size:0.88rem;line-height:1.65;">'
                        f'{reflection.get("response","")}</div>',
                        unsafe_allow_html=True
                    )

                fb = get_feedback(email, week_num)
                if fb:
                    section_label("Feedback from Abdul", color="var(--gold)")
                    feedback_box(fb)

            else:
                prompt = get_prompt(week_num)
                if prompt:
                    section_label("Weekly reflection", color="var(--gold)")
                    reflection_box(prompt)
                    response = st.text_area(
                        "Your response",
                        placeholder="Write your reflection here — be honest, specific, and thoughtful...",
                        key=f"reflection_input_{week_num}",
                        height=140,
                    )
                    if st.button("Submit reflection →",
                                 key=f"submit_ref_{week_num}", type="primary"):
                        if response.strip():
                            submit_reflection(
                                email, week_num, response.strip(),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            st.session_state["celebrate"] = "reflection"
                            st.session_state["celebrate_week"] = week_num
                            st.rerun()
                        else:
                            st.warning("Please write something before submitting.")
                else:
                    st.markdown("""
<div class="alert-success">
  ✅ All tasks done! Your reflection prompt will appear here shortly.
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── Footer actions ────────────────────────────────────────
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Refresh progress", use_container_width=True, type="secondary"):
            st.session_state.pop("progress", None)
            st.rerun()
    with col_r2:
        if st.button("🔄 Check for new weeks", use_container_width=True, type="secondary"):
            st.session_state.pop("active_week", None)
            st.session_state.pop("active_week_last_check", None)
            st.rerun()
