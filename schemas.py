"""Structured summarization contracts (per persona / doc type)."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DocType(str, Enum):
    ARTICLE = "article"
    MEETING = "meeting"
    POLICY = "policy"


class PersonaBrief(BaseModel):
    """Audience-specific brief returned by the summarization pipeline."""

    persona: str = Field(..., min_length=1, description="Persona id, e.g. executive")
    title: str = Field(..., min_length=1)
    bullets: List[str] = Field(..., min_length=1)
    risks: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("bullets", "risks", "next_steps", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return [str(item).strip() for item in value if str(item).strip()]


class MeetingBrief(PersonaBrief):
    """Meeting transcripts emphasize decisions and owned actions."""

    decisions: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)

    @field_validator("decisions", "action_items", mode="before")
    @classmethod
    def strip_meeting_lists(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return [str(item).strip() for item in value if str(item).strip()]


class SummarizeResponseV2(BaseModel):
    """Batch API / CLI export shape."""

    schema_version: int = 2
    doc_type: DocType = DocType.ARTICLE
    source_word_count: Optional[int] = None
    personas: dict[str, PersonaBrief | MeetingBrief]
