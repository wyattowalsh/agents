"""Tests for wagents.rendering — MDX escaping functions."""

from wagents.rendering import escape_mdx, escape_mdx_line, safe_outer_fence

# ---------------------------------------------------------------------------
# escape_mdx_line
# ---------------------------------------------------------------------------


class TestEscapeMdxLine:
    def test_curly_braces_escaped(self):
        assert escape_mdx_line("use {x} here") == "use \\{x\\} here"

    def test_angle_bracket_escaped(self):
        assert escape_mdx_line("a < b") == "a \\< b"

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
