"""Gradio UI for Multi-Audience Summarizer.

Quick start:
  python -m venv .venv
  .venv\\Scripts\\Activate.ps1          # Windows PowerShell
  # source .venv/bin/activate           # macOS / Linux
  pip install -r requirements.txt
  pytest -q                             # run tests first
  python app_gradio.py                  # launch UI on http://localhost:7860

NOTE: The first run will download HuggingFace models (~1.5 GB).
      Set HF_TOKEN env var for faster, authenticated downloads.

TODO: Deploy to HF Spaces (add app.py alias or Procfile).
TODO: Add URL extraction via newspaper3k.
TODO: Add chunking for very long articles (> 1024 tokens).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import gradio as gr

# ---------------------------------------------------------------------------
# Import backend from app.py (robust fallback if something is missing)
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
        "Make sure app.py is in the same directory and dependencies are installed."
    )


# ---------------------------------------------------------------------------
# Globals — models are loaded lazily on first Summarize click
# ---------------------------------------------------------------------------
_summarizer: Any = None
_sentiment_model: Any = None


def _ensure_models() -> Tuple[Any, Any]:
    """Load models once on first call (lazy init keeps startup fast)."""
    global _summarizer, _sentiment_model
    if _summarizer is None or _sentiment_model is None:
        _summarizer, _sentiment_model = load_models()
    return _summarizer, _sentiment_model


# ---------------------------------------------------------------------------
# Load example inputs from samples file
# ---------------------------------------------------------------------------
def _load_examples(max_examples: int = 3) -> List[List[str]]:
    """Read the first non-URL lines from sample_articles.txt for gr.Examples."""
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
    """Return a colour-coded sentiment string."""
    if label == "POSITIVE":
        emoji, colour = "🟢", "#2e7d32"
    elif label == "NEGATIVE":
        emoji, colour = "🔴", "#c62828"
    else:
        emoji, colour = "⚪", "#757575"
    return (
        f'<span style="color:{colour}; font-weight:600">'
        f"{emoji} {label} — {score:.3f}</span>"
    )


# ---------------------------------------------------------------------------
# Core handler wired to the Summarize button
# ---------------------------------------------------------------------------
def summarize_handler(
    article_text: str,
    selected_personas: List[str],
) -> str:
    """Run summarization + sentiment for each selected persona, return HTML."""
    if not article_text or not article_text.strip():
        return "<p style='color:red'>⚠️ Please paste some article text first.</p>"

    if not selected_personas:
        selected_personas = list(PERSONA_PRESETS.keys())

    summarizer, sentiment_model = _ensure_models()

    word_count = len(article_text.split())
    parts: List[str] = [
        f"<p><b>Original word count:</b> {word_count}</p><hr>"
    ]

    for persona in selected_personas:
        persona_lower = persona.lower()
        preset = PERSONA_PRESETS.get(persona_lower, {})

        # TODO: Tune presets further per persona.
        summary = summarize_with_persona(
            summarizer,
            article_text,
            persona_lower,
            max_length=int(preset.get("max_length", 150)),
            min_length=int(preset.get("min_length", 30)),
            num_beams=int(preset.get("num_beams", 4)),
            length_penalty=float(preset.get("length_penalty", 1.0)),
        )

        label, score = sentiment_for_text(
            sentiment_model, summary or article_text
        )
        badge = _sentiment_badge(label, score)

        parts.append(
            f"<h3>📌 {persona.title()}</h3>"
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
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "## 📝 Multi-Audience Summarizer\n"
            "Paste an article and get persona-specific summaries with sentiment."
        )

        with gr.Row():
            with gr.Column(scale=2):
                article_box = gr.Textbox(
                    label="Article text",
                    placeholder="Paste your article here …",
                    lines=10,
                    elem_id="article_text",
                )
                # TODO: Wire up URL extraction with newspaper3k.
                url_box = gr.Textbox(
                    label="Article URL (placeholder — paste text above for now)",
                    placeholder="https://example.com/article",
                    lines=1,
                    interactive=False,
                )
                persona_select = gr.CheckboxGroup(
                    choices=["Executive", "Student", "Casual"],
                    value=["Executive", "Student", "Casual"],
                    label="Personas",
                )
                btn = gr.Button("Summarize", variant="primary")

            with gr.Column(scale=3):
                output_html = gr.HTML(label="Results")

        # Wire button click
        btn.click(
            fn=summarize_handler,
            inputs=[article_box, persona_select],
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
