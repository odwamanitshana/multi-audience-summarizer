# Polish Checklist — Pre-Release Manual QA

Run through this checklist before tagging a release. Each item is a quick
manual check; automate later if you find recurring issues.

---

## UI / Text Typos

- [ ] Scan `app_gradio.py` labels, placeholders, and helper text for spelling errors
- [ ] Check all `gr.Markdown()` strings for broken Markdown (unclosed bold, links)
- [ ] Verify emoji render correctly in all sentiment badges (✅ ❌ ⚠️)
- [ ] Confirm "Summarize" button label is consistent (not "Summarise" elsewhere)
- [ ] Ensure the word "persona" is not user-facing — prefer "audience" in the UI

## Accessibility Sanity

- [ ] Every `gr.Textbox`, `gr.CheckboxGroup`, and `gr.Button` has a visible `label`
- [ ] Tab order follows top-to-bottom, left-to-right reading flow (test with Tab key)
- [ ] Summarize button is reachable via keyboard (Enter or Space activates)
- [ ] Colour contrast of sentiment badges meets WCAG AA (4.5:1) — test with Lighthouse
- [ ] No content is cut off at browser zoom 150%

## Small UX Polish Items

- [ ] Input textbox placeholder text explains what to paste (article / URL)
- [ ] Results pane has a minimum height so the page doesn't "jump" on first Summarize
- [ ] Loading spinner / progress text is visible during model inference
- [ ] Error state (empty input, failed URL) shows a user-friendly message, not a traceback
- [ ] Example articles load on click without page reload

## Typography & Spacing

- [ ] Line height in result cards is ≥ 1.4 for readability
- [ ] Card padding is consistent across all three persona panels
- [ ] Section headers ("Input", "Results", "Examples") are visually distinct

## Final Smoke Test

- [ ] Paste a short article → Summarize → all three panels render
- [ ] Paste a long article (>3 000 words) → chunking notice appears → summaries render
- [ ] Enter a URL → text extracted → summaries render
- [ ] Leave input empty → Submit → friendly validation message

---

*Last updated: 2026-02-27*
