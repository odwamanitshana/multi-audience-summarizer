# Demo Assets — Placeholder & Instructions

This directory will hold demo assets (GIF, screenshots) for the README and PR.

## How to capture demo assets

### GIF (recommended)

1. **Windows**: Use [ScreenToGif](https://www.screentogif.com/) or [ShareX](https://getsharex.com/).
2. **macOS**: Use [Kap](https://getkap.co/) or QuickTime Player → screen recording → convert to GIF.
3. **Linux**: Use [Peek](https://github.com/phw/peek) or `ffmpeg` + `gifski`.

**Recording flow**:
1. Launch the app: `python app_gradio.py`
2. Open http://127.0.0.1:7860
3. Start recording
4. Paste an example article → click **Summarize** → show the 3 persona panels with sentiment badges
5. Optionally show: selecting a single persona, entering a URL, the long-input chunking notice
6. Stop recording and save as `assets/demo.gif`

### Screenshots

Capture at least:
- `assets/screenshot_main.png` — Main UI with article text pasted and all 3 personas selected
- `assets/screenshot_results.png` — Results panel showing per-persona summaries and sentiment badges
- `assets/screenshot_examples.png` — Example articles section at the bottom of the UI

### Adding to README

Once assets are captured, add to `README.md`:

```markdown
## Demo

![Demo GIF](assets/demo.gif)

### Screenshots

| Main UI | Results |
|---------|---------|
| ![Main](assets/screenshot_main.png) | ![Results](assets/screenshot_results.png) |
```

## File naming convention

| File | Purpose |
|------|---------|
| `demo.gif` | Animated walkthrough of the Summarize flow |
| `screenshot_main.png` | Main UI before summarization |
| `screenshot_results.png` | Results panel with persona summaries |
| `screenshot_examples.png` | Example articles section |
