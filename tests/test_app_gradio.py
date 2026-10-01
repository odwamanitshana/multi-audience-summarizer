"""Presentation-layer tests for app_gradio (no model downloads)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app
import app_gradio
from app_gradio import _empty_results, _sentiment_chip, summarize_handler
from tests.conftest import _make_dummy_sentiment, _make_dummy_summarizer


class TestSentimentChip:
    def test_positive_chip(self):
        html = _sentiment_chip("POSITIVE", 0.91)
        assert "sentiment-positive" in html
        assert "Positive" in html
        assert "0.91" in html

    def test_negative_chip(self):
        html = _sentiment_chip("NEGATIVE", 0.42)
        assert "sentiment-negative" in html

    def test_neutral_chip(self):
        html = _sentiment_chip("UNKNOWN", 0.0)
        assert "sentiment-neutral" in html


class TestSummarizeHandlerPresentation:
    def test_empty_input_returns_placeholder(self):
        meta, ex, st, ca = summarize_handler("", "", ["Executive"])
        assert "Summaries will appear here" in meta
        assert ex == "" and st == "" and ca == ""

    def test_success_returns_three_cards(self, monkeypatch):
        monkeypatch.setattr(
            app,
            "load_models",
            lambda device=None: (_make_dummy_summarizer(), _make_dummy_sentiment()),
        )
        app_gradio._summarizer = None
        app_gradio._sentiment_model = None

        sample = (
            "A startup launched a new energy-efficient sensor, reporting early demand "
            "from logistics and retail customers."
        )
        meta, ex, st, ca = summarize_handler(sample, "", ["Executive", "Student", "Casual"])
        assert "Original word count" in meta
        assert "EXECUTIVE" in ex
        assert "STUDENT" in st
        assert "CASUAL" in ca
        assert "persona-card" in ex

    def test_empty_results_helper(self):
        assert _empty_results()[0].startswith("<p")
