# CareerPilot

AI multi-agent companion for students and job seekers. A LangGraph
orchestrator routes requests to specialized agents that plan your day,
track your job hunt, close skill gaps, and run mock interviews.

## Why this exists

We all accumulate useful information — ideas, resources, notes on what
we've done — scattered across notes apps, saved messages, documents, and
screenshots. The problem usually isn't a lack of information; it's that
retrieval requires remembering the exact keyword you filed it under, not
just the idea. If you only remember *what* you did, not the words you
used to describe it, keyword search fails you.

The Skill-Gap Agent is a working instance of the fix: it embeds your
resume and target job postings into a vector store (Chroma) and matches
by semantic similarity, not exact terms. A job posting asking for
"stakeholder communication" can match a resume line that says "presented
findings to leadership" — same idea, different words. That's retrieval
by meaning instead of by memory.

## Architecture

| Agent | Responsibility |
|---|---|
| Planner | Ingests syllabus PDFs / deadlines, outputs a prioritized daily task list |
| Application Tracker | Reads Gmail for application status signals, flags stale applications |
| Skill-Gap | Compares resume/LinkedIn skills against target job postings |
| Mock Interview | Runs a text/voice mock interview and scores answers |
| Orchestrator | Routes requests to the right agent, owns shared state (LangGraph) |

Only the orchestrator and stubbed agent nodes exist so far — see
`backend/graph.py`. Each agent's real implementation lands in its own
phase (see the phased build plan below).

## Project layout

```
backend/
  agents/       # per-agent implementations (added phase by phase)
  models.py     # shared LangGraph state schema
  graph.py      # orchestrator: router + agent nodes
  main.py       # CLI loop for local development
frontend/       # dashboard (Streamlit or React) - added in later phases
data/           # local SQLite DB, sample PDFs
tests/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in ANTHROPIC_API_KEY
```

## Run

```bash
python -m backend.main
```

## Test

```bash
pytest
```

## Phased build plan

1. **MVP:** Planner Agent + manual task input, simple dashboard, no external integrations.
2. **Phase 2:** Application Tracker Agent with Gmail API (read-only), persistent DB, daily digest.
3. **Phase 3:** Skill-Gap Agent with RAG over job descriptions + resume upload.
4. **Phase 4:** Mock Interview Agent, text-based first, voice via Whisper as a stretch goal.
5. **Polish:** Dashboard UI, architecture diagram, deployed demo.
