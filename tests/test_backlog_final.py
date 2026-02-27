"""Non-invasive tests for the backlog-finalize deliverables.

Verifies that required documentation files exist and contain expected
content markers. No model downloads, no protected-file modifications.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestBacklogDeliverables:
    """Confirm all backlog-finalize artifacts are present."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "docs/prompt_templates.md",
            "code-snippets/prompt_wrappers.txt",
            "docs/polish_checklist.md",
            "docs/release_buffer.md",
            "tools/lint-quick.sh",
            "RETROSPECTIVE.md",
        ],
    )
    def test_file_exists(self, rel_path: str) -> None:
        path = PROJECT_ROOT / rel_path
        assert path.exists(), f"Missing deliverable: {rel_path}"
        assert path.stat().st_size > 50, f"File too small (likely empty): {rel_path}"

    def test_prompt_templates_has_five_templates(self) -> None:
        text = (PROJECT_ROOT / "docs/prompt_templates.md").read_text(encoding="utf-8")
        # Each template section starts with "### 1.N"
        template_count = text.count("### 1.")
        assert template_count >= 5, (
            f"Expected ≥5 prompt templates (### 1.x headings), found {template_count}"
        )

    def test_prompt_templates_has_length_control(self) -> None:
        text = (PROJECT_ROOT / "docs/prompt_templates.md").read_text(encoding="utf-8")
        assert "Length" in text or "length" in text, "Missing length-control section"
        assert "72" in text, "Missing 72-char commit-subject limit reference"

    def test_prompt_wrappers_has_wrappers(self) -> None:
        text = (PROJECT_ROOT / "code-snippets/prompt_wrappers.txt").read_text(encoding="utf-8")
        for tag in ["[SHORT]", "[DETAILED]", "[COMPACT]", "[COMMIT]", "[PR-BODY]"]:
            assert tag in text, f"Missing wrapper tag: {tag}"

    def test_retrospective_has_top_issues(self) -> None:
        text = (PROJECT_ROOT / "RETROSPECTIVE.md").read_text(encoding="utf-8")
        assert "Top 5" in text or "Top Five" in text, "Missing top-issues section"
        assert "Recommendations" in text, "Missing recommendations section"

    def test_lint_script_is_shell(self) -> None:
        text = (PROJECT_ROOT / "tools/lint-quick.sh").read_text(encoding="utf-8")
        assert text.startswith("#!/"), "lint-quick.sh missing shebang line"
