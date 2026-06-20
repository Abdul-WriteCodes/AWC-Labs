import streamlit as st
import pandas as pd
from utils.auth import login_admin, is_admin, logout
from utils.sheets import (
    get_all_participants, get_all_progress,
    get_active_week, set_active_week
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

    tab_overview, tab_participants, tab_engagement, tab_control = st.tabs([
        "Overview", "Participants", "Engagement", "Cohort control"
    ])

    # ── Overview ──────────────────────────────────────────────
    with tab_overview:
        participants = get_all_participants()
        progress     = get_all_progress()
        active_week  = get_active_week()

        total = len(participants)
        students   = sum(1 for p in participants if p.get("cohort_type") == "Student")
        graduates  = sum(1 for p in participants if p.get("cohort_type") == "Graduate / Job seeker")
        pivoters   = sum(1 for p in participants if p.get("cohort_type") == "Career pivoter")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total registered", total)
        col2.metric("Students", students)
        col3.metric("Graduates / Job seekers", graduates)
        col4.metric("Career pivoters", pivoters)

        st.markdown("")
        st.metric("Active week", f"Week {active_week} — {PROGRAM_WEEKS[active_week]['title']}")

        # Revenue estimate
        st.markdown("")
        st.info(f"💰 Estimated book revenue: **₦{total * 5000:,}** ({total} × ₦5,000)")

    # ── Participants ──────────────────────────────────────────
    with tab_participants:
        st.markdown("### All registered participants")
        participants = get_all_participants()
        if participants:
            df = pd.DataFrame(participants)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Export as CSV", csv, "participants.csv", "text/csv")
        else:
            st.info("No participants registered yet.")

    # ── Engagement ────────────────────────────────────────────
    with tab_engagement:
        st.markdown("### Task completion by week")
        progress    = get_all_progress()
        participants = get_all_participants()

        if progress and participants:
            emails = [p["email"] for p in participants]
            rows   = []
            for email in emails:
                name = next((p["full_name"] for p in participants if p["email"] == email), email)
                row  = {"Participant": name}
                for w in range(1, TOTAL_WEEKS + 1):
                    done  = sum(1 for r in progress if r.get("email") == email and int(r.get("week", 0)) == w)
                    total = len(PROGRAM_WEEKS[w]["tasks"])
                    row[f"Wk {w}"] = f"{done}/{total}"
                rows.append(row)

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No progress data yet.")

    # ── Cohort control ────────────────────────────────────────
    with tab_control:
        st.markdown("### Unlock the next week")
        active_week = get_active_week()
        st.info(f"Currently active: **Week {active_week} — {PROGRAM_WEEKS[active_week]['title']}**")

        st.markdown("Move all participants to the next week when you're ready:")
        new_week = st.selectbox(
            "Set active week",
            options=list(range(1, TOTAL_WEEKS + 1)),
            index=active_week - 1,
            format_func=lambda w: f"Week {w} — {PROGRAM_WEEKS[w]['title']}"
        )

        if st.button("Update active week", type="primary"):
            set_active_week(new_week)
            st.success(f"Week {new_week} is now live for all participants.")
            st.rerun()


def _admin_login():
    st.markdown("## Admin login")
    with st.form("admin_login"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in →")
    if submitted:
        if login_admin(password):
            st.rerun()
        else:
            st.error("Incorrect password.")
