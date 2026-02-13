from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import torch
from transformers import pipeline

# TODO: Swap summarization model here if needed.
# - Default: "sshleifer/distilbart-cnn-12-6"
# - Alternatives: "facebook/bart-large-cnn", "t5-small"
DEFAULT_SUMMARIZER_MODEL = "sshleifer/distilbart-cnn-12-6"
DEFAULT_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

PERSONA_TEMPLATES = {
    "executive": (
        "You are an executive assistant. Provide a concise, high-level summary "
        "emphasizing business impact, risks, and next steps."
    ),
    "student": (
        "You are a helpful tutor. Summarize in clear, structured bullets and "
        "explain any jargon briefly."
    ),
    "casual": (
        "You are chatting with a friend. Summarize in a relaxed, accessible tone."
    ),
}


def detect_device() -> str:
    """Return device string for transformers pipelines."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_models(device: str | None = None):
    """Load summarization and sentiment pipelines."""
    device = device or detect_device()
    device_index = 0 if device == "cuda" else -1

    summarizer = pipeline(
        "summarization",
        model=DEFAULT_SUMMARIZER_MODEL,
        device=device_index,
    )

    sentiment_model = pipeline(
        "sentiment-analysis",
        model=DEFAULT_SENTIMENT_MODEL,
        device=device_index,
    )

    return summarizer, sentiment_model


def apply_persona_prompt(article_text: str, persona: str) -> str:
    """Apply a light persona prompt prefix to guide the summarizer."""
    template = PERSONA_TEMPLATES.get(persona, PERSONA_TEMPLATES["casual"])
    return f"{template}\n\nARTICLE:\n{article_text}".strip()


def summarize_with_persona(
    summarizer,
    article_text: str,
    persona: str,
    max_length: int = 150,
    min_length: int = 30,
) -> str:
    """Summarize text using a persona prompt and safe truncation."""
    prompt = apply_persona_prompt(article_text, persona)

    # TODO: Tune these generation params for your use case.
    # Truncate long inputs to avoid model overflow.
    summary = summarizer(
        prompt,
        max_length=max_length,
        min_length=min_length,
        do_sample=False,
        truncation=True,
    )

    if isinstance(summary, list) and summary:
        return summary[0].get("summary_text", "").strip()
    return ""


def sentiment_for_text(sentiment_model, text: str) -> Tuple[str, float]:
    """Return sentiment label and score for a given text."""
    result = sentiment_model(text[:1000])  # light truncation for speed/safety
    if isinstance(result, list) and result:
        label = result[0].get("label", "UNKNOWN")
        score = float(result[0].get("score", 0.0))
        return label, score
    return "UNKNOWN", 0.0


def _read_sample_text() -> str:
    """Read sample text from file or use fallback text."""
    sample_path = Path("samples") / "sample_articles.txt"
    if sample_path.exists():
        content = sample_path.read_text(encoding="utf-8").strip()
        if content:
            return content

    # Fallback sample if file is missing or empty.
    return (
        "Artificial intelligence adoption continues to accelerate across industries, "
        "with companies reporting productivity gains but also raising concerns about "
        "workforce disruption and data privacy. Regulators are exploring new frameworks "
        "to balance innovation with safety."
    )


def main() -> None:
    device = detect_device()
    print(f"Using device: {device}")

    summarizer, sentiment_model = load_models(device=device)

    sample_text = _read_sample_text()

    for persona in PERSONA_TEMPLATES.keys():
        print("\n" + "=" * 60)
        print(f"Persona: {persona}")
        summary = summarize_with_persona(
            summarizer,
            sample_text,
            persona,
            max_length=150,
            min_length=30,
        )
        label, score = sentiment_for_text(sentiment_model, summary or sample_text)
        print("Summary:")
        print(summary)
        print(f"Sentiment: {label} ({score:.3f})")


if __name__ == "__main__":
    main()
