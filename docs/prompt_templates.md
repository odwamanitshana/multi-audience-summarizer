# Prompt Templates & Length-Control Guide

Robust prompt templates and runtime output-length controls for the
multi-audience-summarizer workspace (Copilot / Claude / ChatGPT agents).

---

## 1. System / Instruction Templates

### 1.1 Generate UI Code (Gradio component)

```
You are a senior Python developer working inside the multi-audience-summarizer
repository. Generate a single Gradio component function that:
- Accepts {description_of_inputs}.
- Returns {description_of_outputs}.
- Follows the existing code style in app_gradio.py (type hints, docstrings).
Return ONLY the Python function. No explanation, no markdown fences.
Limit output to 60 lines max.
```

### 1.2 Generate a Git Commit Message

```
Write a conventional-commit message for the following diff.
Rules:
  - Subject line ≤ 72 characters, imperative mood.
  - Optional body separated by a blank line; wrap at 72 characters.
  - Use one of: feat, fix, docs, chore, test, refactor, style, ci.
Return ONLY the commit message text. Nothing else.
```

### 1.3 Create a Pull-Request Body

```
Write a GitHub pull-request description for merging branch {branch} into main.
Include:
  1. One-line summary (≤ 120 chars)
  2. "## Changes" section — bullet list of what changed (≤ 10 bullets)
  3. "## How to verify" — numbered steps for a reviewer (≤ 5 steps)
  4. "## Test status" — one line: "pytest -q: X passed in Y s"
Total length ≤ 800 words. Use Markdown. No extra commentary.
```

### 1.4 Create a CHANGELOG Entry

```
Write a CHANGELOG.md entry for version {version}.
Format:
  ## [{version}] — {YYYY-MM-DD}
  ### Added
  - …
  ### Changed
  - …
  ### Fixed
  - …
Keep each bullet ≤ 120 characters. Limit to the items listed below:
{items}
Return ONLY the markdown block.
```

### 1.5 Summarise a File for Documentation

```
Read the file at {path} and produce a summary paragraph (≤ 300 characters)
describing its purpose, key exports, and dependencies. Return only the
paragraph, no code.
```

---

## 2. Length-Control Section

Predictable output length is critical for commit hooks, CI pipelines, and
UI text blocks that must not overflow.

### 2.1 Recommended Limits

| Output type        | Hard limit           | Soft target        |
|--------------------|----------------------|--------------------|
| Commit subject     | 72 characters        | 50–60 characters   |
| Commit body line   | 72 characters        | 60 characters      |
| PR title           | 120 characters       | 80 characters      |
| PR body            | 800 words            | 400–600 words      |
| UI tooltip / badge | 120 characters       | 80 characters      |
| UI summary block   | 300 characters       | 200 characters     |
| CHANGELOG bullet   | 120 characters       | 80 characters      |
| Token budget       | Model max (1 024)    | ≤ 512 tokens       |

### 2.2 Prompt Instructions to Enforce Limits

**Explicit character cap:**
```
Limit your response to at most {N} characters, including whitespace.
```

**Explicit token cap:**
```
Respond in at most {N} tokens.
```

**"Return only" guard:**
```
Return only the requested artifact. Do not add explanations, greetings,
or markdown fences unless explicitly asked.
```

**Excerpt request:**
```
Return the first 5 lines of the file, followed by "..." if there is more.
```

### 2.3 Example — Enforcing a 72-char Commit Subject

```
Write a commit message for the diff below.
The subject line MUST be ≤ 72 characters. If the initial subject exceeds
72 characters, shorten it by removing less-important details.
Return ONLY the commit message.

Diff:
{diff}
```

---

## 3. Short vs Detailed Output Wrappers

Use **short** mode for quick inline answers, commit messages, tooltips.
Use **detailed** mode for PR bodies, docs, architecture explanations.

### Short wrapper

```
Answer in ≤ 3 sentences. Be precise and omit pleasantries.
```

### Detailed wrapper

```
Provide a thorough answer. Use headings, bullet lists, and code blocks
where appropriate. Target 400–600 words.
```

### Compact wrapper (for CI / automation)

```
Return a single JSON object with keys: "summary" (≤ 120 chars),
"details" (≤ 500 chars). No other text.
```

### When to use each

| Scenario                         | Wrapper   |
|----------------------------------|-----------|
| In-editor quick fix suggestion   | Short     |
| Commit message generation        | Short     |
| PR / MR description              | Detailed  |
| CHANGELOG entry                  | Short     |
| Architecture decision record     | Detailed  |
| CI status one-liner              | Compact   |
| Gradio UI helper text            | Short     |

---

*Last updated: 2026-02-27*
