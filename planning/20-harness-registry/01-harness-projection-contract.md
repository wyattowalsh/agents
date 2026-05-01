# Harness Projection Contract

## Purpose

This contract defines how canonical repo assets project into harness-specific surfaces. Child lanes should implement fixtures from this contract instead of creating one-off adapter behavior.

## Canonical Inputs

| Canonical Input | Owner | Projects To |
|---|---|---|
| `AGENTS.md` and `instructions/global.md` | docs/instructions lane | Harness instructions, generated bridge files, global symlinks where supported. |
| `skills/` | skills lifecycle lane | Skill installs, symlinked skill entries, generated skill inventories, docs pages. |
| `agents/` | agent conventions lane | Harness-native agent definitions only where supported. |
| `mcp.json` and `config/mcp-registry.json` | MCP audit lane | Project/global MCP profiles, desktop MCP imports, smoke fixtures. |
| `config/sync-manifest.json` | registry/config safety lanes | Managed surface inventory, canonical/generated/merged/symlink modes. |
| `config/tooling-policy.json` | registry/config safety lanes | Model and provider policy where repo-managed harnesses allow it. |
| `agent-bundle.json` | release/docs/harness lanes | Bundle adapters, install/update commands, supported-agent list. |
| `.claude-plugin/`, `.codex-plugin/`, `.opencode-plugin/` | harness/plugin lanes | Native plugin projections from repo root. |
| `openspec/` | OpenSpec workflow lane | Change governance, generated downstream OpenSpec artifacts. |

## Projection Matrix

| Harness | Instructions | Skills | Agents | MCP | Plugins/Extensions | Hooks/Guards | UI/Telemetry |
|---|---|---|---|---|---|---|---|
| Claude Code | `CLAUDE.md`/repo instructions bridge | Skills CLI/native plugin | Claude subagents if present | Project/user MCP via settings | `.claude-plugin/` marketplace | Claude hooks/settings | Session telemetry planned |
| Claude Desktop | Desktop prompt behavior is a blind spot | No default skill projection claim | No default agent projection claim | Global desktop MCP config | Desktop extensions unknown | Desktop config safety only | Desktop-specific telemetry unknown |
| ChatGPT | Custom instructions/project instructions are blind spots | ChatGPT Apps/skills require separate verification | GPT/agent surface unknown | ChatGPT MCP connector config | Apps SDK/widgets, if verified | Unknown | App interaction telemetry unknown |
| Codex | `AGENTS.md`, Codex config, plugin instructions | Skills CLI/plugin adapter | Codex plugin/agent support by fixture | Codex MCP config | `.codex-plugin/` marketplace | Codex hooks | Session telemetry planned |
| GitHub Copilot Web | `.github/copilot-instructions.md`, prompts | Do not fabricate installed-skill support | Copilot coding agents/prompts | Copilot MCP config if supported | GitHub app/native surfaces unknown | GitHub hooks generated only where supported | Web task telemetry blind spot |
| GitHub Copilot CLI | Global Copilot config/instructions | Symlinked skills only when CLI supports discovery | CLI agents config | CLI MCP config | CLI extensions unknown | CLI env/guard surfaces | CLI telemetry blind spot |
| OpenCode | `opencode.json`, `instructions/opencode-global.md`, AGENTS | `skill` path and Skills CLI | OpenCode agents/modes if repo-owned | OpenCode MCP registry/launcher | npm plugins and `.opencode-plugin/` | credential guard, approval notify | DCP, statusline, quota, scheduler |
| Gemini CLI | `GEMINI.md` and global Gemini settings | Skills CLI/symlinked skills | Gemini agents if supported | Gemini MCP settings | Gemini extensions/OpenSpec artifacts | Settings and hooks where supported | Telemetry planned |
| Antigravity | Gemini-compatible instructions, distinct support caveats | Skills CLI if supported | Antigravity agents unknown | Antigravity MCP config paths | Antigravity extensions | Unknown | Unknown |
| Cursor Editor | `.cursor/` rules, commands | Cursor skills where supported | Cursor agents/prompts where supported | Cursor MCP config | Cursor extensions unknown | Cursor rules/commands | Cursor telemetry blind spot |
| Cursor Agent Web | Web instructions unknown | No default skill projection claim | Cloud/background agents unknown | MCP support unknown | Web extensions unknown | Unknown | Cloud task telemetry blind spot |
| Cursor Agent CLI | CLI instructions unknown | No default skill projection claim | CLI agents unknown | MCP support unknown | CLI extensions unknown | Unknown | CLI telemetry blind spot |
| Perplexity Desktop | Unknown | No default skill projection claim | Unknown | Unknown until verified | Unknown | Unknown | Unknown |
| Cherry Studio | Unknown | No default skill projection claim | Unknown | MCP import/managed config | Desktop extension/imports | Config safety only | Unknown |
| Crush | `AGENTS.md` compatible bridge | Skills CLI support in bundle | Unknown | Crush config merge | Unknown | Unknown | Unknown |

## Support Tier Rules

| Tier | Meaning For Harnesses |
|---|---|
| `validated` | Repo has observed surface, fixture, rollback, and validation command. |
| `repo-present-validation-required` | Repo has paths/config entries but missing complete fixture or docs confirmation. |
| `planned-research-backed` | User requested or external research supports planning, but local support is not verified. |
| `experimental` | Surface exists or is requested, but behavior is unstable, incomplete, or mostly blind-spot. |
| `unverified` | Mentioned but not yet grounded in repo files or first-party docs. |
| `unsupported` | Explicitly not projected by this repo. |
| `quarantine` | Credential/proxy/offensive/live-risk surface requiring security lane approval. |

## Fixture Requirements

Every harness projection must eventually provide fixtures for:

- Fresh install or projection preview.
- Idempotent re-run with no drift.
- Merge with existing user-owned global config.
- Rollback to pre-apply state.
- Redaction of secrets and private paths in output.
- Validation of generated files against canonical sources.
- No fabricated installed-skill claims when discovery returns zero installs.

## Blind-Spot Policy

Do not guess hidden desktop, cloud, or UI-only behavior. Use `blind-spot` when a surface cannot be inspected from repo files or first-party docs. Blind spots can inform research tasks but cannot produce `validated` support.
