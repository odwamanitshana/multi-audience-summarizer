"""Smoke tests for summarize_with_persona and sentiment_for_text.

All tests use dummy (mocked) pipelines provided by conftest.dummy_models,
so they are fast (< 1 s), deterministic, and CPU-only with no model downloads.

Run:  pytest -q
"""

import pytest

from app import summarize_with_persona, sentiment_for_text


# ── Word-count bounds per persona (intentionally loose) ──────────────────
WORD_BOUNDS = {
    "executive": (5, 200),
    "student": (5, 400),
    "casual": (1, 120),
}


# ── helpers ──────────────────────────────────────────────────────────────
def _word_count(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


# ── tests ────────────────────────────────────────────────────────────────


class TestSummarizeNonEmpty:
    """summarize_with_persona must return a non-empty string for every persona."""

    @pytest.mark.parametrize("persona", ["executive", "student", "casual"])
    def test_returns_non_empty(
        self, dummy_models, sample_text, persona_presets, persona
    ):
        summarizer, _ = dummy_models
        preset = persona_presets[persona]
        result = summarize_with_persona(
            summarizer,
            sample_text,
            persona,
            max_length=int(preset["max_length"]),
            min_length=int(preset["min_length"]),
            num_beams=int(preset["num_beams"]),
            length_penalty=float(preset["length_penalty"]),
        )
        assert isinstance(result, str)
        assert result.strip() != "", f"Summary for '{persona}' was empty"


class TestSummaryWordcount:
    """Word count must fall within loose persona-specific bounds."""

    @pytest.mark.parametrize("persona", ["executive", "student", "casual"])
    def test_wordcount_in_bounds(
        self, dummy_models, sample_text, persona_presets, persona
    ):
        summarizer, _ = dummy_models
        preset = persona_presets[persona]
        summary = summarize_with_persona(
            summarizer,
            sample_text,
            persona,
            max_length=int(preset["max_length"]),
            min_length=int(preset["min_length"]),
            num_beams=int(preset["num_beams"]),
            length_penalty=float(preset["length_penalty"]),
        )
        wc = _word_count(summary)
        lo, hi = WORD_BOUNDS[persona]
        assert lo <= wc <= hi, (
            f"[{persona}] word count {wc} outside [{lo}, {hi}]"
        )


class TestSentimentOutput:
    """sentiment_for_text must return (label: str, score: float) in expected range."""

    @pytest.mark.parametrize("persona", ["executive", "student", "casual"])
    def test_label_and_score(
        self, dummy_models, sample_text, persona_presets, persona
    ):
        summarizer, sentiment_model = dummy_models
        preset = persona_presets[persona]
        summary = summarize_with_persona(
            summarizer,
            sample_text,
            persona,
            max_length=int(preset["max_length"]),
            min_length=int(preset["min_length"]),
            num_beams=int(preset["num_beams"]),
            length_penalty=float(preset["length_penalty"]),
        )
        label, score = sentiment_for_text(sentiment_model, summary)

        assert isinstance(label, str)
        assert label in {"POSITIVE", "NEGATIVE"}, f"Unexpected label: {label}"
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0, f"Score {score} out of [0, 1]"
