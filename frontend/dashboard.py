"""Streamlit dashboard for CareerPilot.

Run with: streamlit run frontend/dashboard.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

from backend.agents import interview, planner, skill_gap, tracker
from backend.db import Application, get_session, init_db

load_dotenv()
init_db()

st.set_page_config(page_title="CareerPilot", layout="wide")
st.title("CareerPilot")

tab_tasks, tab_applications, tab_skills, tab_interview = st.tabs(
    ["Tasks", "Applications", "Skill Gap", "Mock Interview"]
)

with tab_tasks:
    st.subheader("Today's tasks")
    with st.form("add_task"):
        title = st.text_input("Task")
        due_date = st.text_input("Due date (optional, YYYY-MM-DD)")
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        if st.form_submit_button("Add") and title:
            planner.add_manual_task(title, due_date or None, priority)
            st.rerun()

    uploaded = st.file_uploader("Or upload a syllabus PDF", type="pdf")
    if uploaded and st.button("Extract tasks from PDF"):
        tmp_path = Path("data") / uploaded.name
        tmp_path.write_bytes(uploaded.getvalue())
        tasks = planner.extract_tasks_from_pdf(str(tmp_path))
        planner.save_tasks(tasks, source="pdf")
        st.success(f"Added {len(tasks)} tasks from {uploaded.name}")
        st.rerun()

    for task in planner.todays_tasks():
        st.checkbox(
            f"{task.title}" + (f" — due {task.due_date}" if task.due_date else "") + f" ({task.priority})",
            value=task.done,
            key=f"task-{task.id}",
        )

with tab_applications:
    st.subheader("Application board")
    if st.button("Sync from Gmail"):
        try:
            updated = tracker.sync_applications()
            st.success(f"Synced {len(updated)} applications")
        except Exception as exc:  # missing/invalid Gmail credentials, etc.
            st.error(f"Gmail sync failed: {exc}")

    session = get_session()
    apps = session.query(Application).all()
    session.close()

    columns = st.columns(4)
    for col, status in zip(columns, ["applied", "interview", "offer", "rejected"]):
        with col:
            st.markdown(f"**{status.title()}**")
            for app in apps:
                if app.status == status:
                    st.write(f"{app.company} — {app.role}")

    st.markdown("---")
    st.text(tracker.daily_digest())

with tab_skills:
    st.subheader("Skill gap analysis")
    resume_text = st.text_area("Paste your resume text")
    if st.button("Index resume") and resume_text:
        n = skill_gap.index_resume(resume_text)
        st.success(f"Indexed {n} resume chunks")

    job_text = st.text_area("Paste a target job posting")
    if st.button("Find gaps") and job_text:
        report = skill_gap.find_skill_gaps(job_text)
        for item in report.items:
            if item.covered:
                st.success(f"{item.requirement} — {item.evidence}")
            else:
                st.warning(f"{item.requirement} — try: {item.suggestion}")

with tab_interview:
    st.subheader("Mock interview")
    if "interview_session_id" not in st.session_state:
        role = st.text_input("Role to practice for", key="interview_role")
        if st.button("Start interview") and role:
            session_id, question = interview.start_session(role)
            st.session_state["interview_session_id"] = session_id
            st.session_state["interview_question"] = question
    else:
        st.write(st.session_state["interview_question"])
        answer = st.text_area("Your answer")
        col1, col2 = st.columns(2)
        if col1.button("Submit answer") and answer:
            question = interview.submit_answer(st.session_state["interview_session_id"], answer)
            st.session_state["interview_question"] = question
            st.rerun()
        if col2.button("Finish & get feedback"):
            feedback = interview.finish_session(st.session_state["interview_session_id"])
            st.write(
                f"Clarity: {feedback.clarity}/5, Technical depth: {feedback.technical_depth}/5, "
                f"Structure: {feedback.structure}/5"
            )
            st.write(feedback.feedback)
            del st.session_state["interview_session_id"]
