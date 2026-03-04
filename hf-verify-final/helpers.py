"""Chunking, aggregation, and safe model-loading helpers.

These utilities support the Gradio UI and CLI when articles exceed a safe
token limit.  The chunking strategy is intentionally simple — future work
should explore overlapping windows, extractive pre-filtering, or
progressive summarization.

Functions:
  estimate_token_count(text)           — fast heuristic token estimate
  chunk_text(text, max_words)          — split on sentence boundaries
  chunk_and_summarize(...)             — multi-pass chunk → aggregate flow
  safe_load_models(device)             — load_models with CPU fallback
  extract_article_from_url(url)        — newspaper3k wrapper (best-effort)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — tune as needed
# ---------------------------------------------------------------------------
# Rough multiplier: 1 word ≈ 1.3 sub-word tokens for BART/T5 tokenizers.
_TOKENS_PER_WORD: float = 1.3
# Default chunk size in words.  800 words ≈ ~1 024 tokens — safely inside
# the 1 024 context window of distilbart-cnn-12-6.
DEFAULT_MAX_CHUNK_WORDS: int = 800

# ---------------------------------------------------------------------------
# Fallback persona presets (mirrors PERSONA_PRESETS in app.py)
# ---------------------------------------------------------------------------
_FALLBACK_PRESETS: Dict[str, Dict[str, float]] = {
    "executive": {"max_length": 110, "min_length": 40, "num_beams": 4, "length_penalty": 1.0},
    "student":   {"max_length": 200, "min_length": 80, "num_beams": 4, "length_penalty": 0.9},
    "casual":    {"max_length": 60,  "min_length": 15, "num_beams": 2, "length_penalty": 1.2},
}


# ── Token estimation ─────────────────────────────────────────────────────
def estimate_token_count(text: str) -> int:
    """Return an approximate token count using a simple word × 1.3 heuristic.

    This avoids importing a tokenizer just for a length check.
    """
    words = len(text.split())
    return int(words * _TOKENS_PER_WORD)


# ── Chunking ──────────────────────────────────────────────────────────────
def chunk_text(text: str, max_words: int = DEFAULT_MAX_CHUNK_WORDS) -> List[str]:
    """Split *text* into chunks of roughly *max_words* words each.

    The splitter tries to break on sentence boundaries (period / newline)
    so that individual chunks are more coherent.

    TODO: Add overlapping windows so context isn't lost at boundaries.
    TODO: Consider an extractive first step to drop low-info sentences.
    """
    # Split into sentences (simple regex; good enough for news text).
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_words = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())
        # If a single sentence exceeds max_words, force‐add it alone.
        if sentence_words > max_words:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_words = 0
            chunks.append(sentence)
            continue

        if current_words + sentence_words > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_words = 0

        current_chunk.append(sentence)
        current_words += sentence_words

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text]


# ── Chunk-then-aggregate summarisation ────────────────────────────────────
def chunk_and_summarize(
    article_text: str,
    persona: str,
    summarizer: Any,
    persona_preset: Optional[Dict[str, float]] = None,
    max_chunk_words: int = DEFAULT_MAX_CHUNK_WORDS,
    *,
    _summarize_fn: Optional[Callable[..., str]] = None,
) -> str:
    """Chunk a long article, summarise each chunk, then aggregate.

    Flow:
      1. Split article into ≤ max_chunk_words chunks.
      2. Summarise each chunk with the persona preset.
      3. Concatenate chunk summaries and run a final summarisation pass
         to produce one coherent output.

    The optional ``_summarize_fn`` parameter lets tests inject a mock
    without importing app.summarize_with_persona at module level.

    TODO: Replace naive concatenation with a trained merge or LLM-refine step.
    TODO: Progressive summarisation for very long documents (> 10 k words).
    """
    # Resolve the summarise callable.
    if _summarize_fn is None:
        try:
            from app import summarize_with_persona
        except ImportError:
            raise RuntimeError(
                "Cannot import summarize_with_persona from app.py.  "
                "Ensure app.py is on PYTHONPATH."
            )
        _summarize_fn = summarize_with_persona

    preset = persona_preset or _FALLBACK_PRESETS.get(persona, _FALLBACK_PRESETS["casual"])

    chunks = chunk_text(article_text, max_words=max_chunk_words)

    if len(chunks) <= 1:
        # Short enough — single pass is fine.
        return _summarize_fn(
            summarizer,
            article_text,
            persona,
            max_length=int(preset.get("max_length", 150)),
            min_length=int(preset.get("min_length", 30)),
            num_beams=int(preset.get("num_beams", 4)),
            length_penalty=float(preset.get("length_penalty", 1.0)),
        )

    # --- Pass 1: summarise each chunk individually --------------------------
    logger.info("Chunking article into %d parts for persona '%s'", len(chunks), persona)
    chunk_summaries: List[str] = []

    for i, chunk in enumerate(chunks):
        logger.debug("  Summarising chunk %d/%d (%d words)", i + 1, len(chunks), len(chunk.split()))
        summary = _summarize_fn(
            summarizer,
            chunk,
            persona,
            # Scale lengths down for per-chunk pass so they stay short.
            max_length=max(40, int(preset.get("max_length", 150) * 0.7)),
            min_length=max(10, int(preset.get("min_length", 30) * 0.5)),
            num_beams=int(preset.get("num_beams", 4)),
            length_penalty=float(preset.get("length_penalty", 1.0)),
        )
        if summary:
            chunk_summaries.append(summary)

    if not chunk_summaries:
        return ""

    # --- Pass 2: aggregate chunk summaries into one final summary -----------
    merged = " ".join(chunk_summaries)
    logger.info("Aggregating %d chunk summaries (%d words total)", len(chunk_summaries), len(merged.split()))

    aggregated = _summarize_fn(
        summarizer,
        merged,
        persona,
        max_length=int(preset.get("max_length", 150)),
        min_length=int(preset.get("min_length", 30)),
        num_beams=int(preset.get("num_beams", 4)),
        length_penalty=float(preset.get("length_penalty", 1.0)),
    )
    return aggregated


# ── Safe model loader ─────────────────────────────────────────────────────
def safe_load_models(device: Optional[str] = None) -> Tuple[Any, Any]:
    """Call app.load_models with automatic CPU fallback.

    If CUDA is requested but fails, retries on CPU.  Logs the device used.
    """
    try:
        from app import load_models
    except ImportError:
        raise RuntimeError(
            "Cannot import load_models from app.py. "
            "Ensure app.py is in the project root."
        )

    try:
        logger.info("Loading models (device=%s) …", device or "auto")
        summarizer, sentiment = load_models(device=device)
        logger.info("Models loaded successfully.")
        return summarizer, sentiment
    except Exception as exc:  # noqa: BLE001
        if device and device != "cpu":
            logger.warning("Failed to load on '%s': %s — retrying on CPU", device, exc)
            summarizer, sentiment = load_models(device="cpu")
            logger.info("Models loaded on CPU (fallback).")
            return summarizer, sentiment
        raise


# ── URL extraction (best-effort) ──────────────────────────────────────────
def extract_article_from_url(url: str) -> str:
    """Try to pull article body from *url* using newspaper3k.

    Returns the extracted text, or an empty string on failure.

    TODO: Add rate-limit handling and timeout before deploying to HF Spaces.
    """
    try:
        from newspaper import Article  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("newspaper3k not installed — cannot extract URL.")
        return ""

    try:
        article = Article(url)
        article.download()
        article.parse()
        return (article.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("URL extraction failed for %s: %s", url, exc)
        return ""
