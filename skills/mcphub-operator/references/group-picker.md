# MCPHub Group Picker

Workflow-first groups from `config/mcp-registry.json`. Local managed harnesses project **all** groups plus per-server endpoints unless a harness-specific client override exists.

## Default guidance

| Group | When to connect |
| --- | --- |
| `daily` | Default local workhorse (search + docs + fetch + code-intel lite) |
| `search` | Need multiple search APIs (Brave, Tavily, DuckDuckGo) |
| `read-web` | URL ingestion without search APIs (fetch, fetcher, trafilatura, wayback) |
| `docs` | Library/framework documentation (context7, deepwiki) |
| `code-intel` | Repo/deps intelligence (repomix, package-version, ossinsight) |
| `references` | Academic/archive lookup (arxiv, wikipedia, wayback) |
| `browser` | Live Chrome automation (chrome-devtools) |
| `reasoning` | Hard problems only — three curated thinkers |
| `data-pipeline` | Heavy extract/transform (docling, ffmpeg, trafilatura) |
| `personal` | Account-backed connectors — explicit user intent only |
| `productivity` | GTD/design (supathings, penpot) |
| `experimental` | Bleeding-edge — opt-in |
| `repo-catalog` | Repo read-only catalog/docs MCP servers |
| `tunnel` | **ChatGPT remote only** — not for local harness default |
| `harness-safe` | Deprecated alias of `daily` |
| `all-managed` | Entire fleet meta-endpoint |

## Decision flow

1. Routine coding/research → start with `daily`.
2. Need a specific API shape → add `search`, `read-web`, or `docs` instead of attaching everything blindly in the UI.
3. Sensitive/account tools → `personal` only when the user asked for Gmail/LinkedIn workflows.
4. ChatGPT connector → `tunnel` endpoint via public URL; do not mirror full fleet remotely.