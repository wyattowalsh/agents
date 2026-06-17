"""Surgical regen of harness-config JSON embeds from config/*.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from wagents import ROOT
from wagents.rendering import safe_outer_fence

CONFIG_DIR = ROOT / "config"
HARNESS_CONFIG_DIR = ROOT / "docs" / "src" / "content" / "docs" / "harness-config"
_CONFIG_STEM_TO_JSON = {
    "mcp-registry": "mcp-registry.json",
    "sync-manifest": "sync-manifest.json",
    "tooling-policy": "tooling-policy.json",
}
_MCP_SNIPPET_IMPORT = (
    "import McpClientSnippet from '../../../components/McpClientSnippet.astro';"
)
_MCP_SNIPPET_SECTION = """## Client snippets

Example MCP client blocks for commonly referenced servers:

<McpClientSnippet serverKey="chrome-devtools" chromeRepoPath="${REPO_ROOT}" />

<McpClientSnippet serverKey="brave-search" package="brave-search-mcp" />

"""


@dataclass(frozen=True)
class RegenResult:
    written: int
    skipped: int
    paths: list[str]


def build_mcp_registry_snippet_section() -> str:
    return _MCP_SNIPPET_SECTION


def regen_config_embed(page_text: str, *, config_path: Path, summary: str) -> str:
    """Replace the JSON fenced block inside the source-disclosure details."""
    raw = config_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
        formatted = json.dumps(payload, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        formatted = raw
    fence = safe_outer_fence(formatted)
    try:
        rel = config_path.relative_to(ROOT)
    except ValueError:
        rel = config_path.name
    block = (
        f'<details class="source-disclosure">\n'
        f"<summary>{summary}</summary>\n\n"
        f'{fence}json title="{rel}"\n'
        f"{formatted}\n"
        f"{fence}\n\n"
        f"</details>"
    )
    start = page_text.find('<details class="source-disclosure">')
    if start < 0:
        return page_text
    end = page_text.find("</details>", start)
    if end < 0:
        return page_text
    return page_text[:start] + block + page_text[end + len("</details>") :]


def _ensure_mcp_snippets(page_text: str) -> str:
    page_text = page_text.replace(
        "import McpClientSnippet from '../../../../components/McpClientSnippet.astro';",
        _MCP_SNIPPET_IMPORT,
    )
    if _MCP_SNIPPET_IMPORT not in page_text:
        marker = "import { Badge"
        if marker in page_text:
            page_text = page_text.replace(marker, f"{_MCP_SNIPPET_IMPORT}\n{marker}", 1)
    insert_at = page_text.find("## Key Fields")
    if insert_at < 0:
        insert_at = page_text.find("<details class=\"source-disclosure\">")
    if insert_at < 0:
        return page_text + "\n\n" + build_mcp_registry_snippet_section()
    return page_text[:insert_at] + build_mcp_registry_snippet_section() + page_text[insert_at:]


def regen_config_page(stem: str) -> str | None:
    json_name = _CONFIG_STEM_TO_JSON.get(stem)
    if json_name is None:
        return None
    page_path = HARNESS_CONFIG_DIR / f"{stem}.mdx"
    config_path = CONFIG_DIR / json_name
    if not page_path.exists() or not config_path.exists():
        return None
    page = page_path.read_text(encoding="utf-8")
    summary = f"Full registry ({config_path.relative_to(ROOT).as_posix()})"
    if stem == "sync-manifest":
        summary = f"Full manifest ({config_path.relative_to(ROOT).as_posix()})"
    elif stem == "tooling-policy":
        summary = f"Full policy ({config_path.relative_to(ROOT).as_posix()})"
    page = regen_config_embed(page, config_path=config_path, summary=summary)
    if stem == "mcp-registry":
        page = _ensure_mcp_snippets(page)
    return page


def regen_configs_batch(
    *,
    config_stems: list[str] | None = None,
    dry_run: bool = False,
) -> RegenResult:
    stems = config_stems or list(_CONFIG_STEM_TO_JSON.keys())
    written = 0
    skipped = 0
    paths: list[str] = []
    for stem in stems:
        content = regen_config_page(stem)
        if content is None:
            skipped += 1
            continue
        rel = HARNESS_CONFIG_DIR / f"{stem}.mdx"
        paths.append(str(rel.relative_to(ROOT)))
        if not dry_run:
            rel.write_text(content, encoding="utf-8")
        written += 1
    return RegenResult(written=written, skipped=skipped, paths=paths)