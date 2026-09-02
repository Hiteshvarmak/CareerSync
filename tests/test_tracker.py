from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from backend.agents import tracker
from backend.agents.tracker import EmailClassification
from backend.db import Application, get_session


def test_classify_email_parses_structured_output():
    fake_llm = MagicMock()
    fake_llm.with_structured_output.return_value.invoke.return_value = EmailClassification(
        is_application_related=True, company="Acme", role="SWE Intern", status="interview"
    )
    with patch("backend.agents.tracker._get_llm", return_value=fake_llm):
        result = tracker.classify_email("Interview invite", "We'd like to schedule...")
    assert result.company == "Acme"
    assert result.status == "interview"


def test_upsert_application_creates_and_updates():
    classification = EmailClassification(is_application_related=True, company="Acme", role="SWE", status="applied")
    row = tracker.upsert_application("msg-1", classification)
    assert row.company == "Acme"

    updated_classification = EmailClassification(
        is_application_related=True, company="Acme", role="SWE", status="interview"
    )
    updated = tracker.upsert_application("msg-1", updated_classification)
    assert updated.id == row.id
    assert updated.status == "interview"


def test_upsert_application_ignores_irrelevant_email():
    classification = EmailClassification(is_application_related=False)
    assert tracker.upsert_application("msg-2", classification) is None


def test_stale_applications_flags_old_updates():
    session = get_session()
    stale_row = Application(
        company="OldCo", role="X", status="applied", last_updated=datetime.utcnow() - timedelta(days=30)
    )
    fresh_row = Application(company="NewCo", role="Y", status="applied", last_updated=datetime.utcnow())
    session.add_all([stale_row, fresh_row])
    session.commit()
    session.close()

    stale = [a.company for a in tracker.stale_applications()]
    assert "OldCo" in stale
    assert "NewCo" not in stale
