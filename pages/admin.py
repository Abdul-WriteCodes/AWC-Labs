import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth import login_admin, is_admin, logout
from utils.sheets import (
    get_all_participants, get_all_progress, get_active_week, set_active_week,
    get_prompt, set_prompt, get_all_reflections, get_all_feedback, save_feedback,
    get_all_programs, create_program, delete_program,
    get_program_weeks, save_program_week, delete_week_from_program,
    get_active_program_id, set_active_program, get_active_unit_label,
    wipe_all_progress,
)
from config import PROGRAM_NAME
import uuid


def show():
    if not is_admin():
        _admin_login()
        return

    st.markdown("## Admin panel")
    st.caption("Crea8it — Program Management")

    if st.button("Log out"):
        logout()
        st.rerun()

    st.divider()

    # Resolve active program
    active_pid   = get_active_program_id()
    unit_label   = get_active_unit_label() or "Week"
    all_programs = get_all_programs()
    prog_map     = {p["program_id"]: p for p in all_programs}
    active_prog  = prog_map.get(active_pid)
    PROGRAM_WEEKS = get_program_weeks(active_pid) if active_pid else {}
    TOTAL_UNITS   = len(PROGRAM_WEEKS)

    tab_programs, tab_overview, tab_participants, tab_engagement, tab_prompts, tab_reflections, tab_content, tab_control = st.tabs([
        "🗂 Programs", "Overview", "Participants", "Engagement", "Prompts", "Reflections", "📚 Content", "Cohort control"
    ])

    # ── Programs ──────────────────────────────────────────────
    with tab_programs:
        st.markdown("### Programs")
        st.caption("Create programs, set one as active, delete old ones.")

        # Active program banner
        if active_prog:
            st.success(f"**Active program:** {active_prog['name']}  ·  unit: **{active_prog['unit_label']}**")
        else:
            st.warning("No active program set. Create one below and activate it.")

        st.divider()

        # ── Create new program ────────────────────────────────
        with st.expander("➕ Create new program", expanded=not all_programs):
            p_name  = st.text_input("Program name", placeholder="e.g. Crea8it AI Career Launch", key="new_prog_name")
            p_unit  = st.text_input("Unit label", placeholder="Week / Day / Module / Session / Sprint",
                                    value="Week", key="new_prog_unit")
            if st.button("Create program", key="create_prog", type="primary"):
                if not p_name.strip():
                    st.warning("Program name is required.")
                elif not p_unit.strip():
                    st.warning("Unit label is required.")
                else:
                    new_id = str(uuid.uuid4())[:8]
                    create_program(new_id, p_name.strip(), p_unit.strip(),
                                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.success(f"✅ Program '{p_name.strip()}' created (ID: {new_id})")
                    st.rerun()

        st.divider()

        # ── Existing programs ─────────────────────────────────
        if not all_programs:
            st.info("No programs yet. Create one above.")
        else:
            for prog in all_programs:
                pid   = prog["program_id"]
                pname = prog["name"]
                punit = prog["unit_label"]
                is_active = pid == active_pid

                col_info, col_activate, col_delete = st.columns([4, 2, 1])
                with col_info:
                    badge = "🟢 **ACTIVE**  " if is_active else ""
                    st.markdown(f"{badge}**{pname}**  ·  unit: *{punit}*  ·  `{pid}`")
                with col_activate:
                    if not is_active:
                        if st.button(f"Set active", key=f"activate_{pid}", type="primary"):
                            set_active_program(pid, punit)
                            get_active_program_id.clear()
                            get_active_unit_label.clear()
                            st.success(f"✅ '{pname}' is now active.")
                            st.rerun()
                with col_delete:
                    if st.button("🗑️", key=f"del_prog_{pid}"):
                        st.session_state[f"confirm_del_prog_{pid}"] = True
                    if st.session_state.get(f"confirm_del_prog_{pid}"):
                        st.warning(f"Delete **{pname}**? This removes all its content permanently.")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Yes, delete", key=f"confirm_del_prog_yes_{pid}", type="primary"):
                                delete_program(pid)
                                st.session_state.pop(f"confirm_del_prog_{pid}", None)
                                st.success(f"Program '{pname}' deleted.")
                                st.rerun()
                        with c2:
                            if st.button("Cancel", key=f"confirm_del_prog_no_{pid}"):
                                st.session_state.pop(f"confirm_del_prog_{pid}", None)
                                st.rerun()
                st.divider()

    # ── Overview ──────────────────────────────────────────────
    with tab_overview:
        if not active_prog:
            st.info("No active program. Set one in the Programs tab.")
        else:
            participants = get_all_participants()
            active_week  = get_active_week()
            total = len(participants)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total registered", total)
            col2.metric("Students", sum(1 for p in participants if p.get("cohort_type") == "Student"))
            col3.metric("Graduates", sum(1 for p in participants if p.get("cohort_type") == "Graduate / Job seeker"))
            col4.metric("Pivoters", sum(1 for p in participants if p.get("cohort_type") == "Career pivoter"))
            st.markdown("")
            week_title = PROGRAM_WEEKS.get(active_week, {}).get("title", "—")
            st.metric("Active unit", f"{unit_label} {active_week} — {week_title}")
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
        st.markdown("### Task completion by unit")
        progress     = get_all_progress()
        participants = get_all_participants()
        if progress and participants and PROGRAM_WEEKS:
            rows = []
            for p in participants:
                row = {"Participant": p["full_name"]}
                for w in sorted(PROGRAM_WEEKS.keys()):
                    done  = sum(1 for r in progress if r.get("email") == p["email"] and int(r.get("week", 0)) == w)
                    total = len(PROGRAM_WEEKS[w]["tasks"])
                    row[f"{unit_label} {w}"] = f"{done}/{total}"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("No progress data yet.")

    # ── Prompts ───────────────────────────────────────────────
    with tab_prompts:
        st.markdown("### Reflection prompts")
        st.caption("Write the question participants must answer after completing each unit's tasks.")
        if not PROGRAM_WEEKS:
            st.info("No content yet. Add units in the Content tab.")
        else:
            for w in sorted(PROGRAM_WEEKS.keys()):
                with st.expander(f"{unit_label} {w} — {PROGRAM_WEEKS[w]['title']}", expanded=False):
                    current = get_prompt(w)
                    new_prompt = st.text_area("Reflection prompt", value=current,
                                              placeholder="e.g. What was your biggest insight?",
                                              key=f"prompt_input_{w}", height=100)
                    if st.button("Save prompt", key=f"save_prompt_{w}", type="primary"):
                        if new_prompt.strip():
                            set_prompt(w, new_prompt.strip())
                            st.success(f"✅ {unit_label} {w} prompt saved.")
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
            feedback_lookup = {
                (str(r.get("email", "")).strip().lower(), int(r.get("week", 0))): r.get("feedback", "")
                for r in feedback_all
            }
            participant_map = {p["email"].strip().lower(): p["full_name"] for p in participants}
            sorted_refs = sorted(reflections, key=lambda r: (int(r.get("week", 0)), r.get("email", "")))

            for ref in sorted_refs:
                ref_email = str(ref.get("email", "")).strip().lower()
                ref_week  = int(ref.get("week", 0))
                name      = participant_map.get(ref_email, ref_email)
                existing_feedback = feedback_lookup.get((ref_email, ref_week), "")
                label = f"{unit_label} {ref_week} · {name}" + (" ✓" if existing_feedback else "")

                with st.expander(label, expanded=False):
                    st.markdown(f"**Submitted:** {ref.get('submitted_at', '—')}")
                    st.markdown("**Their reflection:**")
                    st.info(ref.get("response", ""))
                    st.markdown("**Your feedback:**")
                    feedback_input = st.text_area("Write feedback", value=existing_feedback,
                                                  placeholder="Write your personal feedback...",
                                                  key=f"feedback_{ref_email}_{ref_week}",
                                                  height=120, label_visibility="collapsed")
                    if st.button("Save feedback", key=f"save_feedback_{ref_email}_{ref_week}", type="primary"):
                        if feedback_input.strip():
                            save_feedback(ref_email, ref_week, feedback_input.strip(),
                                          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            get_all_feedback.clear()
                            st.success("✅ Feedback saved.")
                            st.rerun()
                        else:
                            st.warning("Feedback cannot be empty.")

    # ── Program Content ───────────────────────────────────────
    with tab_content:
        st.markdown("### Program content")
        if not active_prog:
            st.info("No active program. Go to the Programs tab to create and activate one first.")
        else:
            st.caption(f"Editing: **{active_prog['name']}**  ·  unit label: **{unit_label}**")

            MATERIAL_TYPES = ["book", "video", "article", "worksheet", "template"]

            # ── Add new unit ──────────────────────────────────
            with st.expander(f"➕ Add a new {unit_label}", expanded=not PROGRAM_WEEKS):
                existing_nums   = sorted(PROGRAM_WEEKS.keys())
                suggested_num   = max(existing_nums) + 1 if existing_nums else 1

                new_num   = st.number_input(f"{unit_label} number", min_value=1, max_value=365,
                                            value=suggested_num, key="new_unit_num")
                new_title = st.text_input("Title", placeholder=f"e.g. {unit_label} 1: Getting Started",
                                          key="new_unit_title")
                new_theme = st.text_input("Subtitle / theme",
                                          placeholder="e.g. Understand the landscape and why it matters",
                                          key="new_unit_theme")

                st.markdown("**Materials** (up to 8)")
                mat_count = st.number_input("How many materials?", min_value=0, max_value=8,
                                            value=3, key="new_mat_count")
                new_mats = []
                for m in range(int(mat_count)):
                    mc1, mc2 = st.columns([3, 1])
                    with mc1:
                        lbl = st.text_input(f"Material {m+1}", placeholder="e.g. Watch: Intro video",
                                            key=f"new_mat_lbl_{m}")
                    with mc2:
                        mtp = st.selectbox("Type", MATERIAL_TYPES, key=f"new_mat_type_{m}")
                    if lbl.strip():
                        new_mats.append({"label": lbl.strip(), "type": mtp})

                st.markdown("**Activities / Tasks** (up to 10)")
                task_count = st.number_input("How many tasks?", min_value=0, max_value=10,
                                             value=3, key="new_task_count")
                new_tasks = []
                for t in range(int(task_count)):
                    tv = st.text_input(f"Task {t+1}", placeholder="e.g. Complete the worksheet",
                                       key=f"new_task_{t}")
                    if tv.strip():
                        new_tasks.append(tv.strip())

                if st.button(f"Save {unit_label}", key="save_new_unit", type="primary"):
                    if not new_title.strip():
                        st.warning("Title is required.")
                    elif not new_tasks:
                        st.warning("Add at least one task.")
                    else:
                        save_program_week(active_pid, int(new_num), new_title.strip(),
                                          new_theme.strip(), new_mats, new_tasks)
                        st.success(f"✅ {unit_label} {new_num} saved.")
                        st.rerun()

            st.divider()

            # ── Edit / delete existing units ──────────────────
            if not PROGRAM_WEEKS:
                st.info(f"No {unit_label.lower()}s yet. Add one above.")
            else:
                for w in sorted(PROGRAM_WEEKS.keys()):
                    wdata = PROGRAM_WEEKS[w]
                    with st.expander(f"{unit_label} {w} — {wdata.get('title','(untitled)')}", expanded=False):
                        e_title = st.text_input("Title", value=wdata.get("title",""), key=f"e_title_{w}")
                        e_theme = st.text_input("Subtitle", value=wdata.get("theme",""), key=f"e_theme_{w}")

                        st.markdown("**Materials**")
                        ex_mats = wdata.get("materials", [])
                        e_mat_n = st.number_input("Number of materials", min_value=0, max_value=8,
                                                  value=len(ex_mats), key=f"e_mat_n_{w}")
                        e_mats = []
                        for m in range(int(e_mat_n)):
                            dl = ex_mats[m]["label"] if m < len(ex_mats) else ""
                            dt = ex_mats[m]["type"]  if m < len(ex_mats) else "article"
                            mc1, mc2 = st.columns([3, 1])
                            with mc1:
                                ml = st.text_input(f"Material {m+1}", value=dl, key=f"e_mat_lbl_{w}_{m}")
                            with mc2:
                                idx = MATERIAL_TYPES.index(dt) if dt in MATERIAL_TYPES else 0
                                mt = st.selectbox("Type", MATERIAL_TYPES, index=idx, key=f"e_mat_tp_{w}_{m}")
                            if ml.strip():
                                e_mats.append({"label": ml.strip(), "type": mt})

                        st.markdown("**Tasks**")
                        ex_tasks = wdata.get("tasks", [])
                        e_task_n = st.number_input("Number of tasks", min_value=0, max_value=10,
                                                   value=len(ex_tasks), key=f"e_task_n_{w}")
                        e_tasks = []
                        for t in range(int(e_task_n)):
                            dv = ex_tasks[t] if t < len(ex_tasks) else ""
                            tv = st.text_input(f"Task {t+1}", value=dv, key=f"e_task_{w}_{t}")
                            if tv.strip():
                                e_tasks.append(tv.strip())

                        col_save, col_del = st.columns([3, 1])
                        with col_save:
                            if st.button(f"💾 Save {unit_label} {w}", key=f"save_unit_{w}", type="primary"):
                                if not e_title.strip():
                                    st.warning("Title required.")
                                elif not e_tasks:
                                    st.warning("At least one task required.")
                                else:
                                    save_program_week(active_pid, w, e_title.strip(), e_theme.strip(),
                                                      e_mats, e_tasks)
                                    st.success(f"✅ {unit_label} {w} updated.")
                                    st.rerun()
                        with col_del:
                            if st.button("🗑️ Delete", key=f"del_unit_{w}"):
                                st.session_state[f"confirm_del_unit_{w}"] = True
                            if st.session_state.get(f"confirm_del_unit_{w}"):
                                st.warning(f"Delete {unit_label} {w}?")
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button("Yes", key=f"del_unit_yes_{w}", type="primary"):
                                        delete_week_from_program(active_pid, w)
                                        st.session_state.pop(f"confirm_del_unit_{w}", None)
                                        st.success(f"{unit_label} {w} deleted.")
                                        st.rerun()
                                with c2:
                                    if st.button("Cancel", key=f"del_unit_no_{w}"):
                                        st.session_state.pop(f"confirm_del_unit_{w}", None)
                                        st.rerun()

    # ── Cohort control ────────────────────────────────────────
    with tab_control:
        if not active_prog:
            st.info("No active program. Set one in the Programs tab.")
        else:
            st.markdown(f"### Unlock the next {unit_label.lower()}")
            active_week = get_active_week()
            cur_title   = PROGRAM_WEEKS.get(active_week, {}).get("title", "—")
            st.info(f"Program: **{active_prog['name']}**  ·  Currently active: **{unit_label} {active_week} — {cur_title}**")

            if PROGRAM_WEEKS:
                new_week = st.selectbox(
                    f"Set active {unit_label.lower()}",
                    options=sorted(PROGRAM_WEEKS.keys()),
                    index=list(sorted(PROGRAM_WEEKS.keys())).index(active_week)
                          if active_week in PROGRAM_WEEKS else 0,
                    format_func=lambda w: f"{unit_label} {w} — {PROGRAM_WEEKS[w]['title']}"
                )
                if st.button(f"Update active {unit_label.lower()}", type="primary"):
                    try:
                        set_active_week(new_week)
                        st.session_state.pop("active_week", None)
                        st.session_state.pop("active_week_last_check", None)
                        st.success(f"✅ {unit_label} {new_week} is now live for all participants.")
                        import time as _time; _time.sleep(0.8)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update: {e}")
            else:
                st.warning(f"No {unit_label.lower()}s defined yet. Add content first.")

            st.divider()

            # ── Export + wipe progress ────────────────────────
            st.markdown("### Switch program — export & wipe progress")
            st.caption("Export participant progress before switching to a new program, then wipe.")
            progress = get_all_progress()
            if progress:
                df_prog = pd.DataFrame(progress)
                st.download_button(
                    "⬇️ Export progress as CSV",
                    df_prog.to_csv(index=False).encode("utf-8"),
                    f"progress_{active_pid}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                )
                st.markdown("")
                if st.button("🗑️ Wipe all progress", type="secondary"):
                    st.session_state["confirm_wipe"] = True
                if st.session_state.get("confirm_wipe"):
                    st.warning("This deletes ALL participant progress permanently. Export first!")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes, wipe progress", type="primary"):
                            wipe_all_progress()
                            st.session_state.pop("confirm_wipe", None)
                            st.success("✅ Progress wiped. Ready for new program.")
                            st.rerun()
                    with c2:
                        if st.button("Cancel"):
                            st.session_state.pop("confirm_wipe", None)
                            st.rerun()
            else:
                st.info("No progress data to export.")


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
