# QA_CHECKLIST.md — Cross-Browser & Accessibility Testing

> Run all checks against `http://127.0.0.1:7860` after launching with
> `NO_PROXY="localhost,127.0.0.1" python app_gradio.py`.

---

## 1. Browser Compatibility Matrix

| # | Check | Chrome | Firefox | Edge | Safari | Mobile (Chrome) |
|---|-------|--------|---------|------|--------|-----------------|
| 1 | Page loads without console errors | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Input textbox accepts paste & typing | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | URL textbox accepts a URL and extracts text | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Persona checkboxes toggle correctly | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Summarize button triggers processing | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Loading spinner appears during inference | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | All 3 persona panels render summaries | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Sentiment badges display with correct colours | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Example articles section is visible & clickable | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Long input (>3 000 words) chunking notice shown | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## 2. Functional Tests

### 2a. Short input (< 500 words)

**Repro steps:**
1. Open the app in browser
2. Paste a short news article (use line 1 from `samples/examples_for_ui.txt`)
3. Select all 3 personas (executive, student, casual)
4. Click **Summarize**

**Expected:**
- All 3 summary panels show output within 10–30 seconds
- Sentiment badges appear under each summary
- No errors in the browser console

### 2b. Long input (> 3 000 words)

**Repro steps:**
1. Open the app
2. Paste a long article (concatenate all 6 lines from `samples/examples_for_ui.txt` and duplicate 5×)
3. Select all personas
4. Click **Summarize**

**Expected:**
- A "chunking" or processing notice may appear
- Summaries still render correctly (may take 60+ seconds)
- No browser timeout or crash

### 2c. URL extraction

**Repro steps:**
1. Enter a publicly accessible article URL (e.g., a Wikipedia page)
2. Leave the main textbox empty
3. Click **Summarize**

**Expected:**
- App extracts article text from the URL
- Summaries render normally
- If extraction fails, a clear error message is shown

### 2d. Empty input

**Repro steps:**
1. Leave both textbox and URL empty
2. Click **Summarize**

**Expected:**
- A validation message prompts for input
- No crash or unhandled exception

### 2e. Single persona selection

**Repro steps:**
1. Paste a short article
2. Select only "student"
3. Click **Summarize**

**Expected:**
- Only the student panel shows a summary
- Other panels are blank or hidden
- Sentiment badge appears for the student summary

---

## 3. Accessibility Checks

| # | Check | Status |
|---|-------|--------|
| 1 | All form inputs have visible labels | ☐ |
| 2 | Tab order follows logical reading flow | ☐ |
| 3 | Summarize button is keyboard-accessible (Enter/Space) | ☐ |
| 4 | Colour contrast meets WCAG AA (4.5:1 ratio) | ☐ |
| 5 | Screen reader announces form labels correctly | ☐ |
| 6 | No content cut off at 150% zoom | ☐ |

**Tools:**
- Chrome DevTools → Lighthouse → Accessibility audit
- Firefox → Accessibility Inspector
- [axe DevTools](https://www.deque.com/axe/) browser extension

---

## 4. Mobile / Responsive View

**Repro steps:**
1. Open Chrome DevTools → Toggle Device Toolbar (Ctrl+Shift+M)
2. Select a mobile viewport (e.g., iPhone 14, Pixel 7)
3. Load `http://127.0.0.1:7860`

**Expected:**
- Layout stacks vertically (single column)
- Input textbox is usable on small screens
- Summarize button is tappable with thumb
- Results scroll naturally without horizontal overflow

---

## 5. Performance Baselines

| Metric | Target | How to measure |
|--------|--------|----------------|
| Page load (no models) | < 3 s | Chrome DevTools → Network tab |
| First summarise (model download) | < 120 s | Depends on connection speed |
| Subsequent summarise (cached) | < 30 s | Stopwatch from click to result |
| Memory usage (idle) | < 500 MB | Task Manager / Activity Monitor |

---

## 6. Known Issues & Workarounds

| Issue | Workaround | Status |
|-------|-----------|--------|
| `RemoteProtocolError` on launch behind proxy | Set `NO_PROXY=localhost,127.0.0.1` | Documented |
| Port 7860 occupied by stale process | Kill process manually (see RUNNING_LOCALLY.md) | Documented |
| Gradio theme flicker on first load | Cosmetic only; no fix needed | Known |
| newspaper3k may fail on paywalled URLs | Use plain-text paste instead of URL | Known |

---

## 7. Reporting Issues

When reporting a QA issue, include:
1. **Browser & version** (e.g., Chrome 122.0.6261.94)
2. **OS** (e.g., Windows 11 23H2)
3. **Steps to reproduce** (numbered)
4. **Expected vs actual behaviour**
5. **Console errors** (F12 → Console tab → copy/paste)
6. **Screenshot or screen recording** (optional but helpful)

File issues at: https://github.com/odwamanitshana/multi-audience-summarizer/issues

---

*Last updated: 2026-02-26*
