"""Shared pytest fixtures for multi-audience-summarizer tests."""

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so `import app` works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_text() -> str:
    """Short offline paragraph for testing — no network required."""
    return (
        "A startup launched a new energy-efficient sensor, reporting early demand "
        "from logistics and retail customers. The company highlighted supply chain "
        "risks but projected profitability within two years. Analysts praised the "
        "innovative design while cautioning about competitive pressures."
    )


@pytest.fixture
def persona_presets() -> dict:
    """Recommended generation presets per persona (mirrors PERSONA_PRESETS in app.py)."""
    return {
        "executive": {
            "max_length": 110,
            "min_length": 40,
            "num_beams": 4,
            "length_penalty": 1.0,
        },
        "student": {
            "max_length": 200,
            "min_length": 80,
            "num_beams": 4,
            "length_penalty": 0.9,
        },
        "casual": {
            "max_length": 60,
            "min_length": 15,
            "num_beams": 2,
            "length_penalty": 1.2,
        },
    }


# ---------------------------------------------------------------------------
# Dummy pipeline factories (used by tests to avoid downloading real models)
# ---------------------------------------------------------------------------


def _make_dummy_summarizer():
    """Return a callable that mimics a HF summarization pipeline."""

    def _dummy(*args, **kwargs):
        text = args[0] if args else kwargs.get("inputs", "")
        truncated = str(text)[:50]
        persona = "unknown"
        for p in ("executive", "student", "casual"):
            if p in str(text).lower():
                persona = p
                break
        return [{"summary_text": f"[{persona}] summary: {truncated}"}]

    return _dummy


def _make_dummy_sentiment():
    """Return a callable that mimics a HF sentiment-analysis pipeline."""

    def _dummy(text, **kwargs):
        return [{"label": "POSITIVE", "score": 0.95}]

    return _dummy


@pytest.fixture
def dummy_models(monkeypatch):
    """Patch app.load_models so no real model download occurs."""
    import app  # noqa: E402 — imported here so sys.path fix above takes effect

    dummy_sum = _make_dummy_summarizer()
    dummy_sent = _make_dummy_sentiment()

    monkeypatch.setattr(
        app, "load_models", lambda device=None: (dummy_sum, dummy_sent)
    )
    return dummy_sum, dummy_sent
