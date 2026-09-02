from unittest.mock import MagicMock, patch

from backend.agents import skill_gap
from backend.agents.skill_gap import SkillGapItem, SkillGapReport


def test_find_skill_gaps_uses_retrieved_resume_chunks():
    fake_collection = MagicMock()
    fake_collection.query.return_value = {"documents": [["Led a team of 4 engineers"]]}
    fake_llm = MagicMock()
    fake_llm.with_structured_output.return_value.invoke.return_value = SkillGapReport(
        items=[
            SkillGapItem(
                requirement="Leadership experience",
                covered=True,
                evidence="Led a team of 4 engineers",
            )
        ]
    )
    with patch("backend.agents.skill_gap._get_collection", return_value=fake_collection), patch(
        "backend.agents.skill_gap._get_llm", return_value=fake_llm
    ):
        report = skill_gap.find_skill_gaps("Looking for a candidate with leadership experience")

    assert report.items[0].covered is True
    fake_collection.query.assert_called_once()


def test_handle_message_prompts_for_resume_when_none_indexed():
    with patch("backend.agents.skill_gap.find_skill_gaps", return_value=SkillGapReport(items=[])):
        reply = skill_gap.handle_message("some job posting")
    assert "upload your resume" in reply
