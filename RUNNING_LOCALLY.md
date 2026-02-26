# Running Locally

Step-by-step guide to run **Multi-Audience Summarizer** on your local machine.

---

## 1. Prerequisites

- **Python 3.10+** (tested with 3.13 on Windows, 3.11 on Linux/macOS)
- **pip** (bundled with Python)
- **Git** (to clone the repo)
- ~1.5 GB free disk space for model downloads on first run

---

## 2. Clone and set up the virtual environment

```bash
git clone https://github.com/odwamanitshana/multi-audience-summarizer.git
cd multi-audience-summarizer
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Proxy / NO_PROXY configuration

If you are behind a **corporate or system HTTP proxy**, Gradio's internal
`httpx` self-check can fail with `RemoteProtocolError`. Fix this by telling
your OS to bypass the proxy for localhost:

### Windows (PowerShell)

```powershell
$env:NO_PROXY = "localhost,127.0.0.1"
```

### macOS / Linux

```bash
export NO_PROXY="localhost,127.0.0.1"
```

> Set this **before** running `app_gradio.py` in the same terminal session.

---

## 4. (Optional) DEMO_MODEL environment variable

By default the app downloads `sshleifer/distilbart-cnn-12-6` (~1.2 GB).
If you want to use a **smaller or custom model** for development/demo purposes,
set the `DEMO_MODEL` environment variable:

### Windows

```powershell
$env:DEMO_MODEL = "sshleifer/distilbart-cnn-12-6"   # default
# or a smaller model for fast local testing:
# $env:DEMO_MODEL = "philschmid/bart-large-cnn-samsum"
```

### macOS / Linux

```bash
export DEMO_MODEL="sshleifer/distilbart-cnn-12-6"
```

> **Note:** The app currently reads model names from `app.py`. To use
> `DEMO_MODEL`, you would add `os.environ.get("DEMO_MODEL", default_model)`
> in `app.py`'s `load_models()` function (not done yet — see `UI_HINTS.md`
> for a wiring snippet).

---

## 5. Run tests (fast, mocked — no model downloads)

```bash
pytest -q
```

All tests use mocks and should pass in under 30 seconds.

---

## 6. Launch the Gradio UI

```powershell
# Windows
$env:NO_PROXY = "localhost,127.0.0.1"
.\.venv\Scripts\python.exe app_gradio.py
```

```bash
# macOS / Linux
NO_PROXY="localhost,127.0.0.1" python app_gradio.py
```

Open **http://127.0.0.1:7860** in your browser.

### First-run model downloads

The **first Summarize click** downloads ~1.5 GB of HuggingFace models:

| Model | Purpose | Size |
|-------|---------|------|
| `sshleifer/distilbart-cnn-12-6` | Summarisation | ~1.2 GB |
| `distilbert-base-uncased-finetuned-sst-2-english` | Sentiment | ~0.3 GB |

Set `HF_TOKEN` for authenticated / faster downloads:

```powershell
$env:HF_TOKEN = "hf_your_token_here"
```

Subsequent runs use the local HuggingFace cache (`~/.cache/huggingface/`) and
start instantly.

---

## 7. Run the CLI backend

```bash
python app.py --save-outputs
# Outputs saved to samples/outputs/summary_outputs.jsonl
```

---

## 8. Troubleshooting

| Problem | Solution |
|---------|----------|
| `RemoteProtocolError` on launch | Set `NO_PROXY=localhost,127.0.0.1` |
| Port 7860 already in use | Kill stale process: `taskkill /F /PID <pid>` (Win) or `kill <pid>` (Linux) |
| Browser "connection refused" | Ensure the app printed `Running on http://127.0.0.1:7860`; check with `netstat -ano \| findstr 7860` |
| Models not downloading | Check internet, set `HF_TOKEN`, ensure `pip install transformers torch` succeeded |

---

*Last updated: 2026-02-26*
