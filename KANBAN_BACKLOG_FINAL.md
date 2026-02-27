# KANBAN_BACKLOG_FINAL.md — Final Backlog Card Status

**Date**: 2026-02-27
**Branch**: `feature/backlog-finalize`
**Parent**: `feature/kanban-closeout`
**Repo**: multi-audience-summarizer

---

## Card Status

| # | Card | Status |
|---|------|--------|
| 1 | Refine prompt outputs & length control | **Done** |
| 2 | Final polish & buffer | **Done** |
| 3 | Retrospective & lessons learned | **Done** |

---

## Detailed Breakdown

### 1) Refine prompt outputs & length control

- **Status**: Done
- **Branch**: `feature/backlog-finalize`
- **Commit**: `bb3746d` docs: add prompt_templates and length-control wrappers
- **Files added**:
  - `docs/prompt_templates.md` — 5 concrete system/instruction templates (UI code, commit messages, PR bodies, CHANGELOG entries, file summaries) plus a length-control section with token/char limits and enforcement examples
  - `code-snippets/prompt_wrappers.txt` — 7 copy/paste-ready wrappers (SHORT, DETAILED, COMPACT, COMMIT, PR-BODY, FILE-ONLY, EXCERPT)
- **Acceptance**: ✅ prompt_templates.md has ≥5 templates, clear length-control recipe with limits table, short-vs-detailed wrapper guidance
- **Verify**:
  ```bash
  cat docs/prompt_templates.md | grep -c "### 1\."   # expect ≥5
  cat code-snippets/prompt_wrappers.txt | grep -c "\[.*\]"  # expect ≥5
  ```

### 2) Final polish & buffer

- **Status**: Done
- **Branch**: `feature/backlog-finalize`
- **Commit**: `3cd6928` chore(polish): add polish checklist, release buffer guidance and quick lint script
- **Files added**:
  - `docs/polish_checklist.md` — 25-item checklist covering UI typos, accessibility, UX polish, typography, and smoke tests
  - `docs/release_buffer.md` — NO_PROXY guidance (PowerShell + POSIX), timeout/retry snippets, log-level recommendations, rollback procedure
  - `tools/lint-quick.sh` — POSIX shell script that runs flake8 → pyflakes → py_compile fallback chain; safe when no linter is installed
- **Acceptance**: ✅ All three files present with clear actionable items; lint script has shebang and is idempotent
- **Verify**:
  ```bash
  test -f docs/polish_checklist.md && echo OK
  test -f docs/release_buffer.md && echo OK
  head -1 tools/lint-quick.sh   # expect #!/usr/bin/env sh
  ```

### 3) Retrospective & lessons learned

- **Status**: Done
- **Branch**: `feature/backlog-finalize`
- **Commit**: `b72434a` docs: add RETROSPECTIVE.md with root causes and recommendations
- **Files added**:
  - `RETROSPECTIVE.md` — Summary paragraph, top 5 issues with root causes, actions-taken table, 5 recommendations for next sprints, owner/follow-up action list
- **Acceptance**: ✅ Concise (~600 words), includes specific actionable improvements, owner placeholders present
- **Verify**:
  ```bash
  wc -w RETROSPECTIVE.md         # expect 300–800
  grep "Recommendations" RETROSPECTIVE.md  # expect match
  ```

---

## Additional deliverables

| File | Commit | Purpose |
|------|--------|---------|
| `tests/test_backlog_final.py` | `75b4691` | 11 tests verifying deliverable files exist and contain expected content |
| `KANBAN_BACKLOG_FINAL.md` | (this file) | Kanban card-to-status mapping |
| `CLOSEOUT_BACKLOG.md` | (this commit) | Final run report with commits, files, and verification steps |

---

## Verification Commands

```powershell
# Switch to branch
git checkout feature/backlog-finalize

# Activate venv
.\.venv\Scripts\Activate.ps1

# Run all tests (42 expected)
pytest -q

# List new files
git diff --name-only feature/kanban-closeout..feature/backlog-finalize
```
