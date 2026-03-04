# Release Buffer — Runtime Safeguards & Rollback

Pre-release safeguards to reduce breakage. These are **documented
recommendations only** — no protected source files are modified.

---

## 1. NO_PROXY Guidance

Gradio's internal `httpx` self-check can fail behind a corporate proxy.
Set `NO_PROXY` **before** launching the app in the same terminal session.

### PowerShell (Windows)

```powershell
$env:NO_PROXY = "localhost,127.0.0.1"
.\.venv\Scripts\python.exe app_gradio.py
```

### Bash / Zsh (macOS / Linux)

```bash
export NO_PROXY="localhost,127.0.0.1"
python app_gradio.py
```

> **Tip:** Add `NO_PROXY=localhost,127.0.0.1` to your `.env` file and load
> it with `python-dotenv` (already in `requirements.txt`).

---

## 2. Suggested Timeouts & Retries for External Calls

These are not implemented in the protected code files but should be added
when next touching those modules:

| Call site | File | Suggested change |
|-----------|------|------------------|
| `extract_article_from_url()` | `helpers.py` ≈ line 180 | Add `requests.get(url, timeout=15)` and wrap in a 1-retry loop |
| HF model download (first run) | `app.py` ≈ `load_models()` | Set `TRANSFORMERS_REQUEST_TIMEOUT=120` env var before import |
| Gradio self-check | (internal) | Handled by `NO_PROXY`; no code change needed |

### Code snippet (for helpers.py — do not apply, paste when ready)

```python
# In extract_article_from_url(), replace bare requests call with:
import requests
from requests.exceptions import RequestException

for attempt in range(2):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        break
    except RequestException:
        if attempt == 1:
            return ""
```

---

## 3. Recommended Log-Level Adjustments

For debugging during QA, temporarily raise log verbosity without modifying
protected files:

```bash
# Set via environment before launch
export TRANSFORMERS_VERBOSITY=info   # HF model download progress
export GRADIO_ANALYTICS_ENABLED=False
```

### Where to add ephemeral debug logs (snippets, not edits)

| Purpose | Location | Snippet |
|---------|----------|---------|
| Model load timing | `app.py` after `load_models()` return | `logging.info("Models loaded in %.1fs", elapsed)` |
| Chunk count | `helpers.py` inside `chunk_and_summarize()` | `logging.debug("Chunked into %d pieces", len(chunks))` |
| Summarise duration | `app_gradio.py` `summarize_handler()` | `logging.info("Summarise took %.1fs", time.time() - t0)` |

---

## 4. Rollback Procedure

### Revert last deployment tag

```bash
# Delete the remote tag
git push --delete origin vX.Y.Z

# Delete the local tag
git tag -d vX.Y.Z

# Force-push the previous good commit (if branch was fast-forwarded)
git reset --hard <previous-good-sha>
git push --force-with-lease origin main
```

### Revert a single commit on main

```bash
git revert <sha> --no-edit
git push origin main
```

### HF Spaces rollback

1. Go to **Settings → Repository** on your HF Space.
2. Click **Factory reset** or pin the Space to a previous commit SHA.
3. Alternatively, push a revert commit — Spaces auto-rebuilds on push.

---

*Last updated: 2026-02-27*
