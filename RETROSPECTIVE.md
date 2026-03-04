# Retrospective & Lessons Learned

## Summary

The multi-audience-summarizer project evolved from a minimal CLI prototype to a
Gradio web UI with persona-based summarisation, sentiment badges, chunked
long-input handling, and a full CI/CD pipeline — over roughly four sprint cycles.
The bulk of the bugs and delays came from environment-specific issues (proxy
interception, port conflicts, Gradio API changes) rather than from core logic.
Documenting workarounds early and investing in mocked tests paid off quickly,
eliminating model-download bottlenecks in CI.

---

## Top 5 Issues Encountered

1. **Gradio `httpx` self-check crash behind corporate proxy**
   *Root cause:* Gradio 6+ performs an internal HTTP self-check at launch.
   When a system proxy intercepts `localhost` traffic, `httpx` receives an
   unexpected protocol response and raises `RemoteProtocolError`.
   *Impact:* Blocked all local development until diagnosed.

2. **Port 7860 held by stale Python process**
   *Root cause:* A previous `app_gradio.py` process was not terminated cleanly
   (Ctrl+C missed), leaving a zombie process binding the port.
   *Impact:* New launches failed with "Address already in use" and no clear
   error message from Gradio.

3. **SyntaxWarning from unescaped backslashes in docstring**
   *Root cause:* A PowerShell code snippet inside a Python docstring contained
   `\.` sequences, which Python 3.12+ flags as invalid escape sequences.
   *Impact:* Warning noise on every import; would become a hard error in
   future Python versions.

4. **Gradio theme API change (`Blocks()` vs `launch()`)**
   *Root cause:* Gradio 6 moved theme specification from the `Blocks()`
   constructor to `launch(theme=...)`. Existing code followed the old API.
   *Impact:* Theme was silently ignored, producing a plain white UI.

5. **GitHub CLI `gh pr create` transient API failure**
   *Root cause:* Pushing a new branch and immediately calling `gh pr create`
   can race against GitHub's ref-advertisement cache, producing "Head sha
   can't be blank".
   *Impact:* Automated PR creation failed; required a manual retry or a short
   delay before the CLI call.

---

## Actions Taken

| Issue | Resolution |
|-------|-----------|
| Proxy self-check | Bound server to `127.0.0.1`; documented `NO_PROXY` in README, RUNNING_LOCALLY.md, and release_buffer.md |
| Stale port | Documented `taskkill`/`kill` fallback in RUNNING_LOCALLY.md troubleshooting table |
| Backslash warning | Escaped `\.` → `\\.` in the docstring (one-line fix) |
| Theme API | Moved `theme=` kwarg from `Blocks()` to `launch()` |
| gh CLI race | Added manual PR-creation URL as fallback; noted retry advice in CLOSEOUT_REPORT.md |

---

## Recommendations for Next Sprints

1. **Add an integration-test matrix in CI.**
   Run `pytest` against Python 3.11 and 3.13 on both ubuntu-latest and
   windows-latest to catch OS-specific issues (path separators, proxy
   behaviour) before they reach developers.

2. **Use a small/mock model in CI.**
   Create a `DEMO_MODEL` env-var path that points to a tiny random-weight
   checkpoint (or a `unittest.mock` pipeline) so CI can exercise the full
   `summarize_handler` path without downloading 1.5 GB of weights.

3. **Gate merges on green CI.**
   Enable GitHub branch-protection rules on `main`: require status checks
   to pass and at least one approval before merge. This prevents broken
   commits from reaching the default branch.

4. **Add a pre-merge checklist as a PR template.**
   Create `.github/PULL_REQUEST_TEMPLATE.md` with checkboxes for: tests
   pass, docs updated, no protected-file edits, KANBAN card linked. This
   reduces reviewer cognitive load.

5. **Schedule quarterly dependency pruning.**
   Pin top-level dependencies in `requirements.txt` and run
   `pip-audit` or `safety check` monthly. Gradio and Transformers ship
   breaking changes frequently; pinning prevents surprise regressions.

---

## Owner & Follow-Up Actions

| Action | Suggested Owner | Target Sprint |
|--------|-----------------|---------------|
| CI matrix (Python 3.11 + 3.13, Ubuntu + Windows) | @devops | Sprint 5 |
| DEMO_MODEL mock pipeline for CI | @ml-eng | Sprint 5 |
| Branch-protection rules on `main` | @tech-lead | Sprint 5 |
| PR template with checklist | @tech-lead | Sprint 5 |
| Dependency audit schedule | @devops | Sprint 6 |

---

*Last updated: 2026-02-27*
