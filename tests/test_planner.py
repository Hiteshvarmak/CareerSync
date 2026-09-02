from unittest.mock import MagicMock, patch

from backend.agents import planner
from backend.agents.planner import TaskItem, TaskList


def test_extract_tasks_from_text_parses_structured_output():
    fake_llm = MagicMock()
    fake_llm.with_structured_output.return_value.invoke.return_value = TaskList(
        tasks=[TaskItem(title="Submit HW3", due_date="2026-09-10", priority="high")]
    )
    with patch("backend.agents.planner._get_llm", return_value=fake_llm):
        tasks = planner.extract_tasks_from_text("HW3 due Sept 10")
    assert tasks == [TaskItem(title="Submit HW3", due_date="2026-09-10", priority="high")]


def test_save_and_fetch_tasks_roundtrip():
    saved = planner.save_tasks([TaskItem(title="Read chapter 4")], source="test")
    assert saved[0].id is not None
    titles = [t.title for t in planner.todays_tasks()]
    assert "Read chapter 4" in titles


def test_handle_message_reports_when_no_tasks_found():
    with patch("backend.agents.planner.extract_tasks_from_text", return_value=[]):
        reply = planner.handle_message("just saying hi")
    assert "didn't find any concrete tasks" in reply
