import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DB_URL = os.environ.get("CAREERPILOT_DB_URL", "sqlite:///data/careerpilot.db")
_engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    due_date: Mapped[str | None] = mapped_column(default=None)
    priority: Mapped[str] = mapped_column(default="medium")
    source: Mapped[str] = mapped_column(default="manual")
    done: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str]
    role: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(default="applied")
    gmail_message_id: Mapped[str | None] = mapped_column(default=None, unique=True)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str]
    transcript: Mapped[str] = mapped_column(default="")
    feedback: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


def init_db() -> None:
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(_engine)


def get_session() -> Session:
    return SessionLocal()
