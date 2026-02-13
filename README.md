# Multi-Audience Summarizer

A minimal Python prototype that summarizes articles for different audiences (executive, student, casual) and reports sentiment.

## Project idea (one line)
Summarize the same article in different tones for different audiences and add a quick sentiment snapshot.

## MVP
- Load a summarization model and a sentiment model
- Generate persona-based summaries from the same input
- Print sentiment labels/scores for each persona summary

## Quick setup (VS Code)
1. Create and activate a virtual environment:
   - Windows (PowerShell): `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python app.py`

## Notes
- The first run will download Hugging Face models (internet required).
- Swap models in [app.py](app.py) if you want higher quality or speed.