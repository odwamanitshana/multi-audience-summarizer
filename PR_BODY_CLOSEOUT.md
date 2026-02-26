## chore(closeout): implement Kanban closeout tasks (docs, tests, QA, demo placeholder)

### Summary
This branch completes the six outstanding Kanban cards with documentation, test validation, and release tooling — without modifying any protected production files.

### Cards completed
| # | Card | Key file(s) |
|---|------|-------------|
| 1 | Examples & input size handling | `samples/examples_for_ui.txt`, `UI_HINTS.md` |
| 2 | requirements.txt & local run docs | `requirements.txt`, `RUNNING_LOCALLY.md` |
| 3 | HF Spaces guidance & DEMO_MODEL | `README.md` (appended) |
| 4 | QA & cross-browser checklist | `QA_CHECKLIST.md` |
| 5 | Demo assets placeholder & README | `assets/demo_placeholder.md`, `README.md` |
| 6 | Release checklist & packaging | `RELEASE.md` |

### Tests
- **31 passed** in 13.39s (`pytest -q`)
- No protected files modified

### How to verify
```bash
git checkout feature/kanban-closeout
pytest -q
cat KANBAN_UPDATE.md
```

### Files added/changed (this branch only)
- `samples/examples_for_ui.txt` (new)
- `UI_HINTS.md` (new)
- `RUNNING_LOCALLY.md` (new)
- `QA_CHECKLIST.md` (new)
- `RELEASE.md` (new)
- `CLOSEOUT_REPORT.md` (new)
- `requirements.txt` (appended dev pins)
- `README.md` (appended DEMO_MODEL, Demo, and guide links sections)
- `KANBAN_UPDATE.md` (rewritten for this branch)
