# UI_HINTS.md — Wiring Examples, Word Count & Size Warnings into the Gradio UI

> **Do NOT edit `app_gradio.py` directly as part of the Kanban closeout.**
> Instead, copy-paste the snippets below into your working branch when ready.

---

## 1. Load examples from `samples/examples_for_ui.txt`

Add a helper function near the top of `app_gradio.py` (after imports):

```python
def _load_ui_examples(path: str = "samples/examples_for_ui.txt") -> list[list[str]]:
    """Load one-per-line article examples for the gr.Examples widget."""
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return []
    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    # gr.Examples expects a list of lists (one inner list per row)
    return [[line] for line in lines[:6]]
```

## 2. Wire `gr.Examples` into the Blocks layout

Inside `build_ui()`, after the input `gr.Textbox`, add:

```python
examples_data = _load_ui_examples()
if examples_data:
    gr.Examples(
        examples=examples_data,
        inputs=[article_input],          # must match the Textbox variable
        label="Example articles (click to load)",
    )
```

This creates a clickable examples bar below the input box.

## 3. Live word count & size warning

Add a small event listener that updates a `gr.Markdown` component whenever the
user types or pastes text:

```python
word_count_display = gr.Markdown(value="**Words:** 0")

def _update_word_count(text: str) -> str:
    wc = len(text.split()) if text else 0
    warning = ""
    if wc > 3000:
        warning = "  ⚠️ Long input — will be chunked automatically."
    elif wc > 5000:
        warning = "  🚨 Very long input — summarisation may take 30+ seconds."
    return f"**Words:** {wc}{warning}"

article_input.change(
    fn=_update_word_count,
    inputs=[article_input],
    outputs=[word_count_display],
)
```

## 4. Input-size guidance text

Add a visible note above or below the input:

```python
gr.Markdown(
    "💡 **Tip:** Paste 50–3 000 words for best results. "
    "Longer articles are automatically chunked and summarised "
    "in multiple passes (see `helpers.chunk_and_summarize`)."
)
```

## 5. Displaying size warnings in the results pane

In `summarize_handler()`, you can prepend a notice to the output when chunking
was triggered:

```python
from helpers import estimate_token_count

token_est = estimate_token_count(article_text)
if token_est > 600:
    # chunk_and_summarize was used
    results_notice = (
        f"ℹ️ Input was ~{token_est} tokens — "
        "chunked into multiple passes for quality.\n\n"
    )
```

---

## File reference

| File | Purpose |
|------|---------|
| `samples/examples_for_ui.txt` | One example article per line (up to 6) |
| `app_gradio.py` | Main Gradio UI — paste snippets above here |
| `helpers.py` | `estimate_token_count`, `chunk_and_summarize` |

---

*Last updated: 2026-02-26*
