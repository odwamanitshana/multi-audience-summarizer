"""Tests for structured summarization schemas and persona YAML."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from persona_loader import load_personas
from schemas import DocType, MeetingBrief, PersonaBrief, SummarizeResponseV2


def test_persona_brief_validates():
    brief = PersonaBrief(
        persona="executive",
        title="AI adoption accelerates",
        bullets=["Productivity gains reported", "Privacy concerns rise"],
        risks=["Regulatory uncertainty"],
        next_steps=["Review data policy"],
        confidence=0.85,
    )
    assert brief.persona == "executive"
    assert len(brief.bullets) == 2


def test_persona_brief_strips_empty_bullets():
    brief = PersonaBrief(
        persona="student",
        title="Topic",
        bullets=["  keep me  ", "", "  "],
    )
    assert brief.bullets == ["keep me"]


def test_meeting_brief_extra_fields():
    brief = MeetingBrief(
        persona="meeting_ops",
        title="Sprint planning",
        bullets=["Velocity stable"],
        decisions=["Ship v2 Friday"],
        action_items=["Alice: update runbook"],
    )
    assert brief.decisions == ["Ship v2 Friday"]


def test_summarize_response_v2():
    payload = SummarizeResponseV2(
        doc_type=DocType.ARTICLE,
        source_word_count=1200,
        personas={
            "executive": PersonaBrief(
                persona="executive",
                title="T",
                bullets=["a"],
            )
        },
    )
    assert payload.schema_version == 2


def test_persona_brief_requires_title():
    with pytest.raises(ValidationError):
        PersonaBrief(persona="x", title="", bullets=["a"])


def test_load_personas_from_repo():
    personas = load_personas(Path(__file__).resolve().parents[1] / "personas")
    assert set(personas) >= {"executive", "student", "casual", "meeting_ops"}
    assert personas["executive"].label == "Executive"
