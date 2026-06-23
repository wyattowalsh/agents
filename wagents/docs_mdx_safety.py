"""MDX safety helpers for composed catalog pages."""

from __future__ import annotations

import re

from wagents.docs_lint import DUPLICATE_SECTION_HEADINGS
from wagents.rendering import escape_mdx_line

_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
_COMPOSED_BY_RE = re.compile(r'^composed_by:\s*"?([^"\n]+)"?', re.M)
_LEGACY_QUICK_START = '<div class="quick-start">'
_SKILL_PAGE_HEADER = "SkillPageHeader"


def parse_composed_by(text: str) -> str | None:
    match = _COMPOSED_BY_RE.search(text)
    return match.group(1).strip() if match else None


def has_legacy_quick_start(text: str) -> bool:
    return _LEGACY_QUICK_START in text and _SKILL_PAGE_HEADER not in text


def _in_fenced_block(line: str, fence: str | None) -> tuple[str | None, bool]:
    stripped = line.lstrip()
    fence_match = _FENCE_RE.match(stripped)
    if fence_match:
        marker = fence_match.group(1)
        if fence is None:
            return marker, True
        if marker == fence:
            return None, False
        return fence, True
    return fence, fence is not None


def escape_composed_page_prose(page: str) -> str:
    """Escape raw angle brackets in prose lines outside fenced code blocks."""
    out: list[str] = []
    fence: str | None = None
    for line in page.splitlines():
        fence, in_fence = _in_fenced_block(line, fence)
        if in_fence:
            out.append(line)
            continue
        stripped = line.strip()
        if stripped.startswith(">"):
            out.append(line)
            continue
        if stripped == "/>":
            out.append(line)
            continue
        if line.startswith("import ") or (stripped.startswith("<") and stripped.endswith("/>")):
            out.append(line)
            continue
        if stripped.startswith("</") and stripped.endswith(">"):
            out.append(line)
            continue
        if (
            stripped.startswith("<")
            and not stripped.startswith("<!--")
            and any(
                tag in stripped
                for tag in (
                    "<Aside",
                    "<Tabs",
                    "<TabItem",
                    "<CardGrid",
                    "<LinkCard",
                    "<Steps",
                    "<details",
                    "</details>",
                    "<summary",
                    "</summary>",
                    "<SkillPageHeader",
                    "<McpClientSnippet",
                    "<Badge",
                    "<CatalogSkillFilter",
                    "<div",
                    "</div>",
                )
            )
        ):
            out.append(line)
            continue
        if ("<" in line or ">" in line) and "&lt;" not in line:
            line = escape_mdx_line(line)
        out.append(line)
    result = "\n".join(out)
    if page.endswith("\n"):
        result += "\n"
    return result


def strip_duplicate_details_headings(page: str) -> str:
    """Remove duplicate section headings inside collapsed details blocks."""
    outside, inside_blocks = _split_details_blocks(page)
    if not inside_blocks:
        return page
    cleaned_blocks: list[str] = []
    changed = False
    for block in inside_blocks:
        new_block = block
        for heading in DUPLICATE_SECTION_HEADINGS:
            if heading in outside and heading in new_block:
                new_block = new_block.replace(heading, f"<!-- deduped {heading.strip('# ')} -->")
                changed = True
        cleaned_blocks.append(new_block)
    if not changed:
        return page
    return _rebuild_details_blocks(page, cleaned_blocks)


def _split_details_blocks(text: str) -> tuple[str, list[str]]:
    outside: list[str] = []
    inside: list[str] = []
    in_details = False
    depth = 0
    current_inside: list[str] = []
    for line in text.splitlines():
        if re.match(r"<details\b", line, re.I):
            in_details = True
            depth += 1
            if depth == 1:
                current_inside = []
            outside.append(line)
            continue
        if in_details and re.match(r"</details>", line, re.I):
            depth -= 1
            if depth == 0:
                inside.append("\n".join(current_inside))
                in_details = False
            outside.append(line)
            continue
        if in_details and depth >= 1:
            current_inside.append(line)
        else:
            outside.append(line)
    return "\n".join(outside), inside


def _rebuild_details_blocks(page: str, cleaned_blocks: list[str]) -> str:
    parts = page.split("<details")
    if len(parts) <= 1:
        return page
    rebuilt = [parts[0]]
    block_iter = iter(cleaned_blocks)
    for chunk in parts[1:]:
        try:
            cleaned = next(block_iter)
        except StopIteration:
            rebuilt.append("<details" + chunk)
            continue
        close_idx = chunk.find(">")
        if close_idx < 0:
            rebuilt.append("<details" + chunk)
            continue
        header = "<details" + chunk[: close_idx + 1]
        rest = chunk[close_idx + 1 :]
        end_tag = "</details>"
        end_idx = rest.rfind(end_tag)
        if end_idx < 0:
            rebuilt.append("<details" + chunk)
            continue
        rebuilt.append(header + "\n" + cleaned + "\n" + end_tag + rest[end_idx + len(end_tag) :])
    return "".join(rebuilt)
