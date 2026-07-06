# MCPHub Group Picker

Workflow-first groups from `config/mcp-registry.json`. Local managed harnesses default to **`harness`** only, with per-server endpoints discoverable but disabled unless a harness-specific profile opts in.

## Default guidance

| Group | When to connect |
| --- | --- |
| `harness` | Default local baseline: bounded high-signal set with search, docs, llms.txt catalog (`llms-txt-explorer` `list_websites` only), URL fetch, package metadata, Chrome DevTools, and Penpot |
| `daily` | Routine opt-in expansion for broader repo, browser, and web reading |
| `coding` | Code-agent context: docs, URL fetch, repo, dependency, browser inspection, and full `jupyter-mcp-server` when JupyterLab is running |
| `research` | Web and reference research across search (including `open-websearch`), read, archive, wiki, `scrapling` scraping, and bounded `jupyter-mcp-server` notebook reads |
| `review` | Repo review, docs/source lookup, generated evidence, browser inspection, and bounded `jupyter-mcp-server` notebook reads |
| `release` | Release checks: versions, repo context, source reads, and package metadata |
| `personal-work` | Account-backed work suites — explicit user intent only |
| `media-work` | Document, 3D, and web-ingestion suites (`scrapling` for advanced page extraction); prefer **`/ffmpeg`** skill plus local CLIs for deterministic ffmpeg-style media transforms (not ffmpeg MCP by default) |
| `web-search` | Search APIs across Brave, DuckDuckGo, DDGS (metasearch/news), Tavily, Exa, Google search (`g-search`), and no-API-key multi-engine `open-websearch` |
| `web-read` | URL ingestion without search APIs (fetch, fetcher, trafilatura, wayback; bounded `open-websearch` fetch tools; bounded `scrapling` `get`/`bulk_get`) |
| `docs` | Library/framework documentation lookup plus full `llms-txt-explorer` (`check_website`, `list_websites`) |
| `repo` | Repo/dependency intelligence (repomix, package-version-check-mcp, ossinsight) |
| `browser` | Live Chrome automation (chrome-devtools) |
| `reasoning` | Hard problems only — three curated thinkers |
| `reasoning-lab` | Experimental thinking servers — opt-in |
| `media` | Document and 3D processing servers |
| `notebooks` | Jupyter notebook read/write and kernel execution (`jupyter-mcp-server`; requires user-owned JupyterLab + `JUPYTER_TOKEN` in `.env.mcphub`) |
| `design` | Design connectors |
| `productivity` | Productivity connectors |
| `accounts` | Account connectors — explicit user intent only |
| `references` | Academic/archive lookup (arxiv, wikipedia, wayback) |
| `shared-read` | Broad read-only shared surface (bounded `scrapling` `get`; bounded `open-websearch` search/fetch) |
| `credentialed` | API-key/OAuth-backed shared services (includes `jupyter-mcp-server` via `JUPYTER_TOKEN`) |
| `account-backed` | Personal/account-backed connectors |
| `live-browser` | Browser/session-bound connectors (`scrapling` sessions, stealth fetch) |
| `heavy` | High-output or high-runtime servers (`scrapling` browser spawn, `jupyter-mcp-server` kernel execution) |
| `experimental` | Bleeding-edge servers — opt-in (`open-websearch`, `scrapling`, `g-search`, …) |
| `tunnel` | **ChatGPT remote only** — not for local harness default |

## Decision flow

1. Routine local harness work → start with `harness`.
2. Broader dev flow → opt into `daily`, `coding`, `research`, `review`, or `release`.
3. Need a specific API shape → add a capability group instead of attaching everything blindly in the UI.
4. Sensitive/account tools → account-backed groups only when the user asked for that workflow.
5. ChatGPT connector → `tunnel` endpoint via public URL; do not mirror the global `/mcp` route remotely.
