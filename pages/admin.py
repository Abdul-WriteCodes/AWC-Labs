import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth import login_admin, is_admin, logout
from utils.sheets import (
    get_all_participants, get_all_progress, get_active_week, set_active_week,
    get_prompt, set_prompt, get_all_reflections, get_all_feedback, save_feedback,
)
from data.content import PROGRAM_WEEKS
from config import TOTAL_WEEKS


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

    tab_overview, tab_participants, tab_engagement, tab_prompts, tab_reflections, tab_control = st.tabs([
        "Overview", "Participants", "Engagement", "Prompts", "Reflections", "Cohort control"
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
