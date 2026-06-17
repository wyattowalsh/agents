"""Tests for composed MDX safety helpers."""

from wagents.docs_mdx_safety import (
    escape_composed_page_prose,
    has_legacy_quick_start,
    parse_composed_by,
    strip_duplicate_details_headings,
)


def test_parse_composed_by() -> None:
    text = '---\ncomposed_by: "compose-custom-wave-3"\n---\n'
    assert parse_composed_by(text) == "compose-custom-wave-3"


def test_has_legacy_quick_start() -> None:
    assert has_legacy_quick_start('<div class="quick-start">') is True
    assert has_legacy_quick_start("<SkillPageHeader />") is False


def test_escape_composed_page_prose_escapes_angle_brackets_outside_fences() -> None:
    page = "## Tab\n\nUse <pre> blocks carefully.\n\n```bash\necho <ok>\n```\n"
    out = escape_composed_page_prose(page)
    assert "&lt;pre&gt;" in out
    assert "echo <ok>" in out


def test_escape_composed_page_prose_preserves_jsx_closing_tags() -> None:
    page = "<CardGrid>\n  <LinkCard title=\"x\" href=\"/\" />\n</CardGrid>\n"
    out = escape_composed_page_prose(page)
    assert "</CardGrid>" in out
    assert "&lt;/CardGrid&gt;" not in out


def test_strip_duplicate_details_headings() -> None:
    page = (
        "## Dispatch\n\nAbove\n\n"
        '<details class="source-disclosure">\n<summary>Full</summary>\n\n'
        "## Dispatch\n\nInside\n\n"
        "</details>\n"
    )
    out = strip_duplicate_details_headings(page)
    assert "## Dispatch" in out
    assert "deduped" in out
    assert out.count("## Dispatch") == 1