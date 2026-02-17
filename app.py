from __future__ import annotations

"""Persona-aware summarizer prototype.

Usage:
- Run saver: python app.py --save-outputs
- Run tests: pip install -r requirements.txt ; pytest -q
"""

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union, cast

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

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

# TODO: Tune these persona presets as you iterate on prompt design.
PERSONA_PRESETS: Dict[str, Dict[str, float | int]] = {
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


def detect_device() -> str:
    """Return device string for transformers pipelines."""
    return "cuda" if torch.cuda.is_available() else "cpu"


SummarizerType = Union[Callable[..., Any], Dict[str, Any]]


def load_models(device: str | None = None):
    """Load summarization and sentiment pipelines."""
    device = device or detect_device()
    device_index = 0 if device == "cuda" else -1
    pipeline_fn: Callable[..., Any] = cast(Any, pipeline)

    # Some transformer builds may not register the "summarization" task.
    # Fallback to text2text-generation if needed.
    try:
        summarizer = pipeline_fn(
            "summarization",
            model=DEFAULT_SUMMARIZER_MODEL,
            device=device_index,
        )
    except KeyError:
        # Final fallback: load seq2seq model directly and run generate() manually.
        tokenizer = AutoTokenizer.from_pretrained(DEFAULT_SUMMARIZER_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(DEFAULT_SUMMARIZER_MODEL)
        model = model.to(device)
        summarizer = {
            "type": "seq2seq",
            "tokenizer": tokenizer,
            "model": model,
            "device": device,
        }

    sentiment_model = pipeline_fn(
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
    summarizer: SummarizerType,
    article_text: str,
    persona: str,
    max_length: int = 150,
    min_length: int = 30,
    num_beams: int = 4,
    length_penalty: float = 1.0,
) -> str:
    """Summarize text using a persona prompt and safe truncation."""
    prompt = apply_persona_prompt(article_text, persona)

    # TODO: Tune these generation params for your use case.
    # Truncate long inputs to avoid model overflow.
    if isinstance(summarizer, dict) and summarizer.get("type") == "seq2seq":
        tokenizer = summarizer["tokenizer"]
        model = summarizer["model"]

        max_input = getattr(tokenizer, "model_max_length", 1024) or 1024
        if max_input > 1024:
            max_input = 1024

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=max_input,
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # TODO: Tune these generation params for your use case.
        output_ids = model.generate(
            **inputs,
            max_length=max_length,
            min_length=min_length,
            num_beams=num_beams,
            length_penalty=length_penalty,
            do_sample=False,
        )
        text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return text.strip()

    summary = cast(Callable[..., Any], summarizer)(
        prompt,
        max_length=max_length,
        min_length=min_length,
        num_beams=num_beams,
        length_penalty=length_penalty,
        do_sample=False,
        truncation=True,
    )

    if isinstance(summary, list) and summary:
        text = summary[0].get("summary_text") or summary[0].get("generated_text", "")
        return text.strip()
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


def _read_samples(samples_file: str) -> List[str]:
    """Read sample lines from a file; fallback to a single sample string."""
    sample_path = Path(samples_file)
    if sample_path.exists():
        raw = sample_path.read_text(encoding="utf-8")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if lines:
            return lines
    return [_read_sample_text()]


def _ensure_output_dir(out_file: str) -> Path:
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path


def run_and_save_all(
    samples_file: str = "samples/sample_articles.txt",
    out_file: str = "samples/outputs/summary_outputs.jsonl",
) -> None:
    """Run summarization + sentiment for all samples/personas and save JSONL."""
    device = detect_device()
    print(f"Using device: {device}")

    summarizer, sentiment_model = load_models(device=device)
    samples = _read_samples(samples_file)
    out_path = _ensure_output_dir(out_file)

    saved_count = 0
    with out_path.open("a", encoding="utf-8") as f:
        for sample in samples:
            article_id = sample
            for persona, preset in PERSONA_PRESETS.items():
                summary = summarize_with_persona(
                    summarizer,
                    sample,
                    persona,
                    max_length=int(preset["max_length"]),
                    min_length=int(preset["min_length"]),
                    num_beams=int(preset["num_beams"]),
                    length_penalty=float(preset["length_penalty"]),
                )
                label, score = sentiment_for_text(
                    sentiment_model, summary or sample
                )
                record = {
                    "article_id": article_id,
                    "persona": persona,
                    "summary": summary,
                    "sentiment_label": label,
                    "sentiment_score": float(score),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                saved_count += 1

    print(f"Saved {saved_count} summaries to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Persona-aware summarizer")
    parser.add_argument(
        "--save-outputs",
        action="store_true",
        help="Run summarization and save JSONL outputs",
    )
    parser.add_argument(
        "--samples",
        default="samples/sample_articles.txt",
        help="Path to samples file",
    )
    parser.add_argument(
        "--out-file",
        default="samples/outputs/summary_outputs.jsonl",
        help="Path to output JSONL file",
    )
    args = parser.parse_args()

    if args.save_outputs:
        run_and_save_all(samples_file=args.samples, out_file=args.out_file)
        return

    device = detect_device()
    print(f"Using device: {device}")

    summarizer, sentiment_model = load_models(device=device)
    sample_text = _read_sample_text()

    for persona, preset in PERSONA_PRESETS.items():
        print("\n" + "=" * 60)
        print(f"Persona: {persona}")
        summary = summarize_with_persona(
            summarizer,
            sample_text,
            persona,
            max_length=int(preset["max_length"]),
            min_length=int(preset["min_length"]),
            num_beams=int(preset["num_beams"]),
            length_penalty=float(preset["length_penalty"]),
        )
        label, score = sentiment_for_text(sentiment_model, summary or sample_text)
        print("Summary:")
        print(summary)
        print(f"Sentiment: {label} ({score:.3f})")


if __name__ == "__main__":
    main()
