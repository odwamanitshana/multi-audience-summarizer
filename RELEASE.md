# RELEASE.md — Release Checklist & Packaging Instructions

Follow these steps to cut a release of **Multi-Audience Summarizer**.

---

## Pre-release checklist

- [ ] All feature branches merged to `main`
- [ ] `pytest -q` passes (0 failures)
- [ ] GitHub Actions CI is green on `main`
- [ ] `requirements.txt` is up-to-date
- [ ] README.md has current instructions and demo assets
- [ ] KANBAN_UPDATE.md shows all cards as **Done**
- [ ] No `TODO` / `FIXME` left in production code (optional: search with `grep -rn "TODO\|FIXME" *.py`)
- [ ] CHANGELOG or PR description covers all changes since last release

---

## Step-by-step release process

### 1. Create a release branch (optional)

```bash
git checkout main
git pull origin main
git checkout -b release/vX.Y.Z
```

### 2. Run full test suite

```bash
# Activate venv first
pytest -q
# Expect: all tests passed
```

### 3. Verify the app runs

```bash
NO_PROXY="localhost,127.0.0.1" python app_gradio.py
# Open http://127.0.0.1:7860 — quick smoke test
# Ctrl+C to stop
```

### 4. Update version references (if any)

If the project uses a version string (e.g., in `__version__`), update it now:

```bash
# Example: update version in setup.py or pyproject.toml
# sed -i 's/version="0.0.1"/version="X.Y.Z"/' setup.py
```

### 5. Tag the release

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z — <short description>"
# Example:
git tag -a v0.1.0 -m "Release v0.1.0 — initial multi-audience summarizer with Gradio UI"
```

### 6. Push the tag

```bash
git push origin main
git push origin vX.Y.Z
# Or push all tags:
git push origin --tags
```

### 7. Create a GitHub Release (optional)

Using GitHub CLI:

```bash
gh release create vX.Y.Z \
  --title "v0.1.0 — Multi-Audience Summarizer" \
  --notes-file CHANGELOG.md \
  --draft
```

Or manually via GitHub → Releases → Draft a new release.

### 8. Produce a release zip (optional)

```bash
git archive --format=zip --prefix=multi-audience-summarizer-vX.Y.Z/ HEAD \
  > multi-audience-summarizer-vX.Y.Z.zip
```

On Windows (PowerShell):

```powershell
git archive --format=zip --prefix="multi-audience-summarizer-vX.Y.Z/" HEAD `
  -o "multi-audience-summarizer-vX.Y.Z.zip"
```

---

## Verification commands (run post-release)

```bash
# Verify tag exists
git tag -l "v*"

# Verify tag points to correct commit
git log --oneline -1 vX.Y.Z

# Clone fresh and test
git clone https://github.com/odwamanitshana/multi-audience-summarizer.git /tmp/release-test
cd /tmp/release-test
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

---

## Versioning scheme

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (X): Breaking changes to API or CLI
- **MINOR** (Y): New features, backward-compatible
- **PATCH** (Z): Bug fixes, documentation updates

### Suggested first release

```
v0.1.0 — Initial release
  - Multi-persona summarisation (executive, student, casual)
  - Gradio web UI with URL extraction, chunking, sentiment badges
  - Mocked test suite (31 tests)
  - GitHub Actions CI
  - Documentation (README, RUNNING_LOCALLY, QA_CHECKLIST)
```

---

## Rollback

If a release has critical issues:

```bash
# Delete the remote tag
git push --delete origin vX.Y.Z

# Delete the local tag
git tag -d vX.Y.Z

# Fix the issue on main, then re-tag
```

---

*Last updated: 2026-02-26*
