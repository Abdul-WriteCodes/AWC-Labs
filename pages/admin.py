import streamlit as st
import pandas as pd
from utils.auth import login_admin, is_admin, logout
from utils.sheets import get_all_participants, get_all_progress, get_active_week, set_active_week
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

    with tab_participants:
        st.markdown("### All registered participants")
        participants = get_all_participants()
        if participants:
            df = pd.DataFrame(participants)
            st.dataframe(df, use_container_width=True)
            st.download_button("Export as CSV", df.to_csv(index=False).encode("utf-8"), "participants.csv", "text/csv")
        else:
            st.info("No participants registered yet.")

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
                st.success(f"✅ Week {new_week} is now live for all participants.")
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
