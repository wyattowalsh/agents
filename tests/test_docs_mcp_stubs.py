"""Tests for MCP registry docs stub generation."""

from __future__ import annotations

import json

from wagents.docs_mcp_stubs import (
    load_mcp_registry_servers,
    mcp_stub_catalog_gaps,
    render_mcp_stub_page,
    write_mcp_registry_stub_pages,
)


def test_load_mcp_registry_servers_has_thirty_three_entries():
    servers = load_mcp_registry_servers()
    assert len(servers) == 33
    assert "duckduckgo-search" in servers
    assert "mcphub" not in servers


def test_render_mcp_stub_page_includes_required_sentinels():
    servers = load_mcp_registry_servers()
    page = render_mcp_stub_page("brave-search", servers["brave-search"])
    assert "composed: true" in page
    assert "{/* HAND-MAINTAINED */}" in page
    assert '<Badge text="Search and Discovery"' in page
    assert '"command": "npx"' in page
    assert 'href="/mcp/"' in page
    assert 'href="/mcp/mcphub/"' in page
    assert "MCPHub routing" in page


def test_render_mcp_stub_page_notes_duckduckgo_alias():
    servers = load_mcp_registry_servers()
    page = render_mcp_stub_page("duckduckgo-search", servers["duckduckgo-search"])
    assert "duckduckgo-search" in page
    assert "Client key alias" in page
    assert "`duckduckgo`" in page


def test_mcp_stub_catalog_covers_all_registry_servers():
    assert mcp_stub_catalog_gaps() == []


def test_write_mcp_registry_stub_pages_skips_existing_mcphub(tmp_repo, monkeypatch):
    content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
    mcp_dir = content_dir / "mcp"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    (mcp_dir / "mcphub.mdx").write_text("{/* HAND-MAINTAINED */}\n", encoding="utf-8")

    registry = {
        "servers": {
            "sample-server": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "sample-mcp"],
                "enabled": True,
            },
            "mcphub": {
                "transport": "stdio",
                "command": "uv",
                "args": [],
                "enabled": True,
            },
        }
    }
    (tmp_repo / "config").mkdir(parents=True, exist_ok=True)
    (tmp_repo / "config" / "mcp-registry.json").write_text(json.dumps(registry), encoding="utf-8")

    import wagents.docs_mcp_stubs as stubs

    monkeypatch.setattr(stubs, "ROOT", tmp_repo)
    monkeypatch.setattr(stubs, "CONTENT_DIR", content_dir)
    monkeypatch.setattr(stubs, "MCP_REGISTRY_PATH", tmp_repo / "config" / "mcp-registry.json")
    monkeypatch.setattr(stubs, "MCP_DOCS_DIR", mcp_dir)

    written = write_mcp_registry_stub_pages()
    assert len(written) == 1
    assert (mcp_dir / "sample-server.mdx").exists()
    assert not (mcp_dir / "mcphub.mdx").read_text(encoding="utf-8").startswith("---")