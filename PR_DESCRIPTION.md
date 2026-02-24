## PR: Integrate Gradio UI, chunking helpers, and CI

### What changed

| File | Change |
|---|---|
| `app_gradio.py` | Full rewrite — integrated backend, URL extraction, chunking for long inputs, per-persona sentiment badges, examples |
| `helpers.py` *(new)* | `chunk_text`, `chunk_and_summarize`, `estimate_token_count`, `safe_load_models`, `extract_article_from_url` |
| `.github/workflows/ci.yml` *(new)* | GitHub Actions workflow — pytest on push/PR for `main` and `feature/*` |
| `PR_DESCRIPTION.md` *(new)* | This file |

### How to run locally

```bash
# 1. Create venv & install
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt

# 2. Run tests (fast, mocked, no model download)
pytest -q

# 3. Launch Gradio UI
python app_gradio.py
# Open http://localhost:7860
```

### Acceptance criteria for reviewers

**Automated (CI)**
- [ ] `pytest -q` passes (9 tests, all mocked, < 30 s)

**Manual smoke test (UI)**
1. Launch `python app_gradio.py` and open http://localhost:7860
2. Paste a short paragraph → click **Summarize** → verify 3 persona panels appear
3. Check sentiment badges show ✅/❌/⚠️ with a score
4. Select only "Executive" → click **Summarize** → verify only one panel renders
5. Leave article empty, enter a valid URL → click **Summarize** → verify extraction or friendly error
6. Paste a very long article (> 3 000 words) → verify chunked summarisation notice appears

### Notes

- **Model downloads**: The first Summarize click downloads ~1.5 GB of HuggingFace models. Subsequent runs use the cache.
- **Long inputs**: Articles over ~3 000 words are automatically chunked (sentence-boundary split), summarised per chunk, then aggregated into a final persona summary. This is a simple approach — see `TODO` comments in `helpers.py` for future improvements.
- **CPU-only CI**: Tests mock all model calls so CI runs fast without GPU.
- **URL extraction**: Uses `newspaper3k` if installed; graceful fallback message otherwise.

### Reviewer checklist

- [ ] Code is well-commented with TODOs for production hardening
- [ ] No model downloads happen at import time (lazy loading only)
- [ ] Tests remain fast and deterministic (mocked pipelines)
- [ ] CI workflow triggers on the correct branches
- [ ] Gradio UI is functional and shows friendly errors on bad input
