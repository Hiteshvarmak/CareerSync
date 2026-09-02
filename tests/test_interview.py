from unittest.mock import MagicMock, patch

from backend.agents import interview
from backend.agents.interview import InterviewFeedback


def _fake_llm(content):
    llm = MagicMock()
    llm.invoke.return_value.content = content
    return llm


def test_start_session_creates_row_and_first_question():
    with patch("backend.agents.interview._get_llm", return_value=_fake_llm("Tell me about a challenge you faced.")):
        session_id, question = interview.start_session("Backend Engineer")
    assert session_id is not None
    assert "challenge" in question


def test_submit_answer_appends_transcript_and_returns_next_question():
    with patch("backend.agents.interview._get_llm", return_value=_fake_llm("First question?")):
        session_id, _ = interview.start_session("Backend Engineer")
    with patch("backend.agents.interview._get_llm", return_value=_fake_llm("Second question?")):
        next_question = interview.submit_answer(session_id, "I fixed a production outage.")
    assert next_question == "Second question?"


def test_finish_session_returns_structured_feedback():
    with patch("backend.agents.interview._get_llm", return_value=_fake_llm("Q1?")):
        session_id, _ = interview.start_session("Backend Engineer")

    fake_llm = MagicMock()
    fake_llm.with_structured_output.return_value.invoke.return_value = InterviewFeedback(
        clarity=4, technical_depth=3, structure=4, feedback="Solid answer, add more metrics."
    )
    with patch("backend.agents.interview._get_llm", return_value=fake_llm):
        feedback = interview.finish_session(session_id)
    assert feedback.clarity == 4
    assert "metrics" in feedback.feedback
