#!/usr/bin/env sh
# lint-quick.sh — Run a fast static check on Python files.
# Safe to run even if no linter is installed.
# Usage: sh tools/lint-quick.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_FILES=$(find "$PROJECT_ROOT" -maxdepth 2 -name '*.py' -not -path '*/.venv/*' -not -path '*/__pycache__/*')

if [ -z "$PY_FILES" ]; then
    echo "No Python files found — nothing to lint."
    exit 0
fi

# Try flake8 first (preferred)
if command -v flake8 >/dev/null 2>&1; then
    echo "=== Running flake8 ==="
    # shellcheck disable=SC2086
    flake8 --max-line-length=120 --count --statistics $PY_FILES
    echo "flake8: done."
    exit 0
fi

# Fallback: pyflakes via python -m
if python -m pyflakes --version >/dev/null 2>&1; then
    echo "=== Running pyflakes (flake8 not found) ==="
    # shellcheck disable=SC2086
    python -m pyflakes $PY_FILES
    echo "pyflakes: done."
    exit 0
fi

# Fallback: py_compile (always available)
echo "=== Running py_compile (no linter found) ==="
echo "Tip: install flake8 for better checks:  pip install flake8"
ERRORS=0
for f in $PY_FILES; do
    if ! python -m py_compile "$f" 2>&1; then
        ERRORS=$((ERRORS + 1))
    fi
done

if [ "$ERRORS" -eq 0 ]; then
    echo "py_compile: all files OK."
else
    echo "py_compile: $ERRORS file(s) had errors."
    exit 1
fi
