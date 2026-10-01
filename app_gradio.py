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

Gradio 6+ compatibility notes:
  - The `theme` parameter was moved from gr.Blocks() to demo.launch() in
    Gradio 6.0.  Passing it to the constructor now emits a deprecation
    warning and may be removed in a future release.
  - Binding to 127.0.0.1 instead of 0.0.0.0 avoids the
    httpx.RemoteProtocolError that occurs when an HTTP proxy intercepts
    Gradio's internal startup self-check on some Windows setups.
  - If you have a corporate or system HTTP proxy, set NO_PROXY in the
    environment before launching:
        $env:NO_PROXY = "localhost,127.0.0.1"
        .\\.venv\\Scripts\\python.exe app_gradio.py

TODO: Deploy to HF Spaces (add app.py alias or Procfile).
TODO: Abstract URL extraction and add rate-limit handling.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path
from typing import Any

import gradio as gr

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ink & Signal theme (shared visual direction)
# ---------------------------------------------------------------------------
INK_SIGNAL_CSS = """
.gradio-container {
  max-width: 1200px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
.ink-muted { color: #5B6470 !important; font-size: 0.875rem; }
.ink-meta.mono-data, .ink-meta.mono-data * {
  font-family: "IBM Plex Mono", ui-monospace, monospace !important;
  font-variant-numeric: tabular-nums;
}
.persona-card {
  border: 1px solid #E2E0DA;
  border-radius: 6px;
  padding: 1rem 1.1rem;
  background: #FFFFFF;
  min-height: 120px;
}
.persona-card .persona-label {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.75rem;
  letter-spacing: 0.06em;
  color: #5B6470;
  margin: 0 0 0.75rem 0;
}
.persona-card .persona-summary {
  color: #1A1814;
  font-size: 0.9375rem;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}
.persona-card .sentiment-chip {
  display: inline-block;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  border: 1px solid #E2E0DA;
}
.persona-card .sentiment-positive {
  color: #1F7A6D;
  border-color: #1F7A6D;
  background: #F0FAF8;
}
.persona-card .sentiment-negative {
  color: #B42318;
  border-color: #B42318;
  background: #FEF3F2;
}
.persona-card .sentiment-neutral {
  color: #5B6470;
  border-color: #E2E0DA;
  background: #F6F5F1;
}
.ink-alert {
  border-radius: 6px;
  padding: 0.65rem 0.85rem;
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  border-width: 1px;
  border-style: solid;
}
.ink-alert-error { color: #B42318; border-color: #B42318; background: #FEF3F2; }
.ink-alert-warning { color: #9A6212; border-color: #9A6212; background: #FFFAF0; }
"""

INK_SIGNAL_THEME = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#FBF1EC",
        c100="#F4DCD0",
        c200="#E9B9A2",
        c300="#DD9573",
        c400="#D9774E",
        c500="#B5522A",
        c600="#9C4523",
        c700="#80391D",
        c800="#642C16",
        c900="#4A2010",
        c950="#2E140A",
    ),
    neutral_hue="stone",
    font=[gr.themes.GoogleFont("IBM Plex Sans"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace", "monospace"],
    radius_size=gr.themes.sizes.radius_sm,
).set(
    body_background_fill="#F6F5F1",
    body_text_color="#1A1814",
    block_border_color="#E2E0DA",
    button_primary_background_fill="#B5522A",
    button_primary_background_fill_hover="#9C4523",
    button_primary_text_color="#FFFFFF",
)

_PERSONA_ORDER = ("Executive", "Student", "Casual")
_EMPTY_PLACEHOLDER = '<p class="ink-muted">Summaries will appear here.</p>'
_PERSONA_INFO = (
    "Executive: ~3 sentences on impact & risk · "
    "Student: structured, explains jargon · "
    "Casual: short and plain"
)

# ---------------------------------------------------------------------------
# Robust backend imports — fall back gracefully if something is missing
# ---------------------------------------------------------------------------
try:
    from app import (
        PERSONA_PRESETS,
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
        extract_article_from_url,
        safe_load_models,
    )
except ImportError:
    logger.warning("helpers.py not found; chunking and URL extraction disabled.")

    def chunk_and_summarize(*a: Any, **kw: Any) -> str:  # type: ignore[misc]
        return ""

    def extract_article_from_url(url: str) -> str:  # type: ignore[misc]
        return ""

    def safe_load_models(device: Any = None) -> tuple[Any, Any]:  # type: ignore[misc]
        return load_models(device=device)


_DEFAULT_PRESETS: dict[str, dict[str, float]] = {
    "executive": {"max_length": 110, "min_length": 40, "num_beams": 4, "length_penalty": 1.0},
    "student": {"max_length": 200, "min_length": 80, "num_beams": 4, "length_penalty": 0.9},
    "casual": {"max_length": 60, "min_length": 15, "num_beams": 2, "length_penalty": 1.2},
}

_LONG_INPUT_WORD_THRESHOLD: int = 3000

_summarizer: Any = None
_sentiment_model: Any = None


def _ensure_models() -> tuple[Any, Any]:
    global _summarizer, _sentiment_model
    if _summarizer is None or _sentiment_model is None:
        _summarizer, _sentiment_model = safe_load_models()
    return _summarizer, _sentiment_model


def _load_examples(max_examples: int = 3) -> list[list[str]]:
    sample_path = Path("samples") / "sample_articles.txt"
    examples: list[list[str]] = []
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


def _empty_results() -> tuple[str, str, str, str]:
    return (_EMPTY_PLACEHOLDER, "", "", "")


def _alert_html(message: str, kind: str) -> str:
    safe = html.escape(message)
    css_class = "ink-alert-error" if kind == "error" else "ink-alert-warning"
    return f'<div class="ink-alert {css_class}">{safe}</div>'


def _sentiment_chip(label: str, score: float) -> str:
    if label == "POSITIVE":
        css = "sentiment-positive"
        text = f"Positive · {score:.2f}"
    elif label == "NEGATIVE":
        css = "sentiment-negative"
        text = f"Negative · {score:.2f}"
    else:
        css = "sentiment-neutral"
        text = f"Neutral · {score:.2f}"
    return f'<span class="sentiment-chip {css}">{html.escape(text)}</span>'


def _persona_card_html(
    persona_label: str,
    body_html: str,
    *,
    selected: bool,
) -> str:
    label = persona_label.upper()
    if not selected:
        inner = '<p class="ink-muted" style="margin:0">Not selected for this run.</p>'
    else:
        inner = body_html
    return (
        f'<div class="persona-card"><p class="persona-label">{html.escape(label)}</p>{inner}</div>'
    )


def _summarize_one_persona(
    text: str,
    persona_label: str,
    summarizer: Any,
    sentiment_model: Any,
    *,
    is_long: bool,
    presets: dict[str, dict[str, float]],
) -> str:
    persona = persona_label.lower()
    preset = presets.get(persona, {})

    try:
        if is_long:
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
        return _alert_html(f"Summarisation failed for {persona_label}: {exc}", "error")

    if summary and summary.startswith("[Error"):
        return _alert_html(summary.strip("[]"), "error")

    try:
        label, score = sentiment_for_text(
            sentiment_model,
            summary if summary and "[Error" not in summary else text,
        )
    except Exception:
        label, score = "UNKNOWN", 0.0

    chip = _sentiment_chip(label, score)
    summary_safe = html.escape(summary or "").replace("\n", "<br>")
    return f'<p class="persona-summary">{summary_safe}</p><div class="mono-data">{chip}</div>'


def summarize_handler(
    article_text: str,
    url_text: str,
    selected_personas: list[str],
) -> tuple[str, str, str, str]:
    """Run summarisation for each persona column; return meta + three card HTML strings."""
    text = (article_text or "").strip()

    if not text and url_text and url_text.strip():
        text = extract_article_from_url(url_text.strip())
        if not text:
            gr.Warning("Could not extract text from the URL. Paste the article text directly.")
            alert = _alert_html(
                "Could not extract text from the URL. Paste the article text directly.",
                "warning",
            )
            return (alert + _EMPTY_PLACEHOLDER, "", "", "")

    if not text:
        gr.Warning("Please paste some article text first.")
        return _empty_results()

    if not selected_personas:
        selected_personas = list(_PERSONA_ORDER)

    try:
        summarizer, sentiment_model = _ensure_models()
    except Exception as exc:
        logger.exception("Model loading failed")
        raise gr.Error(
            f"Failed to load models: {exc}. "
            "Check that dependencies are installed and see the console log."
        ) from exc

    word_count = len(text.split())
    is_long = word_count > _LONG_INPUT_WORD_THRESHOLD
    long_note = " · Long input — chunked summarisation enabled" if is_long else ""
    meta_parts = [
        '<div class="ink-meta mono-data">',
        f"<p><strong>Original word count:</strong> {word_count}{long_note}</p>",
        '<p class="ink-muted" style="margin-top:0.35rem">'
        "Sentiment is applied to each generated summary and is only an approximation."
        "</p>",
        "</div>",
    ]
    meta_html = "\n".join(meta_parts)

    presets = PERSONA_PRESETS if PERSONA_PRESETS else _DEFAULT_PRESETS
    selected_set = {p for p in selected_personas}

    cards: dict[str, str] = {}
    for persona_label in _PERSONA_ORDER:
        if persona_label not in selected_set:
            cards[persona_label] = _persona_card_html(persona_label, "", selected=False)
            continue
        body = _summarize_one_persona(
            text,
            persona_label,
            summarizer,
            sentiment_model,
            is_long=is_long,
            presets=presets,
        )
        cards[persona_label] = _persona_card_html(persona_label, body, selected=True)

    return (
        meta_html,
        cards["Executive"],
        cards["Student"],
        cards["Casual"],
    )


def build_ui() -> gr.Blocks:
    """Construct and return the Gradio Blocks app."""
    with gr.Blocks(
        title="Multi-Audience Summarizer",
    ) as app:
        gr.Markdown(
            "# Multi-Audience Summarizer\n"
            "Paste an article or URL. Get an executive brief, study notes and a casual "
            "recap, each with a tone check."
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
                    choices=list(_PERSONA_ORDER),
                    value=list(_PERSONA_ORDER),
                    label="Personas",
                    info=_PERSONA_INFO,
                )
                btn = gr.Button("Summarise", variant="primary")
                gr.Markdown(
                    '<p class="ink-muted">First run downloads ~1.5 GB of models; later runs are fast.</p>'
                )
                gr.Markdown(
                    '<p class="ink-muted">Long articles are chunked automatically while processing.</p>'
                )

            with gr.Column(scale=3):
                results_meta = gr.HTML(value=_EMPTY_PLACEHOLDER, label="Results")
                with gr.Row():
                    out_executive = gr.HTML("")
                    out_student = gr.HTML("")
                    out_casual = gr.HTML("")

        btn.click(
            fn=summarize_handler,
            inputs=[article_box, url_box, persona_select],
            outputs=[results_meta, out_executive, out_student, out_casual],
        )

        gr.Examples(
            examples=_load_examples(max_examples=3),
            inputs=[article_box],
            label="Example articles",
        )

    return app


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        theme=INK_SIGNAL_THEME,
        css=INK_SIGNAL_CSS,
    )
