"""Skill-Gap Agent: RAG over a resume and job postings to find what's
already covered vs. what's missing, matching by meaning rather than
exact keywords (see README "Why this exists")."""

import os

import chromadb
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

CHROMA_DIR = os.environ.get("CAREERPILOT_CHROMA_DIR", "data/chroma")

GAP_ANALYSIS_PROMPT = """You are comparing a candidate's resume against a job
posting. Resume excerpts most relevant to this posting are listed below,
retrieved by semantic similarity (they may use different wording than the
posting itself).

Resume excerpts:
{resume_chunks}

Job posting:
{job_posting}

List: (1) requirements the resume already covers, citing the matching
resume excerpt, and (2) requirements with no matching coverage, each with
one concrete suggestion (a course or project) to close the gap.
"""


class SkillGapItem(BaseModel):
    requirement: str
    covered: bool
    evidence: str | None = Field(default=None, description="matching resume excerpt, if covered")
    suggestion: str | None = Field(default=None, description="course/project to close the gap, if not covered")


class SkillGapReport(BaseModel):
    items: list[SkillGapItem]


def _get_client() -> chromadb.ClientAPI:
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def _get_collection(name: str = "resume"):
    return _get_client().get_or_create_collection(name)


def _chunk(text: str, size: int = 500) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)] or [text]


def index_resume(resume_text: str) -> int:
    collection = _get_collection("resume")
    chunks = _chunk(resume_text)
    collection.add(
        documents=chunks,
        ids=[f"resume-{i}" for i in range(len(chunks))],
    )
    return len(chunks)


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=0)


def find_skill_gaps(job_posting: str, top_k: int = 5) -> SkillGapReport:
    collection = _get_collection("resume")
    retrieved = collection.query(query_texts=[job_posting], n_results=top_k)
    resume_chunks = "\n---\n".join(retrieved["documents"][0]) if retrieved["documents"] else ""
    llm = _get_llm().with_structured_output(SkillGapReport)
    return llm.invoke(
        GAP_ANALYSIS_PROMPT.format(resume_chunks=resume_chunks or "(no resume indexed yet)", job_posting=job_posting)
    )


def handle_message(text: str) -> str:
    """Entry point used by the orchestrator's skill_gap node. Treats the
    message as a job posting to compare against the already-indexed resume."""
    report = find_skill_gaps(text)
    if not report.items:
        return "No resume indexed yet — upload your resume first."
    lines = []
    for item in report.items:
        if item.covered:
            lines.append(f"✅ {item.requirement} — {item.evidence}")
        else:
            lines.append(f"⚠️ {item.requirement} — try: {item.suggestion}")
    return "\n".join(lines)
