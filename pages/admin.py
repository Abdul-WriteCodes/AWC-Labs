import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth import login_admin, is_admin, logout
from utils.sheets import (
    get_all_participants, get_all_progress, get_active_week, set_active_week,
    get_prompt, set_prompt, get_all_reflections, get_all_feedback, save_feedback,
    get_program_weeks_from_sheet, save_program_week, delete_program_week,
    get_total_weeks_from_sheet, ensure_program_content_sheet,
)
from data.content import PROGRAM_WEEKS as PROGRAM_WEEKS_STATIC


def _get_program_weeks():
    """Return sheet-based weeks if any exist, else fall back to static content."""
    live = get_program_weeks_from_sheet()
    return live if live else PROGRAM_WEEKS_STATIC


def show():
    if not is_admin():
        _admin_login()
        return

    st.markdown("## Admin panel")
    st.caption("Crea8it AI Career Launch Program")

    if st.button("Log out"):
        logout()
        st.rerun()

    st.divider()

    PROGRAM_WEEKS = _get_program_weeks()
    TOTAL_WEEKS   = len(PROGRAM_WEEKS)

    tab_overview, tab_participants, tab_engagement, tab_prompts, tab_reflections, tab_content, tab_control = st.tabs([
        "Overview", "Participants", "Engagement", "Prompts", "Reflections", "📚 Program content", "Cohort control"
    ])

    # ── Overview ──────────────────────────────────────────────
    with tab_overview:
        participants = get_all_participants()
        active_week  = get_active_week()
        total = len(participants)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total registered", total)
        col2.metric("Students", sum(1 for p in participants if p.get("cohort_type") == "Student"))
        col3.metric("Graduates", sum(1 for p in participants if p.get("cohort_type") == "Graduate / Job seeker"))
        col4.metric("Pivoters", sum(1 for p in participants if p.get("cohort_type") == "Career pivoter"))
        st.markdown("")
        st.metric("Active week", f"Week {active_week} — {PROGRAM_WEEKS[active_week]['title']}")
        st.info(f"💰 Estimated book revenue: **₦{total * 5000:,}** ({total} × ₦5,000)")

    # ── Participants ──────────────────────────────────────────
    with tab_participants:
        st.markdown("### All registered participants")
        participants = get_all_participants()
        if participants:
            df = pd.DataFrame(participants)
            st.dataframe(df, use_container_width=True)
            st.download_button("Export as CSV", df.to_csv(index=False).encode("utf-8"), "participants.csv", "text/csv")
        else:
            st.info("No participants registered yet.")

    # ── Engagement ────────────────────────────────────────────
    with tab_engagement:
        st.markdown("### Task completion by week")
        progress     = get_all_progress()
        participants = get_all_participants()
        if progress and participants:
            rows = []
            for p in participants:
                row = {"Participant": p["full_name"]}
                for w in range(1, TOTAL_WEEKS + 1):
                    done  = sum(1 for r in progress if r.get("email") == p["email"] and int(r.get("week", 0)) == w)
                    total = len(PROGRAM_WEEKS[w]["tasks"])
                    row[f"Wk {w}"] = f"{done}/{total}"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("No progress data yet.")

    # ── Prompts ───────────────────────────────────────────────
    with tab_prompts:
        st.markdown("### Weekly reflection prompts")
        st.caption("Write the question participants must answer after completing each week's tasks.")

        for w in range(1, TOTAL_WEEKS + 1):
            with st.expander(f"Week {w} — {PROGRAM_WEEKS[w]['title']}", expanded=False):
                current = get_prompt(w)
                new_prompt = st.text_area(
                    "Reflection prompt",
                    value=current,
                    placeholder="e.g. What was your biggest insight from this week's reading?",
                    key=f"prompt_input_{w}",
                    height=100,
                )
                if st.button("Save prompt", key=f"save_prompt_{w}", type="primary"):
                    if new_prompt.strip():
                        set_prompt(w, new_prompt.strip())
                        st.success(f"✅ Week {w} prompt saved.")
                    else:
                        st.warning("Prompt cannot be empty.")

    # ── Reflections ───────────────────────────────────────────
    with tab_reflections:
        st.markdown("### Participant reflections & feedback")
        reflections  = get_all_reflections()
        feedback_all = get_all_feedback()
        participants = get_all_participants()

        if not reflections:
            st.info("No reflections submitted yet.")
        else:
            # Build lookup for existing feedback
            feedback_lookup = {
                (str(r.get("email", "")).strip().lower(), int(r.get("week", 0))): r.get("feedback", "")
                for r in feedback_all
            }

            # Group by participant
            participant_map = {p["email"].strip().lower(): p["full_name"] for p in participants}

            # Sort reflections by week then name
            sorted_refs = sorted(reflections, key=lambda r: (int(r.get("week", 0)), r.get("email", "")))

            for ref in sorted_refs:
                ref_email = str(ref.get("email", "")).strip().lower()
                ref_week  = int(ref.get("week", 0))
                name      = participant_map.get(ref_email, ref_email)
                existing_feedback = feedback_lookup.get((ref_email, ref_week), "")

                label = f"Week {ref_week} · {name}"
                if existing_feedback:
                    label += " ✓"

                with st.expander(label, expanded=False):
                    st.markdown(f"**Submitted:** {ref.get('submitted_at', '—')}")
                    st.markdown("**Their reflection:**")
                    st.info(ref.get("response", ""))

                    st.markdown("**Your feedback:**")
                    feedback_input = st.text_area(
                        "Write feedback",
                        value=existing_feedback,
                        placeholder="Write your personal feedback to this participant...",
                        key=f"feedback_{ref_email}_{ref_week}",
                        height=120,
                        label_visibility="collapsed",
                    )
                    if st.button("Save feedback", key=f"save_feedback_{ref_email}_{ref_week}", type="primary"):
                        if feedback_input.strip():
                            save_feedback(
                                ref_email, ref_week, feedback_input.strip(),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            get_all_feedback.clear()
                            st.success("✅ Feedback saved.")
                            st.rerun()
                        else:
                            st.warning("Feedback cannot be empty.")

    # ── Program Content ───────────────────────────────────────
    with tab_content:
        st.markdown("### Program content")
        st.caption("Add, edit, or delete weeks and their activities. Changes go live immediately.")

        ensure_program_content_sheet()

        MATERIAL_TYPES = ["book", "video", "article", "worksheet", "template"]

        # ── Create / edit a week ──────────────────────────────
        with st.expander("➕ Add a new week", expanded=False):
            existing_week_nums = sorted(PROGRAM_WEEKS.keys())
            suggested_week = max(existing_week_nums) + 1 if existing_week_nums else 1

            new_week_num = st.number_input("Week number", min_value=1, max_value=52,
                                           value=suggested_week, key="new_week_num")
            new_title    = st.text_input("Week title", placeholder="e.g. AI Orientation", key="new_title")
            new_theme    = st.text_input("Week theme / subtitle",
                                         placeholder="e.g. Understand the AI landscape and why it matters now",
                                         key="new_theme")

            st.markdown("**Materials** (add up to 8)")
            mat_count = st.number_input("How many materials?", min_value=0, max_value=8,
                                        value=3, key="new_mat_count")
            new_materials = []
            for m in range(int(mat_count)):
                mc1, mc2 = st.columns([3, 1])
                with mc1:
                    label = st.text_input(f"Material {m+1} label",
                                          placeholder="e.g. Read Enter AI — Chapters 1 & 2",
                                          key=f"new_mat_label_{m}")
                with mc2:
                    mtype = st.selectbox("Type", MATERIAL_TYPES, key=f"new_mat_type_{m}")
                if label.strip():
                    new_materials.append({"label": label.strip(), "type": mtype})

            st.markdown("**Activities / Tasks** (add up to 10)")
            task_count = st.number_input("How many tasks?", min_value=0, max_value=10,
                                         value=3, key="new_task_count")
            new_tasks = []
            for t in range(int(task_count)):
                task = st.text_input(f"Task {t+1}",
                                     placeholder="e.g. List 3 AI tools you've heard of",
                                     key=f"new_task_{t}")
                if task.strip():
                    new_tasks.append(task.strip())

            if st.button("Save week", key="save_new_week", type="primary"):
                if not new_title.strip():
                    st.warning("Week title is required.")
                elif not new_tasks:
                    st.warning("Add at least one task.")
                else:
                    save_program_week(int(new_week_num), new_title.strip(),
                                      new_theme.strip(), new_materials, new_tasks)
                    st.success(f"✅ Week {new_week_num} saved.")
                    st.rerun()

        st.divider()

        # ── Edit / delete existing weeks ──────────────────────
        if not PROGRAM_WEEKS:
            st.info("No weeks defined yet. Add your first week above.")
        else:
            for week_num in sorted(PROGRAM_WEEKS.keys()):
                wdata = PROGRAM_WEEKS[week_num]
                with st.expander(f"Week {week_num} — {wdata.get('title','(untitled)')}", expanded=False):

                    e_title = st.text_input("Title", value=wdata.get("title",""),
                                            key=f"edit_title_{week_num}")
                    e_theme = st.text_input("Theme / subtitle", value=wdata.get("theme",""),
                                            key=f"edit_theme_{week_num}")

                    st.markdown("**Materials**")
                    existing_mats = wdata.get("materials", [])
                    e_mat_count   = st.number_input("Number of materials", min_value=0, max_value=8,
                                                    value=len(existing_mats),
                                                    key=f"edit_mat_count_{week_num}")
                    e_materials = []
                    for m in range(int(e_mat_count)):
                        default_label = existing_mats[m]["label"] if m < len(existing_mats) else ""
                        default_type  = existing_mats[m]["type"]  if m < len(existing_mats) else "article"
                        mc1, mc2 = st.columns([3, 1])
                        with mc1:
                            ml = st.text_input(f"Material {m+1}", value=default_label,
                                               key=f"edit_mat_label_{week_num}_{m}")
                        with mc2:
                            idx = MATERIAL_TYPES.index(default_type) if default_type in MATERIAL_TYPES else 0
                            mt = st.selectbox("Type", MATERIAL_TYPES, index=idx,
                                              key=f"edit_mat_type_{week_num}_{m}")
                        if ml.strip():
                            e_materials.append({"label": ml.strip(), "type": mt})

                    st.markdown("**Tasks / Activities**")
                    existing_tasks = wdata.get("tasks", [])
                    e_task_count   = st.number_input("Number of tasks", min_value=0, max_value=10,
                                                     value=len(existing_tasks),
                                                     key=f"edit_task_count_{week_num}")
                    e_tasks = []
                    for t in range(int(e_task_count)):
                        default_task = existing_tasks[t] if t < len(existing_tasks) else ""
                        task_val = st.text_input(f"Task {t+1}", value=default_task,
                                                 key=f"edit_task_{week_num}_{t}")
                        if task_val.strip():
                            e_tasks.append(task_val.strip())

                    col_save, col_del = st.columns([3, 1])
                    with col_save:
                        if st.button(f"💾 Save Week {week_num}", key=f"save_week_{week_num}", type="primary"):
                            if not e_title.strip():
                                st.warning("Title required.")
                            elif not e_tasks:
                                st.warning("At least one task required.")
                            else:
                                save_program_week(week_num, e_title.strip(), e_theme.strip(),
                                                  e_materials, e_tasks)
                                st.success(f"✅ Week {week_num} updated.")
                                st.rerun()
                    with col_del:
                        confirm_key = f"confirm_del_{week_num}"
                        if st.button(f"🗑️ Delete", key=f"del_week_{week_num}", type="secondary"):
                            st.session_state[confirm_key] = True
                        if st.session_state.get(confirm_key):
                            st.warning(f"Delete Week {week_num}? This cannot be undone.")
                            if st.button("Yes, delete", key=f"confirm_del_yes_{week_num}", type="primary"):
                                delete_program_week(week_num)
                                st.session_state.pop(confirm_key, None)
                                st.success(f"Week {week_num} deleted.")
                                st.rerun()
                            if st.button("Cancel", key=f"confirm_del_no_{week_num}"):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()

    # ── Cohort control ────────────────────────────────────────
    with tab_control:
        st.markdown("### Unlock the next week")
        active_week = get_active_week()
        st.info(f"Currently active: **Week {active_week} — {PROGRAM_WEEKS[active_week]['title']}**")

        new_week = st.selectbox(
            "Set active week",
            options=list(range(1, TOTAL_WEEKS + 1)),
            index=active_week - 1,
            format_func=lambda w: f"Week {w} — {PROGRAM_WEEKS[w]['title']}"
        )

        if st.button("Update active week", type="primary"):
            try:
                set_active_week(new_week)
                st.session_state.pop("active_week", None)
                st.session_state.pop("active_week_last_check", None)
                st.success(f"✅ Week {new_week} is now live for all participants.")
                import time as _time
                _time.sleep(0.8)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update: {e}")


def _admin_login():
    st.markdown("## Admin login")
    with st.form("admin_login"):
        password  = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in →")
    if submitted:
        if login_admin(password):
            st.rerun()
        else:
            st.error("Incorrect password.")
