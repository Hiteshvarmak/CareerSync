"""Planner Agent: turns a syllabus PDF or a free-text request into tasks."""

from pypdf import PdfReader
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from backend.db import Task, get_session


class TaskItem(BaseModel):
    title: str
    due_date: str | None = Field(default=None, description="ISO date, e.g. 2026-09-10")
    priority: str = Field(default="medium", description="low, medium, or high")


class TaskList(BaseModel):
    tasks: list[TaskItem]


EXTRACTION_PROMPT = """Extract concrete, actionable tasks with deadlines from the
text below (a syllabus, an assignment list, or a plain request). Only include
items with clear actions. If no date is given, leave due_date empty.

Text:
{text}
"""


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=0)


def extract_tasks_from_text(text: str) -> list[TaskItem]:
    llm = _get_llm().with_structured_output(TaskList)
    result = llm.invoke(EXTRACTION_PROMPT.format(text=text))
    return result.tasks


def extract_tasks_from_pdf(pdf_path: str) -> list[TaskItem]:
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return extract_tasks_from_text(text)


def save_tasks(tasks: list[TaskItem], source: str = "planner") -> list[Task]:
    session = get_session()
    try:
        rows = [
            Task(title=t.title, due_date=t.due_date, priority=t.priority, source=source)
            for t in tasks
        ]
        session.add_all(rows)
        session.commit()
        for row in rows:
            session.refresh(row)
        return rows
    finally:
        session.close()


def add_manual_task(title: str, due_date: str | None = None, priority: str = "medium") -> Task:
    return save_tasks([TaskItem(title=title, due_date=due_date, priority=priority)], source="manual")[0]


def todays_tasks() -> list[Task]:
    session = get_session()
    try:
        return session.query(Task).filter(Task.done.is_(False)).order_by(Task.due_date).all()
    finally:
        session.close()


def handle_message(text: str) -> str:
    """Entry point used by the orchestrator's planner node."""
    tasks = extract_tasks_from_text(text)
    if not tasks:
        return "I didn't find any concrete tasks in that — try pasting a syllabus or a deadline list."
    saved = save_tasks(tasks)
    lines = [f"- {t.title}" + (f" (due {t.due_date})" if t.due_date else "") for t in saved]
    return "Added to your task list:\n" + "\n".join(lines)
