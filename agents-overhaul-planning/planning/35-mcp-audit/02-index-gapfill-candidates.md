# MCP Index Gap-Fill Candidates

## Discovery sources

- Official MCP Registry: https://modelcontextprotocol.io/registry/about
- PulseMCP: https://www.pulsemcp.com/servers
- MCP.Directory: https://mcp.directory/awesome-mcp-servers
- abordage/awesome-mcp: https://github.com/abordage/awesome-mcp
- Glama MCP list and MCP.so should be re-queried during implementation.

## High-value gap-fill domains

| Domain | Candidate examples | Why MCP may be justified | Notes |
|---|---|---|---|
| Browser automation | Playwright, Chrome DevTools | live DOM/browser/runtime state | Must sandbox and block secrets |
| GitHub/issue/PR | GitHub MCP | live repo/issue/PR state | GitHub official/reference candidates preferred |
| Docs lookup | OpenAI Docs MCP, Context7, AWS docs | current docs | Read-only preferred |
| DB/vector | Postgres, SQLite/DuckDB, Qdrant | live query/state | Read-only by default |
| Observability | Grafana/Sentry/AppSignal | live metrics/logs/traces | Secrets and tenancy risk |
| Cloud/infra | Kubernetes/Terraform/AWS/GCP/Azure | live infra state | High-risk; require least privilege |
| Search/research | Perplexity/Tavily/Exa/Brave | current web search | API key handling |
| File systems | filesystem MCP | local dynamic files | Usually replace with built-in tools or skill unless harness lacks file tools |

## Index-use policy

Indexes provide candidates and metadata, but adoption requires direct source review and conformance tests.
