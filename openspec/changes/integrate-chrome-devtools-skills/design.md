# Design

## Approach

Use a hybrid integration model. Plugin-capable harnesses consume upstream plugin or extension behavior. Repo-managed skills carry adapted upstream guidance into all portable skill surfaces. The canonical MCP registry remains the fallback for MCP-only harnesses, with dedupe rules preventing two active Chrome DevTools MCP sources in the same harness.

## Upstream Intake

- Source repository: `https://github.com/ChromeDevTools/chrome-devtools-mcp`
- Upstream skills path: `skills/`
- Inspected upstream commit: `a90378adf3226e8b27a05cdcfdd801c199acaa93`
- Package: `chrome-devtools-mcp`
- Version: `0.23.0`
- Author: `Google LLC`
- License: `Apache-2.0`
- MCP package name: `io.github.ChromeDevTools/chrome-devtools-mcp`
- Node engine: `^20.19.0 || ^22.12.0 || >=23`

## Skill Mapping

| Upstream Skill | Repo Skill | Notes |
|----------------|------------|-------|
| `chrome-devtools` | `chrome-devtools` | Preserve canonical broad workflow name. |
| `chrome-devtools-cli` | `chrome-devtools-cli` | Preserve CLI workflow name. |
| `a11y-debugging` | `chrome-devtools-a11y-debugging` | Prefix to avoid generic accessibility namespace collision. |
| `debug-optimize-lcp` | `chrome-devtools-debug-optimize-lcp` | Prefix to clarify DevTools-specific LCP workflow. |
| `memory-leak-debugging` | `chrome-devtools-memory-leak-debugging` | Prefix to clarify browser/Node memory workflow. |
| `troubleshooting` | `chrome-devtools-troubleshooting` | Prefix to avoid generic troubleshooting collision. |

Each skill must include valid repo frontmatter, `license: Apache-2.0`, `metadata.author: Google LLC`, `metadata.version: 0.23.0`, and a provenance section with source URL, commit SHA, access date, and adaptation notes.

## Harness Source Ownership

| Harness | Source | Active MCP Owner | Notes |
|---------|--------|------------------|-------|
| Claude Code | `plugin` | Upstream plugin | Install with `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp` then `/plugin install chrome-devtools-mcp`. |
| Gemini CLI | `extension` | Upstream extension | Install with `gemini extensions install --auto-update https://github.com/ChromeDevTools/chrome-devtools-mcp`. |
| GitHub Copilot Web / VS Code | `plugin` where source plugin is supported, otherwise `repo-mcp` | Plugin or repo MCP, not both | Source plugin path is `https://github.com/ChromeDevTools/chrome-devtools-mcp`. |
| Claude Desktop | `repo-mcp` or `manual-ui` | Repo MCP | Uses global app config or connector UI as supported. |
| ChatGPT | `manual-ui` or `repo-mcp` | Manual UI or repo MCP | Connector UI remains a blind spot; document manual import if needed. |
| Codex | `repo-mcp` | Repo MCP | Skills projected from repo `skills/`. |
| OpenCode | `repo-mcp` | Local wrapper override | Preserve wrapper-backed `chrome-devtools` launch. |
| Cursor | `repo-mcp` | Repo MCP | Do not claim plugin support without verification. |
| Antigravity | `repo-mcp` | Repo MCP | Uses Gemini-compatible surfaces where available. |
| Perplexity Desktop | `manual-ui` or `repo-mcp` | Manual UI or repo skill/preset | App connector and Computer Skills storage are blind spots. |
| Cherry Studio | `repo-mcp` | Repo MCP preset | Uses generated import presets. |

## MCP Hardening

- Preserve the current headed persistent-profile default in `config/mcp-registry.json` and shared docs.
- Preserve the OpenCode-specific browser URL wrapper documented in `instructions/opencode-global.md`.
- Disable usage statistics for repo-managed launches with `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS=1` or equivalent supported flag.
- Disable update checks for deterministic automation with `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS=1`.
- Decide whether repo-managed launches should use `--no-performance-crux`; if not disabled by default, document that performance traces may consult CrUX.
- Keep browser profile paths out of adapted skills except where the canonical repo config already documents them.

## Dedupe Model

- Add a registry field that records the Chrome DevTools source type per harness.
- Treat `plugin` and `extension` as authoritative MCP owners for that harness.
- During sync, suppress standalone `chrome-devtools` MCP projection for harnesses where the registry marks plugin or extension ownership.
- Keep skills projected independently unless the harness plugin is known to provide skills natively and duplicate skills create a concrete problem.

## Alternatives Rejected

- Install only the upstream skills: rejected because the user explicitly requires the upstream plugin too.
- Install only the plugin: rejected because many target harnesses do not have verified plugin support and still need repo skills or MCP fallback.
- Rename every upstream skill exactly as upstream: rejected because generic names like `troubleshooting` and `memory-leak-debugging` collide with broader repo skill namespaces.
- Edit generated harness surfaces directly: rejected by repo policy; source-of-truth files and generators must drive generated output.

## Migration Or Compatibility Notes

- Existing users of the `chrome-devtools` MCP server should keep working through the canonical registry unless their harness is upgraded to plugin or extension ownership.
- Existing OpenCode users should retain the local wrapper that reuses a dedicated Chrome endpoint on `127.0.0.1:9333`.
- Existing dirty worktree changes must be left intact; implementation should touch only files needed for this change.
