# ruff: noqa: E501
"""Generate hand-maintained MCP registry stub pages for the docs site."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

from wagents import CONTENT_DIR, ROOT
from wagents.docs_compose import is_composed_mdx
from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from wagents.parsing import escape_attr, truncate_sentence

if TYPE_CHECKING:
    from pathlib import Path

MCP_REGISTRY_PATH = ROOT / "config" / "mcp-registry.json"
MCP_DOCS_DIR = CONTENT_DIR / "mcp"
STUB_WAVE_ID = "docs-mcp-stubs"
GITHUB_REGISTRY_URL = (
    "https://github.com/wyattowalsh/agents/blob/main/config/mcp-registry.json"
)

_CATEGORY_VARIANTS = {
    "Thinking and Reasoning": "note",
    "Search and Discovery": "tip",
    "Web Fetching and Extraction": "caution",
    "Knowledge and Documentation": "success",
    "Development Tools": "danger",
    "Productivity": "default",
    "Media": "note",
    "Social": "tip",
}


@dataclass(frozen=True)
class McpServerCatalogEntry:
    category: str
    badge: str
    purpose: str


# Purposes and category badges aligned with docs/src/content/docs/mcp/index.mdx.
MCP_SERVER_CATALOG: dict[str, McpServerCatalogEntry] = {
    "sequential-thinking": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Analysis",
        "Step-by-step reasoning with revision and branching. The reference implementation from Anthropic for dynamic, reflective thought processes.",
    ),
    "atom-of-thoughts": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Synthesis",
        "Decomposes complex problems into atomic, independent thought units that can be contracted and combined for robust answers.",
    ),
    "shannon-thinking": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Information Theory",
        "Information-theoretic reasoning inspired by Claude Shannon. Reduces noise and uncertainty through systematic problem decomposition.",
    ),
    "structured-thinking": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Memory",
        "Captures, retrieves, and revises thoughts with persistent history. Supports tagging and relevance-based retrieval across sessions.",
    ),
    "cascade-thinking": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Deep Dive",
        "Multi-stage reasoning cascade that escalates through progressively deeper analysis levels when simpler passes are insufficient.",
    ),
    "crash": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Verification",
        "Constraint-satisfaction reasoning with strict mode toggle. Enforces logical consistency checking on intermediate conclusions.",
    ),
    "deep-lucid-3d": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Exploration",
        "Three-dimensional problem analysis exploring depth, breadth, and lateral connections. Includes creative exploration mode.",
    ),
    "lotus-wisdom-mcp": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Perspective",
        "Eastern-philosophy-inspired reasoning combining multiple perspectives and reflective synthesis for balanced conclusions.",
    ),
    "think-strategies": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Routing",
        "Strategy-selection toolkit that matches reasoning patterns to problem types. Session management for ongoing analysis threads.",
    ),
    "creative-thinking": McpServerCatalogEntry(
        "Thinking and Reasoning",
        "Ideation",
        "Lateral and divergent thinking techniques for brainstorming, ideation, and breaking out of conventional solution spaces.",
    ),
    "brave-search": McpServerCatalogEntry(
        "Search and Discovery",
        "Web/Local",
        "Brave Search API with web, news, image, video, and local search. Includes AI-powered summarization of search results.",
    ),
    "exa": McpServerCatalogEntry(
        "Search and Discovery",
        "Neural Search",
        "Neural search engine that understands meaning, not just keywords. Optimized for finding technical content, papers, and documentation.",
    ),
    "g-search": McpServerCatalogEntry(
        "Search and Discovery",
        "Google",
        "Google Search results via SerpAPI. Familiar ranking and broad coverage across the public web.",
    ),
    "duckduckgo-search": McpServerCatalogEntry(
        "Search and Discovery",
        "Privacy First",
        "Privacy-focused web search via DuckDuckGo. No tracking, no API key required.",
    ),
    "arxiv": McpServerCatalogEntry(
        "Search and Discovery",
        "Academic",
        "arXiv paper search and metadata retrieval for research workflows, including direct access to paper IDs and summaries.",
    ),
    "wikipedia": McpServerCatalogEntry(
        "Search and Discovery",
        "Encyclopedic",
        "Wikipedia content retrieval and lookup tools for encyclopedic background, entities, and topic overviews.",
    ),
    "wayback": McpServerCatalogEntry(
        "Search and Discovery",
        "Archive",
        "Access archived pages from the Internet Archive Wayback Machine for historical snapshots and link recovery.",
    ),
    "tavily": McpServerCatalogEntry(
        "Search and Discovery",
        "Research",
        "Tavily-powered web search, extraction, crawl, and deep-research workflows for current-event and multi-source investigations.",
    ),
    "fetch": McpServerCatalogEntry(
        "Web Fetching and Extraction",
        "HTTP Fetch",
        "Core URL fetcher from the MCP reference servers. Retrieves web pages and returns content in multiple formats.",
    ),
    "fetcher": McpServerCatalogEntry(
        "Web Fetching and Extraction",
        "JS Rendering",
        "Browser-based URL fetcher with JavaScript rendering. Handles SPAs and dynamic content that simple HTTP fetches miss.",
    ),
    "trafilatura": McpServerCatalogEntry(
        "Web Fetching and Extraction",
        "Content Extraction",
        "High-quality web content extraction using the Trafilatura library. Strips boilerplate to return clean article text and metadata.",
    ),
    "context7": McpServerCatalogEntry(
        "Knowledge and Documentation",
        "API Docs",
        "Retrieves up-to-date documentation for libraries and frameworks directly from source. Eliminates hallucinated APIs and outdated references.",
    ),
    "deepwiki": McpServerCatalogEntry(
        "Knowledge and Documentation",
        "GitHub Wikis",
        "Queries the DeepWiki knowledge base of open-source project documentation. Ask questions about repos and read generated wiki pages.",
    ),
    "repomix": McpServerCatalogEntry(
        "Knowledge and Documentation",
        "Codebase Context",
        "Packs entire codebases into AI-friendly context. Supports local directories and remote repositories with grep and directory browsing.",
    ),
    "ossinsight": McpServerCatalogEntry(
        "Knowledge and Documentation",
        "OSS Analytics",
        "Open-source project analytics via the OSSInsight public API. Useful for repository trends and ecosystem research with public rate limits.",
    ),
    "chrome-devtools": McpServerCatalogEntry(
        "Development Tools",
        "CDP Automation",
        "Chrome DevTools Protocol automation via Puppeteer. Navigate, click, fill forms, trace performance, inspect network requests, and take screenshots. Requires Node.js v22+.",
    ),
    "package-version": McpServerCatalogEntry(
        "Development Tools",
        "Dependency Mgmt",
        "Checks latest versions across npm, PyPI, Go, Maven, Gradle, Swift, Docker, Bedrock models, and GitHub Actions.",
    ),
    "docling": McpServerCatalogEntry(
        "Development Tools",
        "Doc Processing",
        "Converts documents (PDF, DOCX, PPTX, HTML) into structured Docling format. Create, edit, search, and export documents as Markdown.",
    ),
    "penpot": McpServerCatalogEntry(
        "Development Tools",
        "Design UI",
        "Remote MCP bridge to Penpot design files for UI review, asset inspection, and design-to-code workflows.",
    ),
    "gmail": McpServerCatalogEntry(
        "Productivity",
        "Inbox Zero",
        "Full Gmail access: search, read, send, draft, label, filter, and batch-manage emails. Supports attachment downloads.",
    ),
    "supathings": McpServerCatalogEntry(
        "Productivity",
        "Things 3",
        "Local Things 3 task and project management on macOS through SupaThings MCP. Treat as personal data with write-capable tools.",
    ),
    "ffmpeg": McpServerCatalogEntry(
        "Media",
        "Video Processing",
        "Video and audio processing via FFmpeg. Get info, clip, scale, concatenate, overlay, extract frames, and play media files.",
    ),
    "linkedin": McpServerCatalogEntry(
        "Social",
        "Professional Data",
        "LinkedIn profile scraping for professional networking data. Extract public profile information and connections.",
    ),
}


def load_mcp_registry_servers() -> dict[str, dict[str, Any]]:
    """Return the managed server map from config/mcp-registry.json."""
    data = json.loads(MCP_REGISTRY_PATH.read_text(encoding="utf-8"))
    servers = data.get("servers", {})
    if not isinstance(servers, dict):
        return {}
    return {str(name): entry for name, entry in servers.items() if isinstance(entry, dict)}


def _catalog_entry(server_id: str) -> McpServerCatalogEntry:
    entry = MCP_SERVER_CATALOG.get(server_id)
    if entry is not None:
        return entry
    return McpServerCatalogEntry(
        "Managed MCP",
        "Registry",
        f"Managed MCP server `{server_id}` from config/mcp-registry.json.",
    )


def _registry_env_block(env_spec: dict[str, Any]) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for key, value in env_spec.items():
        if not isinstance(value, dict):
            continue
        if "env_var" in value:
            rendered[key] = f"${{{value['env_var']}}}"
        elif "value" in value:
            rendered[key] = str(value["value"])
    return rendered


def registry_connection_snippet(server_id: str, server_config: dict[str, Any]) -> dict[str, Any]:
    """Build a representative stdio client block from registry command/args/env."""
    server: dict[str, Any] = {
        "command": server_config.get("command", ""),
        "args": list(server_config.get("args") or []),
    }
    env_spec = server_config.get("env")
    if isinstance(env_spec, dict) and env_spec:
        server["env"] = _registry_env_block(env_spec)
    return {"mcpServers": {server_id: server}}


def _category_variant(category: str) -> str:
    return _CATEGORY_VARIANTS.get(category, "note")


def _duckduckgo_alias_aside(server_id: str) -> str:
    if server_id != "duckduckgo-search":
        return ""
    return (
        '<Aside type="caution" title="Client key alias">\n'
        "Registry and MCPHub use server key `duckduckgo-search`, while several client examples on "
        "[MCP Overview](/mcp/) use the shorter key `duckduckgo` with the same `uvx duckduckgo-mcp-server` launch command.\n"
        "</Aside>\n\n"
    )


def render_mcp_stub_page(server_id: str, server_config: dict[str, Any]) -> str:
    """Render a composed HAND-MAINTAINED MCP registry stub page."""
    catalog = _catalog_entry(server_id)
    description = truncate_sentence(catalog.purpose, 200)
    category_variant = _category_variant(catalog.category)
    transport = str(server_config.get("transport") or "stdio")
    snippet = registry_connection_snippet(server_id, server_config)
    composed_at = date.today().isoformat()

    parts = [
        "---",
        f'title: "{escape_attr(server_id)}"',
        f'description: "{escape_attr(description)}"',
        'page_kind: "mcp"',
        'source_kind: "registry"',
        f'asset_id: "{escape_attr(server_id)}"',
        "composed: true",
        "docs_density: standard",
        f'composed_by: "{STUB_WAVE_ID}"',
        f'composed_at: "{composed_at}"',
        "---",
        "",
        HAND_MAINTAINED_SENTINEL,
        "",
        "import { Badge, Aside, CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        (
            f'<Badge text="MCP" variant="note" /> '
            f'<Badge text="{escape_attr(catalog.category)}" variant="{category_variant}" /> '
            f'<Badge text="{escape_attr(catalog.badge)}" variant="default" /> '
            f'<Badge text="{escape_attr(transport)}" variant="note" />'
        ),
        "",
        f"> {catalog.purpose}",
        "",
        '<Aside type="note" title="Registry MCP server (hand-maintained)">',
        f"Composed {STUB_WAVE_ID} from `config/mcp-registry.json`. ",
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel).",
        "</Aside>",
        "",
        '<Aside type="note" title="MCPHub routing">',
        "When MCPHub is enabled, clients can reach this server at ",
        f"`http://127.0.0.1:46683/mcp/{server_id}` via the local control plane. ",
        "See [MCPHub](/mcp/mcphub/) for the repo-owned metadata server and launch details.",
        "</Aside>",
        "",
        _duckduckgo_alias_aside(server_id),
        "## Registry Connection",
        "",
        "Representative stdio launch block from `config/mcp-registry.json`:",
        "",
        "```json",
        json.dumps(snippet, indent=2),
        "```",
        "",
        "## Registry Entry",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| id | `{server_id}` |",
        f"| transport | `{transport}` |",
        f"| command | `{server_config.get('command', '')}` |",
        f"| enabled | `{server_config.get('enabled', True)}` |",
        "",
        "## Resources",
        "",
        "<CardGrid>",
        '  <LinkCard title="MCP Overview" href="/mcp/" description="Browse all MCP servers by category." />',
        '  <LinkCard title="MCPHub" href="/mcp/mcphub/" description="Local MCP control-plane and endpoint routing." />',
        '  <LinkCard title="MCP Registry" href="/harness-config/mcp-registry/" description="Full registry schema, groups, and client projections." />',
        "</CardGrid>",
        "",
        "---",
        f"[View registry on GitHub]({GITHUB_REGISTRY_URL})",
        "",
    ]
    return "\n".join(parts)


def _should_skip_repo_owned_page(server_id: str) -> bool:
    if server_id != "mcphub":
        return False
    page = MCP_DOCS_DIR / "mcphub.mdx"
    return page.exists()


def write_mcp_registry_stub_pages(*, dry_run: bool = False) -> list[str]:
    """Write registry stub pages under docs/src/content/docs/mcp/.

    Skips mcphub when a repo-owned page already exists and preserves any
    existing hand-maintained MDX files.
    """
    servers = load_mcp_registry_servers()
    MCP_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    for server_id in sorted(servers):
        if _should_skip_repo_owned_page(server_id):
            continue

        out_path: Path = MCP_DOCS_DIR / f"{server_id}.mdx"
        rel = out_path.relative_to(ROOT)
        if out_path.exists():
            try:
                if is_composed_mdx(out_path.read_text(encoding="utf-8")):
                    continue
            except OSError:
                pass

        content = render_mcp_stub_page(server_id, servers[server_id])
        if not dry_run:
            out_path.write_text(content, encoding="utf-8")
        written.append(str(rel))

    return written


def mcp_stub_catalog_gaps() -> list[str]:
    """Return registry server IDs missing catalog purpose metadata."""
    servers = load_mcp_registry_servers()
    return sorted(server_id for server_id in servers if server_id not in MCP_SERVER_CATALOG)