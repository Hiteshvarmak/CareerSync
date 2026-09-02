"""Mock Interview Agent: asks role-specific questions one at a time and
scores the finished session against a structured rubric."""

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from backend.db import InterviewSession, get_session

QUESTION_PROMPT = """You are interviewing a candidate for a {role} position.
Conversation so far (candidate answers marked A:):
{transcript}

Ask exactly one good follow-up interview question. Return only the question.
"""

FEEDBACK_PROMPT = """Score this {role} mock interview transcript on a 1-5
scale for clarity, technical depth, and structure (e.g. STAR method), and
give 2-3 concrete lines of feedback.

Transcript:
{transcript}
"""


class InterviewFeedback(BaseModel):
    clarity: int = Field(ge=1, le=5)
    technical_depth: int = Field(ge=1, le=5)
    structure: int = Field(ge=1, le=5)
    feedback: str


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=0.3)


def start_session(role: str) -> tuple[int, str]:
    session = get_session()
    try:
        row = InterviewSession(role=role, transcript="")
        session.add(row)
        session.commit()
        session.refresh(row)
        session_id = row.id
    finally:
        session.close()
    question = _get_llm().invoke(QUESTION_PROMPT.format(role=role, transcript="(none yet)")).content
    _append_transcript(session_id, f"Q: {question}")
    return session_id, question


def _append_transcript(session_id: int, line: str) -> str:
    session = get_session()
    try:
        row = session.get(InterviewSession, session_id)
        row.transcript = (row.transcript + "\n" + line).strip()
        session.commit()
        return row.transcript
    finally:
        session.close()


def submit_answer(session_id: int, answer: str) -> str:
    transcript = _append_transcript(session_id, f"A: {answer}")
    db = get_session()
    try:
        role = db.get(InterviewSession, session_id).role
    finally:
        db.close()
    question = _get_llm().invoke(QUESTION_PROMPT.format(role=role, transcript=transcript)).content
    _append_transcript(session_id, f"Q: {question}")
    return question


def finish_session(session_id: int) -> InterviewFeedback:
    db = get_session()
    try:
        row = db.get(InterviewSession, session_id)
        role, transcript = row.role, row.transcript
    finally:
        db.close()
    llm = _get_llm().with_structured_output(InterviewFeedback)
    feedback = llm.invoke(FEEDBACK_PROMPT.format(role=role, transcript=transcript))
    db = get_session()
    try:
        row = db.get(InterviewSession, session_id)
        row.feedback = feedback.feedback
        db.commit()
    finally:
        db.close()
    return feedback


def handle_message(text: str) -> str:
    """Entry point used by the orchestrator's interview node. `text` is
    treated as the target role for a fresh practice question."""
    _, question = start_session(role=text)
    return f"Let's practice a {text} interview. First question:\n{question}"
