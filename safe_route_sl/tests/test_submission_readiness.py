"""Static submission-readiness checks for documentation and Streamlit pages."""

from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent


def test_submission_documents_exist_and_readme_is_current() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "currently in Phase 1" not in readme
    assert "Toolkit Validation" in readme
    assert "SimpleAI is optional" in readme
    assert (PROJECT_ROOT / "SUBMISSION_CHECKLIST.md").is_file()
    assert (PROJECT_ROOT / "DEMO_SCRIPT.md").is_file()


def test_deprecated_streamlit_width_argument_is_removed() -> None:
    source_paths = (
        PROJECT_ROOT / "app.py",
        *sorted((PROJECT_ROOT / "pages").glob("*.py")),
        *sorted((PROJECT_ROOT / "visualizations").glob("*.py")),
    )

    assert all("use_container_width" not in path.read_text(encoding="utf-8") for path in source_paths)


def test_pages_are_valid_python_and_keep_the_educational_disclaimer() -> None:
    page_paths = (PROJECT_ROOT / "app.py", *sorted((PROJECT_ROOT / "pages").glob("*.py")))

    for path in page_paths:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        assert "Not for real emergency decision-making" in source


def test_each_application_page_explicitly_uses_the_wide_layout() -> None:
    for path in sorted((PROJECT_ROOT / "pages").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "st.set_page_config(" in source
        assert 'layout="wide"' in source


def test_interactive_page_uses_compact_top_spacing() -> None:
    source = (PROJECT_ROOT / "pages" / "1_Interactive_Simulation.py").read_text(encoding="utf-8")

    assert 'data-testid="stMainBlockContainer"' in source
    assert "padding-top: 1rem" in source
    assert 'class="safe-route-page-title"' in source
    assert "margin: 0.15rem 0 1.25rem !important" in source
    assert "padding: 0.45rem 0.75rem 0.45rem 1rem !important" in source
    assert "render_section_title(\"Controls\")" in source
    assert "render_section_title(\"Scenario View\")" in source
    assert "render_section_title(\"Results\")" in source
    assert 'st.expander("About and educational disclaimer")' in source


def test_problem_model_has_all_explicit_sections() -> None:
    source = (PROJECT_ROOT / "pages" / "3_Problem_Model.py").read_text(encoding="utf-8")
    required_sections = (
        "Problem Statement",
        "State-Space Model",
        "Initial State",
        "Goal State",
        "Actions",
        "Transition Model",
        "Goal Test",
        "Constraints",
        "Path-Cost Functions",
        "Heuristic",
        "Search Algorithm Properties",
        "Dataset",
        "Scenarios",
        "Toolkit Roles",
        "Limitations",
    )

    assert all(f'st.subheader("{section}")' in source for section in required_sections)


def test_gitignore_covers_generated_artifacts_and_virtual_environments() -> None:
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in ("__pycache__/", "*.py[cod]", ".pytest_cache/", ".coverage", ".venv/", ".DS_Store"):
        assert pattern in gitignore
