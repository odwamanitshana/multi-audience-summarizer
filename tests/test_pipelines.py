from app import (
    PERSONA_PRESETS,
    load_models,
    sentiment_for_text,
    summarize_with_persona,
)


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


def test_summarize_and_sentiment_smoke():
    summarizer, sentiment_model = load_models(device="cpu")
    sample = (
        "A startup launched a new energy-efficient sensor, reporting early demand "
        "from logistics and retail customers while highlighting supply chain risks."
    )

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

        assert isinstance(summary, str)
        assert summary.strip() != ""

        wc = _word_count(summary)
        if persona == "executive":
            assert 30 <= wc <= 200
        elif persona == "student":
            assert 50 <= wc <= 300
        elif persona == "casual":
            assert 5 <= wc <= 80

        label, score = sentiment_for_text(sentiment_model, summary)
        assert label in {"POSITIVE", "NEGATIVE", "UNKNOWN"}
        assert 0.0 <= float(score) <= 1.0
