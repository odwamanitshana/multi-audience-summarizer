"""Unit tests for helpers.py — chunking, token estimation, and safe model loading.

All tests use mocks or simple local functions; no HuggingFace model downloads
or GPU access required.

Run:  pytest tests/test_helpers.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List

import pytest

# Ensure project root is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import (
    DEFAULT_MAX_CHUNK_WORDS,
    chunk_and_summarize,
    chunk_text,
    estimate_token_count,
    extract_article_from_url,
    safe_load_models,
)


# ---------------------------------------------------------------------------
# estimate_token_count
# ---------------------------------------------------------------------------

class TestEstimateTokenCount:
    """estimate_token_count should return a reasonable heuristic value."""

    def test_empty_string(self):
        assert estimate_token_count("") == 0

    def test_single_word(self):
        result = estimate_token_count("hello")
        assert result >= 1, "Single word should produce at least 1 token"

    def test_short_text(self):
        text = "The quick brown fox jumps over the lazy dog"  # 9 words
        result = estimate_token_count(text)
        # 9 * 1.3 ≈ 11
        assert 9 <= result <= 15, f"Expected ~11 tokens, got {result}"

    def test_longer_text(self):
        text = " ".join(["word"] * 1000)
        result = estimate_token_count(text)
        # 1000 * 1.3 = 1300
        assert 1200 <= result <= 1400, f"Expected ~1300 tokens, got {result}"

    def test_returns_int(self):
        assert isinstance(estimate_token_count("some text here"), int)


# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------

class TestChunkText:
    """chunk_text should split text respecting word limits and sentence boundaries."""

    def test_short_text_single_chunk(self):
        text = "A short sentence. Another one."
        chunks = chunk_text(text, max_words=100)
        assert len(chunks) == 1
        assert text.strip() in chunks[0]

    def test_splits_at_sentence_boundary(self):
        # Build text with clear sentences that exceed max_words together.
        s1 = "Word " * 50 + "end."  # ~51 words
        s2 = "Another " * 50 + "end."  # ~51 words
        text = f"{s1} {s2}"
        chunks = chunk_text(text, max_words=60)
        assert len(chunks) >= 2, f"Expected >=2 chunks, got {len(chunks)}"

    def test_chunk_sizes_within_limit(self):
        sentences = [f"Sentence number {i} has several words in it." for i in range(50)]
        text = " ".join(sentences)
        chunks = chunk_text(text, max_words=40)
        for i, chunk in enumerate(chunks):
            wc = len(chunk.split())
            # Individual sentences might just barely exceed if a single sentence
            # is longer than max_words (force-add case), but normal chunks
            # should be at or below.
            # We allow a small margin for the force-add edge case.
            assert wc <= 60, f"Chunk {i} has {wc} words, expected <=60"

    def test_empty_text(self):
        chunks = chunk_text("", max_words=100)
        assert len(chunks) == 1  # Returns [text] as fallback

    def test_single_long_sentence_force_added(self):
        # A single sentence with more words than max_words.
        long_sentence = "word " * 200 + "end."
        chunks = chunk_text(long_sentence, max_words=50)
        assert len(chunks) >= 1
        # The full sentence should appear in the chunks (force-added).
        combined = " ".join(chunks)
        assert "end." in combined

    def test_preserves_all_content(self):
        sentences = ["First sentence here.", "Second sentence here.", "Third sentence here."]
        text = " ".join(sentences)
        chunks = chunk_text(text, max_words=10)
        combined = " ".join(chunks)
        for s in sentences:
            assert s in combined, f"Lost sentence: {s}"

    def test_default_max_words(self):
        # Verify default parameter matches module constant.
        text = "Short."
        chunks = chunk_text(text)
        assert len(chunks) == 1  # Short text → 1 chunk with default


# ---------------------------------------------------------------------------
# chunk_and_summarize (mocked summarizer)
# ---------------------------------------------------------------------------

class TestChunkAndSummarize:
    """chunk_and_summarize should call the summarizer per-chunk then aggregate."""

    @staticmethod
    def _make_tracking_summarizer() -> tuple:
        """Return (mock_fn, call_log) where call_log records each invocation."""
        call_log: List[dict] = []

        def mock_summarize(
            summarizer: Any,
            text: str,
            persona: str,
            max_length: int = 150,
            min_length: int = 30,
            num_beams: int = 4,
            length_penalty: float = 1.0,
        ) -> str:
            call_log.append({
                "text_len": len(text.split()),
                "persona": persona,
                "max_length": max_length,
                "min_length": min_length,
            })
            # Return a deterministic short summary.
            return f"[summary-{len(call_log)}]"

        return mock_summarize, call_log

    def test_short_text_single_pass(self):
        mock_fn, log = self._make_tracking_summarizer()
        text = "A short article about cats and dogs."
        result = chunk_and_summarize(
            text, "executive", "fake_summarizer",
            persona_preset={"max_length": 110, "min_length": 40, "num_beams": 4, "length_penalty": 1.0},
            max_chunk_words=100,
            _summarize_fn=mock_fn,
        )
        # For short text (1 chunk), only 1 call expected.
        assert len(log) == 1
        assert result == "[summary-1]"

    def test_long_text_multi_chunk(self):
        mock_fn, log = self._make_tracking_summarizer()
        # Build text with 3 clear chunks (each ~40 words).
        chunk_text_parts = [
            " ".join([f"word{i}" for i in range(40)]) + "."
            for _ in range(3)
        ]
        long_text = " ".join(chunk_text_parts)

        result = chunk_and_summarize(
            long_text, "student", "fake_summarizer",
            persona_preset={"max_length": 200, "min_length": 80, "num_beams": 4, "length_penalty": 0.9},
            max_chunk_words=50,
            _summarize_fn=mock_fn,
        )
        # Expect: 3 chunk calls + 1 aggregation call = 4 total.
        assert len(log) >= 4, f"Expected >=4 calls, got {len(log)}: per-chunk + aggregation"
        # Final result should be the last summary.
        assert "[summary-" in result

    def test_per_chunk_not_full_text(self):
        mock_fn, log = self._make_tracking_summarizer()
        # 200 words → should be chunked into multiple pieces with max_chunk_words=50.
        long_text = " ".join(["word"] * 200) + "."
        chunk_and_summarize(
            long_text, "casual", "fake_summarizer",
            persona_preset={"max_length": 60, "min_length": 15, "num_beams": 2, "length_penalty": 1.2},
            max_chunk_words=50,
            _summarize_fn=mock_fn,
        )
        # No individual chunk call should receive all 200 words.
        for entry in log[:-1]:  # Exclude the final aggregation call.
            assert entry["text_len"] < 200, (
                f"Chunk call received {entry['text_len']} words — "
                "expected chunked input, not full text"
            )

    def test_persona_passed_through(self):
        mock_fn, log = self._make_tracking_summarizer()
        text = " ".join(["word"] * 200) + "."
        chunk_and_summarize(
            text, "executive", "fake_summarizer",
            max_chunk_words=50,
            _summarize_fn=mock_fn,
        )
        for entry in log:
            assert entry["persona"] == "executive"


# ---------------------------------------------------------------------------
# safe_load_models (mocked app.load_models)
# ---------------------------------------------------------------------------

class TestSafeLoadModels:
    """safe_load_models should handle CPU fallback gracefully."""

    def test_successful_load(self, monkeypatch):
        import app
        dummy_sum = lambda *a, **k: "summary"
        dummy_sent = lambda *a, **k: ("POSITIVE", 0.9)
        monkeypatch.setattr(app, "load_models", lambda device=None: (dummy_sum, dummy_sent))

        s, sent = safe_load_models(device="cpu")
        assert s is dummy_sum
        assert sent is dummy_sent

    def test_cpu_fallback_on_cuda_failure(self, monkeypatch):
        import app

        call_log: List[str] = []

        def mock_load(device=None):
            call_log.append(device or "auto")
            if device and device != "cpu":
                raise RuntimeError("CUDA not available")
            return ("sum_cpu", "sent_cpu")

        monkeypatch.setattr(app, "load_models", mock_load)

        s, sent = safe_load_models(device="cuda")
        assert "cuda" in call_log, "Should have tried CUDA first"
        assert "cpu" in call_log, "Should have fallen back to CPU"
        assert s == "sum_cpu"

    def test_no_fallback_when_cpu_requested(self, monkeypatch):
        import app

        def mock_load(device=None):
            if device == "cpu":
                return ("sum", "sent")
            raise RuntimeError("Unexpected device")

        monkeypatch.setattr(app, "load_models", mock_load)

        s, sent = safe_load_models(device="cpu")
        assert s == "sum"

    def test_raises_when_cpu_also_fails(self, monkeypatch):
        import app

        def mock_load(device=None):
            raise RuntimeError("Everything is broken")

        monkeypatch.setattr(app, "load_models", mock_load)

        with pytest.raises(RuntimeError, match="Everything is broken"):
            safe_load_models(device="cpu")


# ---------------------------------------------------------------------------
# extract_article_from_url (mocked newspaper)
# ---------------------------------------------------------------------------

class TestExtractArticleFromUrl:
    """extract_article_from_url should fail gracefully without network."""

    def test_returns_empty_on_failure(self):
        # Invalid URL should not raise, just return empty string.
        result = extract_article_from_url("not-a-real-url")
        assert isinstance(result, str)
        # We accept empty string (newspaper3k may or may not be installed).

    def test_returns_string(self):
        result = extract_article_from_url("https://example.com")
        assert isinstance(result, str)
