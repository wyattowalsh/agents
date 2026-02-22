"""Tests for wagents.parsing — frontmatter parsing, fence tracking, and text transforms."""

import pytest

from wagents.parsing import (
    FenceTracker,
    escape_attr,
    parse_frontmatter,
    shift_headings,
    strip_relative_md_links,
    to_title,
    truncate_sentence,
)

# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_valid_with_body(self, sample_skill_content):
        fm, body = parse_frontmatter(sample_skill_content)
        assert fm["name"] == "test-skill"
        assert fm["description"] == "A test skill"
        assert "Body here." in body

    def test_closing_dashes_at_eof(self):
        content = "---\nkey: value\n---"
        fm, body = parse_frontmatter(content)
        assert fm["key"] == "value"
        assert body == ""

    def test_missing_opening_dashes(self):
        with pytest.raises(ValueError, match="must start with '---'"):
            parse_frontmatter("key: value\n---\n")

    def test_missing_closing_dashes(self):
        with pytest.raises(ValueError, match="missing closing '---'"):
            parse_frontmatter("---\nkey: value\n")

    def test_empty_body(self):
        content = "---\nname: x\n---\n"
        fm, body = parse_frontmatter(content)
        assert fm["name"] == "x"
        assert body == ""

    def test_nested_yaml(self):
        content = "---\nmetadata:\n  author: alice\n  version: 1.0\n---\n\nSome body.\n"
        fm, body = parse_frontmatter(content)
        assert fm["metadata"]["author"] == "alice"
        assert fm["metadata"]["version"] == 1.0
        assert "Some body." in body


# ---------------------------------------------------------------------------
# FenceTracker
# ---------------------------------------------------------------------------


class TestFenceTracker:
    def test_open_and_close_backtick(self):
        ft = FenceTracker()
        assert not ft.inside_fence
        assert ft.update("```python") is True
        assert ft.inside_fence
        assert ft.update("some code") is False
        assert ft.inside_fence
        assert ft.update("```") is True
        assert not ft.inside_fence

    def test_open_and_close_tilde(self):
        ft = FenceTracker()
        assert ft.update("~~~") is True
        assert ft.inside_fence
        assert ft.update("~~~") is True
        assert not ft.inside_fence

    def test_nested_longer_fence_inside_shorter(self):
        """A longer fence inside a shorter one does NOT close the outer fence."""
        ft = FenceTracker()
        assert ft.update("```") is True
        assert ft.inside_fence
        # A 4-backtick line inside a 3-backtick fence closes it (>= count)
        assert ft.update("````") is True
        assert not ft.inside_fence

    def test_shorter_fence_does_not_close(self):
        """A shorter fence inside a longer one does NOT close the outer fence."""
        ft = FenceTracker()
        assert ft.update("````") is True
        assert ft.inside_fence
        # 3-backtick line cannot close a 4-backtick fence
        assert ft.update("```") is False
        assert ft.inside_fence
        assert ft.update("````") is True
        assert not ft.inside_fence

    def test_indented_fence_up_to_3_spaces(self):
        ft = FenceTracker()
        assert ft.update("   ```") is True
        assert ft.inside_fence
        assert ft.update("   ```") is True
        assert not ft.inside_fence

    def test_indented_4_spaces_not_fence(self):
        ft = FenceTracker()
        assert ft.update("    ```") is False
        assert not ft.inside_fence

    def test_mismatched_char_does_not_close(self):
        ft = FenceTracker()
        assert ft.update("```") is True
        assert ft.inside_fence
        # Tilde line cannot close a backtick fence
        assert ft.update("~~~") is False
        assert ft.inside_fence
        assert ft.update("```") is True
        assert not ft.inside_fence


# ---------------------------------------------------------------------------
# to_title
# ---------------------------------------------------------------------------


class TestToTitle:
    def test_kebab_case(self):
        assert to_title("my-skill") == "My Skill"

    def test_single_word(self):
        assert to_title("hello") == "Hello"

    def test_multiple_hyphens(self):
        assert to_title("one-two-three") == "One Two Three"


# ---------------------------------------------------------------------------
# truncate_sentence
# ---------------------------------------------------------------------------


class TestTruncateSentence:
    def test_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        result = truncate_sentence(text, 30)
        assert result == "First sentence."

    def test_word_boundary_with_ellipsis(self):
        text = "No sentence boundary here at all"
        result = truncate_sentence(text, 20)
        assert result.endswith("\u2026")
        assert len(result) <= 20

    def test_passthrough_when_short(self):
        text = "Short."
        assert truncate_sentence(text, 100) == "Short."

    def test_exclamation_boundary(self):
        text = "Wow! That is great."
        result = truncate_sentence(text, 10)
        assert result == "Wow!"


# ---------------------------------------------------------------------------
# strip_relative_md_links
# ---------------------------------------------------------------------------


class TestStripRelativeMdLinks:
    def test_relative_link_becomes_code(self):
        assert strip_relative_md_links("[foo](bar.md)") == "`foo`"

    def test_preserves_absolute_link(self):
        text = "[foo](https://example.com)"
        assert strip_relative_md_links(text) == text

    def test_preserves_absolute_http(self):
        text = "[foo](http://example.com)"
        assert strip_relative_md_links(text) == text

    def test_relative_with_anchor(self):
        assert strip_relative_md_links("[ref](docs.md#section)") == "`ref`"

    def test_multiple_links(self):
        text = "See [a](x.md) and [b](https://b.com) and [c](y.md)"
        result = strip_relative_md_links(text)
        assert result == "See `a` and [b](https://b.com) and `c`"


# ---------------------------------------------------------------------------
# escape_attr
# ---------------------------------------------------------------------------


class TestEscapeAttr:
    def test_ampersand(self):
        assert escape_attr("a&b") == "a&amp;b"

    def test_double_quote(self):
        assert escape_attr('a"b') == "a&quot;b"

    def test_angle_brackets(self):
        assert escape_attr("<b>") == "&lt;b&gt;"

    def test_all_entities(self):
        assert escape_attr('&"<>') == "&amp;&quot;&lt;&gt;"

    def test_no_escaping_needed(self):
        assert escape_attr("plain text") == "plain text"


# ---------------------------------------------------------------------------
# shift_headings
# ---------------------------------------------------------------------------


class TestShiftHeadings:
    def test_shift_level_1(self):
        result = shift_headings("# H1\n## H2\n### H3", levels=1)
        assert result == "## H1\n### H2\n#### H3"

    def test_shift_level_2(self):
        result = shift_headings("# H1", levels=2)
        assert result == "### H1"

    def test_fence_aware_headings_unchanged(self):
        body = "```\n# Not a heading\n```\n# Real heading"
        result = shift_headings(body, levels=1)
        lines = result.split("\n")
        assert lines[0] == "```"
        assert lines[1] == "# Not a heading"
        assert lines[2] == "```"
        assert lines[3] == "## Real heading"

    def test_non_heading_lines_unchanged(self):
        body = "Just text\n# Heading\nMore text"
        result = shift_headings(body, levels=1)
        assert result == "Just text\n## Heading\nMore text"

    def test_empty_body(self):
        assert shift_headings("", levels=1) == ""
