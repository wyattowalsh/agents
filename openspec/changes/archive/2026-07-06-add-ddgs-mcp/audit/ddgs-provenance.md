# DDGS MCP provenance audit

**Date:** 2026-07-04  
**Package:** [ddgs-mcp-server](https://pypi.org/project/ddgs-mcp-server/) **0.5.1**  
**Source:** [chirag127/ddgs-mcp-server](https://github.com/chirag127/ddgs-mcp-server)  
**License:** MIT (`LICENSE` in package)

## Launch

```bash
uvx ddgs-mcp-server
```

Transport: stdio. No API key required (`auth_policy: none`).

## Tools

- `search_text` — metasearch (bing, brave, duckduckgo, google, mojeek, yahoo, yandex, wikipedia); optional `fetch_full_content`
- `search_news` — news search

## Dependencies (PyPI)

- `ddgs>=9.10.0`, `httpx>=0.27.0`, `mcp>=1.0.0`, `trafilatura>=2.0.0`

## Risks

- Small upstream footprint (~1 GitHub star at audit time).
- Scraping/metasearch egress; rate limits possible.
- `fetch_full_content` increases latency and MCP tool payload size.

## Gate decision

**Proceed** — credential-free stdio server matches existing `duckduckgo-search` class; smoke install via `uvx` succeeded.