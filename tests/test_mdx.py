"""Tests for wagents.rendering — MDX escaping functions."""

from wagents.rendering import (
    _extract_what_it_does,
    _sanitize_what_it_does,
    escape_mdx,
    escape_mdx_line,
    safe_outer_fence,
)

# ---------------------------------------------------------------------------
# escape_mdx_line
# ---------------------------------------------------------------------------


class TestEscapeMdxLine:
    def test_curly_braces_escaped(self):
        assert escape_mdx_line("use {x} here") == "use \\{x\\} here"

    def test_angle_bracket_escaped(self):
        assert escape_mdx_line("a < b") == "a &lt; b"

    def test_angle_brackets_in_table_cells_use_entities(self):
        line = '| **Analyze** ("analyze <url>", "analyze db") | `ref.md` | details |'
        result = escape_mdx_line(line)
        assert "\\<" not in result
        assert "&lt;url&gt;" in result

    def test_markdown_escaped_angle_brackets_normalized(self):
        line = '| ("analyze \\<url\\>", "db") | `ref.md` | details |'
        result = escape_mdx_line(line)
        assert "\\<" not in result
        assert "&lt;url&gt;" in result

    def test_inline_code_preserved(self):
        result = escape_mdx_line("text `{x}` more")
        assert result == "text `{x}` more"

    def test_double_backtick_code_preserved(self):
        result = escape_mdx_line("text ``{x}`` more")
        assert result == "text ``{x}`` more"

    def test_html_comment_to_jsx(self):
        result = escape_mdx_line("before <!-- comment --> after")
        assert result == "before {/* comment */} after"

    def test_import_line_escaped(self):
        result = escape_mdx_line("import React from 'react'")
        assert result == "\\import React from 'react'"

    def test_export_line_escaped(self):
        result = escape_mdx_line("export default App")
        assert result == "\\export default App"

    def test_plain_text_unchanged(self):
        assert escape_mdx_line("just plain text") == "just plain text"

    def test_mixed_braces_and_code(self):
        result = escape_mdx_line("{a} `{b}` {c}")
        assert result == "\\{a\\} `{b}` \\{c\\}"

    def test_inline_placeholder_code_is_mdx_safe_inside_tables(self):
        result = escape_mdx_line("| `research <harness|all>` | Ecosystem Research |")
        assert result == "| `research &lt;harness\\|all&gt;` | Ecosystem Research |"


# ---------------------------------------------------------------------------
# escape_mdx (full body with fenced code blocks)
# ---------------------------------------------------------------------------


class TestEscapeMdx:
    def test_fenced_code_block_not_escaped(self):
        body = "text {x}\n```\n{inside} <Tag>\n```\ntext {y}"
        result = escape_mdx(body)
        lines = result.split("\n")
        assert lines[0] == "text \\{x\\}"
        assert lines[1] == "```"
        assert lines[2] == "{inside} <Tag>"
        assert lines[3] == "```"
        assert lines[4] == "text \\{y\\}"

    def test_outside_fence_escaped(self):
        body = "# Title\n\n{value}"
        result = escape_mdx(body)
        assert "\\{value\\}" in result

    def test_empty_body(self):
        assert escape_mdx("") == ""

    def test_only_fenced_block(self):
        body = "```\n{x}\n```"
        result = escape_mdx(body)
        assert result == "```\n{x}\n```"


# ---------------------------------------------------------------------------
# _sanitize_what_it_does
# ---------------------------------------------------------------------------


class TestSanitizeWhatItDoes:
    def test_rejects_code_fence_fragments(self):
        text = "``` </python> import { createDeepAgent } from 'deepagents';"
        assert _sanitize_what_it_does(text) == ""

    def test_keeps_plain_summary(self):
        text = "Systematic skill discovery engine for gap analysis."
        assert _sanitize_what_it_does(text) == text

    def test_rejects_hash_toc_links(self):
        text = "## Contents - [Layers](#architectural-layers) - [Examples](#examples)"
        assert _sanitize_what_it_does(text) == ""

    def test_rejects_table_heavy_summary(self):
        text = "| a | b | c | d |"
        assert _sanitize_what_it_does(text) == ""


class TestExtractWhatItDoes:
    def test_skips_subheadings_and_tables(self):
        body = (
            "# AWS Serverless\n"
            "## Overview\n"
            "\n"
            "Domain expertise for serverless on AWS.\n"
            "\n"
            "## Routing\n"
            "| need | action |\n"
        )
        assert _extract_what_it_does(body) == "Domain expertise for serverless on AWS."

    def test_rejects_toc_paragraph(self):
        body = "# Flutter App\n## Contents\n- [Layers](#architectural-layers)\n"
        assert _extract_what_it_does(body) == ""


# ---------------------------------------------------------------------------
# safe_outer_fence
# ---------------------------------------------------------------------------


class TestSafeOuterFence:
    def test_no_inner_fences(self):
        # max_fence starts at 3, return is max_fence + 1 = 4 backticks
        assert safe_outer_fence("just text") == "````"

    def test_three_backtick_inner(self):
        content = "some\n```python\ncode\n```\nmore"
        result = safe_outer_fence(content)
        assert result == "````"

    def test_four_backtick_inner(self):
        content = "some\n````\ncode\n````\nmore"
        result = safe_outer_fence(content)
        assert result == "`````"

    def test_tilde_fence_inner(self):
        content = "some\n~~~\ncode\n~~~\nmore"
        result = safe_outer_fence(content)
        assert result == "````"

    def test_mixed_fences(self):
        content = "```\ncode\n```\n`````\nmore\n`````"
        result = safe_outer_fence(content)
        assert result == "``````"
