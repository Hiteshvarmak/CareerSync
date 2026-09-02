"""Application Tracker Agent: reads Gmail (read-only) and classifies
application-related emails, then keeps the applications table current.

Requires a Google Cloud OAuth client file. See README "Gmail setup".
"""

import base64
import os
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from backend.db import Application, get_session

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "backend/credentials.json")
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "data/gmail_token.json")
STALE_AFTER_DAYS = 10


class EmailClassification(BaseModel):
    is_application_related: bool
    company: str | None = Field(default=None)
    role: str | None = Field(default=None)
    status: str = Field(
        default="applied",
        description="one of: applied, interview, rejected, offer, irrelevant",
    )


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=0)


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _decode_snippet(message: dict) -> str:
    return message.get("snippet", "")


def classify_email(subject: str, snippet: str) -> EmailClassification:
    llm = _get_llm().with_structured_output(EmailClassification)
    prompt = f"Subject: {subject}\nSnippet: {snippet}\n\nClassify this email."
    return llm.invoke(prompt)


def upsert_application(gmail_message_id: str, classification: EmailClassification) -> Application | None:
    if not classification.is_application_related or not classification.company:
        return None
    session = get_session()
    try:
        existing = (
            session.query(Application)
            .filter_by(gmail_message_id=gmail_message_id)
            .one_or_none()
        )
        if existing:
            existing.status = classification.status
            existing.last_updated = datetime.utcnow()
            session.commit()
            return existing
        row = Application(
            company=classification.company,
            role=classification.role or "",
            status=classification.status,
            gmail_message_id=gmail_message_id,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row
    finally:
        session.close()


def sync_applications(max_results: int = 20) -> list[Application]:
    service = get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", q="applied OR application OR interview OR offer", maxResults=max_results)
        .execute()
    )
    updated = []
    for msg_ref in results.get("messages", []):
        message = service.users().messages().get(userId="me", id=msg_ref["id"]).execute()
        headers = {h["name"]: h["value"] for h in message["payload"].get("headers", [])}
        subject = headers.get("Subject", "")
        classification = classify_email(subject, _decode_snippet(message))
        row = upsert_application(msg_ref["id"], classification)
        if row:
            updated.append(row)
    return updated


def stale_applications(days: int = STALE_AFTER_DAYS) -> list[Application]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    session = get_session()
    try:
        return (
            session.query(Application)
            .filter(Application.status == "applied", Application.last_updated < cutoff)
            .all()
        )
    finally:
        session.close()


def daily_digest() -> str:
    session = get_session()
    try:
        board = session.query(Application).all()
    finally:
        session.close()
    stale = stale_applications()
    lines = [f"{len(board)} tracked applications, {len(stale)} need follow-up."]
    for app in stale:
        lines.append(f"- Follow up: {app.company} ({app.role}) — no update in {STALE_AFTER_DAYS}+ days")
    return "\n".join(lines)


def handle_message(text: str) -> str:
    """Entry point used by the orchestrator's tracker node."""
    return daily_digest()
