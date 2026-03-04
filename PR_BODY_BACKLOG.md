## chore(backlog): finalize prompt templates, polish, and retrospective

### Summary
Completes the final three backlog cards — prompt templates & length control,
final polish & buffer, and retrospective — with documentation, a lint script,
11 new tests, and full Kanban alignment. No protected files were modified.

### Cards completed
| # | Card | Key file(s) |
|---|------|-------------|
| 1 | Refine prompt outputs & length control | `docs/prompt_templates.md`, `code-snippets/prompt_wrappers.txt` |
| 2 | Final polish & buffer | `docs/polish_checklist.md`, `docs/release_buffer.md`, `tools/lint-quick.sh` |
| 3 | Retrospective & lessons learned | `RETROSPECTIVE.md` |

### Tests
- **42 passed** in 30.42s (`pytest -q`)
- 11 new tests in `tests/test_backlog_final.py`
- No protected files modified

### How to verify
```bash
git checkout feature/backlog-finalize
pytest -q
cat KANBAN_BACKLOG_FINAL.md
```

### Files added (this branch only)
- `docs/prompt_templates.md` — prompt templates + length-control guide
- `code-snippets/prompt_wrappers.txt` — copy/paste prompt wrappers
- `docs/polish_checklist.md` — pre-release UI/accessibility checklist
- `docs/release_buffer.md` — runtime safeguards & rollback guidance
- `tools/lint-quick.sh` — quick lint script (flake8 → pyflakes → py_compile)
- `RETROSPECTIVE.md` — sprint retrospective with root causes & recommendations
- `tests/test_backlog_final.py` — deliverable existence tests
- `KANBAN_BACKLOG_FINAL.md` — Kanban card mapping
- `CLOSEOUT_BACKLOG.md` — run summary & verification steps
