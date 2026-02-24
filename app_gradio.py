"""Gradio UI for Multi-Audience Summarizer.

Quick start (local):
  python -m venv .venv
  .venv\\Scripts\\Activate.ps1          # Windows PowerShell
  # source .venv/bin/activate           # macOS / Linux
  pip install -r requirements.txt
  pytest -q                             # run tests first
  python app_gradio.py                  # launch UI on http://localhost:7860

HF Spaces:
  Set HF_TOKEN as a secret, rename this file to app.py (or add a Procfile),
  and push.  Models download on first request (~1.5 GB).

NOTE: The first Summarize click will download HuggingFace models.
      Set the HF_TOKEN env var for faster, authenticated downloads.

TODO: Deploy to HF Spaces (add app.py alias or Procfile).
TODO: Abstract URL extraction and add rate-limit handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Robust backend imports — fall back gracefully if something is missing
# ---------------------------------------------------------------------------
try:
    from app import (
        PERSONA_PRESETS,
        PERSONA_TEMPLATES,
        load_models,
        sentiment_for_text,
        summarize_with_persona,
    )
except ImportError as exc:
    raise SystemExit(
        f"Could not import from app.py: {exc}\n"
        "Make sure app.py is in the same directory and dependencies are "
        "installed (pip install -r requirements.txt)."
    )

try:
    from helpers import (
        chunk_and_summarize,
        estimate_token_count,
        extract_article_from_url,
        safe_load_models,
    )
except ImportError:
    # helpers.py missing — define inline stubs so the UI still works.
    logger.warning("helpers.py not found; chunking and URL extraction disabled.")

    def estimate_token_count(text: str) -> int:  # type: ignore[misc]
        return int(len(text.split()) * 1.3)

    def chunk_and_summarize(*a: Any, **kw: Any) -> str:  # type: ignore[misc]
        return ""

    def extract_article_from_url(url: str) -> str:  # type: ignore[misc]
        return ""

    def safe_load_models(device: Any = None) -> Tuple[Any, Any]:  # type: ignore[misc]
        return load_models(device=device)


# ---------------------------------------------------------------------------
# Fallback presets (used only when PERSONA_PRESETS is unavailable)
# ---------------------------------------------------------------------------
_DEFAULT_PRESETS: Dict[str, Dict[str, float]] = {
    "executive": {"max_length": 110, "min_length": 40, "num_beams": 4, "length_penalty": 1.0},
    "student":   {"max_length": 200, "min_length": 80, "num_beams": 4, "length_penalty": 0.9},
    "casual":    {"max_length": 60,  "min_length": 15, "num_beams": 2, "length_penalty": 1.2},
}

# Threshold (in words) above which we use chunk-then-aggregate summarisation.
_LONG_INPUT_WORD_THRESHOLD: int = 3000


# ---------------------------------------------------------------------------
# Globals — models are loaded lazily on first Summarize click
# ---------------------------------------------------------------------------
_summarizer: Any = None
_sentiment_model: Any = None


def _ensure_models() -> Tuple[Any, Any]:
    """Load models once on first call (lazy init keeps startup fast)."""
    global _summarizer, _sentiment_model
    if _summarizer is None or _sentiment_model is None:
        _summarizer, _sentiment_model = safe_load_models()
    return _summarizer, _sentiment_model


# ---------------------------------------------------------------------------
# Load example inputs from samples file
# ---------------------------------------------------------------------------
def _load_examples(max_examples: int = 3) -> List[List[str]]:
    """Read the first non-URL, non-empty lines from sample_articles.txt."""
    sample_path = Path("samples") / "sample_articles.txt"
    examples: List[List[str]] = []
    if sample_path.exists():
        for line in sample_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("http"):
                continue
            examples.append([line])
            if len(examples) >= max_examples:
                break
    if not examples:
        examples.append(
            [
                "A startup launched a new energy-efficient sensor, reporting "
                "early demand from logistics and retail customers."
            ]
        )
    return examples


# ---------------------------------------------------------------------------
# Sentiment badge helper
# ---------------------------------------------------------------------------
def _sentiment_badge(label: str, score: float) -> str:
    """Return colour-coded HTML for a sentiment result.

    Colour key:
      POSITIVE → ✅ green
      NEGATIVE → ❌ red
      other    → ⚠️  grey
    """
    if label == "POSITIVE":
        emoji, colour = "✅", "#2e7d32"
    elif label == "NEGATIVE":
        emoji, colour = "❌", "#c62828"
    else:
        emoji, colour = "⚠️", "#757575"
    return (
        f'<span style="color:{colour}; font-weight:600">'
        f"{emoji} {label} — {score:.2f}</span>"
    )


# ---------------------------------------------------------------------------
# Core handler wired to the Summarize button
# ---------------------------------------------------------------------------
def summarize_handler(
    article_text: str,
    url_text: str,
    selected_personas: List[str],
) -> str:
    """Run summarisation + sentiment for each selected persona, return HTML.

    If *article_text* is empty but *url_text* is provided, attempt to
    extract the article body via newspaper3k.
    """
    # ---- resolve input text ------------------------------------------------
    text = (article_text or "").strip()

    if not text and url_text and url_text.strip():
        text = extract_article_from_url(url_text.strip())
        if not text:
            return (
                "<p style='color:orange'>⚠️ Could not extract text from the URL. "
                "Please paste the article text directly.</p>"
            )

    if not text:
        return "<p style='color:red'>⚠️ Please paste some article text first.</p>"

    # ---- resolve personas --------------------------------------------------
    if not selected_personas:
        selected_personas = ["Executive", "Student", "Casual"]

    try:
        summarizer, sentiment_model = _ensure_models()
    except Exception as exc:
        logger.exception("Model loading failed")
        return (
            f"<p style='color:red'>❌ Failed to load models: {exc}<br>"
            "Make sure dependencies are installed and check the console log.</p>"
        )

    # ---- word count & long-input notice ------------------------------------
    word_count = len(text.split())
    is_long = word_count > _LONG_INPUT_WORD_THRESHOLD

    parts: List[str] = [
        f"<p><b>Original word count:</b> {word_count}"
        + (" ⚠️ <em>Long input — chunked summarisation enabled</em>" if is_long else "")
        + "</p>"
        "<p style='font-size:0.85em;color:#888'>"
        "ℹ️ Sentiment is applied to the generated summary and is only an approximation."
        "</p><hr>"
    ]

    presets = PERSONA_PRESETS if PERSONA_PRESETS else _DEFAULT_PRESETS

    for persona_label in selected_personas:
        persona = persona_label.lower()
        preset = presets.get(persona, {})

        try:
            if is_long:
                # Chunk + aggregate for very long articles.
                summary = chunk_and_summarize(
                    text,
                    persona,
                    summarizer,
                    persona_preset=preset,
                )
            else:
                summary = summarize_with_persona(
                    summarizer,
                    text,
                    persona,
                    max_length=int(preset.get("max_length", 150)),
                    min_length=int(preset.get("min_length", 30)),
                    num_beams=int(preset.get("num_beams", 4)),
                    length_penalty=float(preset.get("length_penalty", 1.0)),
                )
        except Exception as exc:
            logger.exception("Summarisation failed for persona '%s'", persona)
            summary = f"[Error: {exc}]"

        # Sentiment on the generated summary (or original text as fallback).
        try:
            label, score = sentiment_for_text(
                sentiment_model, summary if summary and "[Error" not in summary else text
            )
        except Exception:
            label, score = "UNKNOWN", 0.0

        badge = _sentiment_badge(label, score)

        parts.append(
            f"<h3>📌 {persona_label.title()}</h3>"
            f"<p>{summary}</p>"
            f"<p><b>Sentiment:</b> {badge}</p>"
            f"<hr>"
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Build Gradio interface
# ---------------------------------------------------------------------------
def build_ui() -> gr.Blocks:
    """Construct and return the Gradio Blocks app."""
    with gr.Blocks(
        title="Multi-Audience Summarizer",
        theme=gr.themes.Soft(),  # type: ignore[attr-defined]
    ) as app:
        gr.Markdown(
            "## 📝 Multi-Audience Summarizer\n"
            "Paste an article (or provide a URL) and get persona-specific "
            "summaries with sentiment analysis.\n\n"
            "*⚡ Models download on first click (~1.5 GB). Subsequent runs are fast.*"
        )

        with gr.Row():
            with gr.Column(scale=2):
                article_box = gr.Textbox(
                    label="Article text",
                    placeholder="Paste your article here …",
                    lines=12,
                    elem_id="article_text",
                )
                url_box = gr.Textbox(
                    label="Article URL (optional — extracts text automatically)",
                    placeholder="https://example.com/article",
                    lines=1,
                )
                persona_select = gr.CheckboxGroup(
                    choices=["Executive", "Student", "Casual"],
                    value=["Executive", "Student", "Casual"],
                    label="Personas",
                )
                btn = gr.Button(
                    "🚀 Summarize",
                    variant="primary",
                )
                gr.Markdown(
                    "<small>⏳ The button will show a spinner while processing. "
                    "Long articles are automatically chunked.</small>"
                )

            with gr.Column(scale=3):
                output_html = gr.HTML(label="Results")

        # Wire button click
        btn.click(
            fn=summarize_handler,
            inputs=[article_box, url_box, persona_select],
            outputs=output_html,
        )

        # Example inputs
        gr.Examples(
            examples=_load_examples(max_examples=3),
            inputs=[article_box],
            label="Example articles",
        )

    return app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False)
