# Assumption and Drift Ledger

Generated: `2026-05-01T07:19:13Z`

## Latest public repo facts used for sync

The latest visible GitHub repository listing shows these top-level artifacts:

- `.agents/`, `.antigravity/`, `.cherry/`, `.claude-plugin`, `.claude`, `.codex-plugin`, `.cursor/`, `.github/`, `.opencode-plugin`, `.opencode`, `.perplexity/`
- `agents/`, `config/`, `docs/`, `hooks/`, `instructions/`, `mcp/`, `opencode-setup/`, `openspec/`, `platforms/`, `scripts/`, `skills/`, `tests/`, `wagents/`
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `agent-bundle.json`, `mcp.json`, `opencode.json`, `pyproject.toml`, `uv.lock`

Source: https://github.com/wyattowalsh/agents

## Drift categories

| Category | Detection method | Blocking? | Owner |
|---|---|---:|---|
| Planning references non-existent repo path | repo inventory vs docs grep | Yes | Repo Sync Team |
| Repo path lacks planning coverage | repo inventory vs docs artifact manifest | No, unless harness-critical | Docs Truth Team |
| Harness support overclaim | registry support tier vs README/docs claims | Yes | Harness Registry Team |
| MCP install uses absolute local path | `mcp.json` scanner | Yes for portable release | MCP Curation Team |
| Skill lacks spec-compliant frontmatter | skills validator | Yes | Skills Team |
| OpenSpec change references stale task IDs | OpenSpec task cross-check | Yes | OpenSpec Team |
| README stale vs generated catalog | `wagents readme --check` | Yes | Docs Team |
| External source stale or preview | source ledger freshness check | No, but must mark caveat | Research Team |

## Assumptions requiring validation

1. Existing OpenSpec artifacts are already present under `openspec/`; implementation must inventory and preserve them before generating new specs.
2. Current `mcp.json` is a central but not necessarily sole MCP source; per-harness MCP configs may exist in hidden harness folders.
3. The repo has both native plugin adapters and Agent Skills CLI fallback; support tiers must be generated from actual tests, not README intent.
4. The `npx skills` path is preferred for cross-agent skill install, but GitHub's `gh skill` may become a stronger option for Copilot-specific provenance, pinning, and preview flows.
5. Community MCP indexes are discovery leads only; promotion requires direct upstream docs/source review, license check, security scan, and conformance tests.

## Resolution rule

When planning docs and repo files disagree, live repo inventory wins. When community docs and official docs disagree, official docs win. When official docs mark a surface as beta/preview, the harness registry must mark it `experimental` or `planned-research-backed`, never `validated`.
