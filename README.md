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

All four agents are implemented and wired into the orchestrator — see
`backend/graph.py` for routing and `backend/agents/` for each agent.

## Project layout

```
backend/
  agents/
    planner.py    # PDF/text -> structured task list (backend/agents/planner.py)
    tracker.py    # Gmail read-only sync + application status classification
    skill_gap.py  # Chroma-backed resume/job-posting RAG
    interview.py  # multi-turn mock interview + rubric scoring
  db.py          # SQLAlchemy models (Task, Application, InterviewSession)
  models.py      # shared LangGraph state schema
  graph.py       # orchestrator: router + agent nodes
  main.py        # CLI loop for local development
  scheduler.py   # APScheduler daily digest job
frontend/
  dashboard.py   # Streamlit dashboard (tasks, Kanban board, skill gap, interview)
data/            # local SQLite DB, Chroma store (gitignored)
tests/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in ANTHROPIC_API_KEY
```

### Gmail setup (for the Application Tracker agent)

The tracker needs read-only Gmail access, which requires *your own*
Google Cloud OAuth client — this can't be shared/pre-provisioned:

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, enable the **Gmail API**, and create an **OAuth client ID**
   (type: Desktop app).
2. Download the client secret JSON and save it as `backend/credentials.json`
   (gitignored — never commit this file).
3. First call to `tracker.sync_applications()` (or the dashboard's "Sync
   from Gmail" button) opens a browser to authorize; the token is cached
   at `data/gmail_token.json`.

Everything else (Planner, Skill-Gap, Mock Interview) only needs the
Anthropic API key.

## Run

```bash
python -m backend.main          # CLI chat loop
streamlit run frontend/dashboard.py   # dashboard
python -m backend.scheduler     # daily digest, runs on a cron schedule
```

## Test

```bash
pytest
```

## Deployment

Not yet deployed — this needs hosting accounts (e.g. Render for the
backend/scheduler, Streamlit Community Cloud or Vercel for the
dashboard) and their own environment secrets, so it's a manual step
rather than something to automate blind. Suggested path: containerize
`backend/` behind a small FastAPI wrapper, deploy the dashboard
separately pointing at it, and set `ANTHROPIC_API_KEY` /
`CAREERPILOT_DB_URL` as platform secrets.

## Build plan status

1. ✅ **MVP:** Planner Agent + manual task input, dashboard.
2. ✅ **Phase 2:** Application Tracker Agent with Gmail API (read-only), persistent DB, daily digest.
3. ✅ **Phase 3:** Skill-Gap Agent with RAG over job descriptions + resume upload.
4. ✅ **Phase 4:** Mock Interview Agent, text-based.
5. 🔲 **Polish:** deployed demo (needs your hosting accounts, see Deployment above); voice via Whisper remains a stretch goal.
