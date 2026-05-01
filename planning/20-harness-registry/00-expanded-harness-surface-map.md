# Expanded Harness Surface Map

## Purpose

This research plan expands the agents platform overhaul across every named harness and agent surface. It is a planning artifact only: no live user config, generated config, non-Markdown manifest, plugin install, or skill install is changed here.

The goal is elegant coverage: every harness has an explicit ownership lane, surface model, support-tier posture, validation boundary, rollback expectation, and known blind spots.

## Harness Set

| Harness Surface | Canonical Harness | Owner Lane | Current Repo Evidence | Initial Support Tier | Primary Concern |
|---|---|---|---|---|---|
| Claude Code | `claude-code` | `agents-c04-claude-harness` | Claude plugin manifest, repo instructions, generated OpenSpec artifacts, skills install support. | `validated` after fixture pass | Skills, commands, hooks, MCP, plugin marketplace, instruction precedence. |
| Claude Desktop | `claude-desktop` | `agents-c04-claude-harness` | Global Claude Desktop MCP config is merged in `config/sync-manifest.json`. | `repo-present-validation-required` | MCP config merge safety, desktop-only auth boundaries, no generated skill claims. |
| ChatGPT Desktop/App | `chatgpt` | `agents-c04-openai-harness` | ChatGPT MCP path is merged in `config/sync-manifest.json`; app support needs current docs verification. | `repo-present-validation-required` | MCP connector shape, app/widget/tool differences, no unsupported skill projection claims. |
| Codex | `codex` | `agents-c04-openai-harness` | Codex plugin manifest, Codex marketplace adapter, generated/merged Codex config in manifests. | `validated` after fixture pass | Skills, plugins, MCP, instructions, hooks, local provider profile boundaries. |
| GitHub Copilot Web/Coding Agent | `github-copilot-web` | `agents-c04-copilot-harness` | `.github/` generated prompts/instructions/skills and repo Copilot bridge policy. | `repo-present-validation-required` | Web/coding-agent instructions, prompts, MCP, no fabricated installed-skill inventory. |
| GitHub Copilot CLI | `github-copilot-cli` | `agents-c04-copilot-harness` | Global Copilot config and agents/skills symlink surfaces in `config/sync-manifest.json`. | `repo-present-validation-required` | CLI config shape, MCP config, skill discovery limits, subagent behavior. |
| OpenCode | `opencode` | `agents-c04-opencode-gemini-harness` | `opencode.json`, `.opencode/`, `.opencode-plugin/`, live config merge surfaces, plugins, DCP. | `validated` after fixture pass | Model-neutral policy, plugin placement, DCP, MCP launcher override, credential guard. |
| Gemini CLI | `gemini-cli` | `agents-c04-opencode-gemini-harness` | `GEMINI.md`, `.gemini/`, global Gemini settings and skills surfaces. | `validated` after fixture pass | Instructions, MCP, skills, OpenSpec wrapper mapping. |
| Antigravity | `antigravity` | `agents-c04-opencode-gemini-harness` | `.antigravity/`, Antigravity MCP config merge paths, Gemini-compatible bridges. | `repo-present-validation-required` | Separate first-party docs from repo-observed Gemini compatibility assumptions. |
| Cursor Editor | `cursor` | `agents-c04-cursor-harness` | `.cursor/`, `.cursor/commands`, `.cursor/skills`, Cursor MCP config. | `validated` after fixture pass | Rules, commands, skills, MCP, generated vs canonical source. |
| Cursor Agent Web | `cursor-agent-web` | `agents-c04-cursor-harness` | No distinct repo-native surface yet; aliases route to Cursor in `harness-master`. | `planned-research-backed` | Cloud/background agent behavior and web-only surfaces are blind spots until verified. |
| Cursor Agent CLI | `cursor-agent-cli` | `agents-c04-cursor-harness` | No distinct repo-native surface yet; aliases route to Cursor in `harness-master`. | `planned-research-backed` | CLI auth/config, MCP support, and rules precedence need docs/source verification. |
| Perplexity Desktop | `perplexity-desktop` | `agents-c04-experimental-harnesses` | `.perplexity/` path requested; no validated support record yet. | `experimental` | Desktop config support, MCP/instruction support, local data boundaries. |
| Cherry Studio | `cherry-studio` | `agents-c04-experimental-harnesses` | Cherry Studio global config and MCP import path in `config/sync-manifest.json`. | `experimental` | MCP import/export, config merge safety, no skill projection claims. |
| Crush | `crush` | `agents-c04-experimental-harnesses` or current downstream tooling specs | Crush config merge path exists in `config/sync-manifest.json` and install adapter support exists. | `repo-present-validation-required` | Clarify whether it remains supported or moves into experimental lane. |

## Surface Types

| Surface Type | Description | Allowed Projection | Validation Required |
|---|---|---|---|
| Instructions | System prompts, global instructions, project AGENTS/CLAUDE/GEMINI files, Copilot instructions. | Generate from canonical instruction source or bridge file. | Precedence test and generated-output freshness check. |
| Skills | Agent Skills directories, installed-skill inventory, skill symlinks, source-list installs. | Agent Skills first, with no fabricated install support. | `wagents validate`, package dry-run, source-list/audit for externals. |
| Agents/Subagents | Harness-native agent definitions or generated prompts. | Only when harness has native agent surface or compatible prompt artifact. | Frontmatter/schema validation and fixture projection. |
| MCP | MCP server config for live state, browser, SaaS, docs/search, desktop app integrations. | Only if live-system justification exists. | Secrets, transport, sandbox, smoke fixture, rollback. |
| Plugins/Extensions | Native plugin manifests, marketplaces, runtime plugin arrays, desktop extension imports. | Use only as native projections of canonical repo assets. | Plugin schema, install/update commands, rollback, generated-source trace. |
| Hooks/Guards | Approval hooks, credential guards, validation hooks, shell command guards. | Generate from canonical hook registry. | Non-destructive dry-run and blocked-secret fixture. |
| UI/Control Plane | Web, desktop, TUI, statusbar, session board, side panel, dashboards. | Build repo-native views; borrow external UI logic as requirements. | UX fixture, accessibility review, redaction policy. |
| Telemetry/History | Session replay, token/cost, logs, run graph, eval metrics. | Local redacted summaries by default. | Redaction fixture, opt-in policy, retention policy. |

## Cross-Harness Principles

1. Canonical source beats generated output. Fix `config/`, `instructions/`, `agent-bundle.json`, or registry fragments before editing generated harness files.
2. Every harness surface needs a support tier, evidence tag, owner lane, and rollback path.
3. Desktop apps and cloud agents must be treated as separate surfaces even when they share a brand.
4. Web/cloud agents must be marked `planned-research-backed` or lower until first-party docs or observed fixtures confirm config behavior.
5. MCP config must never imply skill support. MCP is live-system wiring; skills are deterministic portable workflows.
6. Auth reuse, credential bridges, account proxies, and desktop-profile access must route through `agents-c15-security-quarantine` before being documented as anything more than a blind spot.
7. Model selectors stay out of repo-managed OpenCode surfaces; preserve user-owned local model settings when merging live config.
8. Generated docs and README support matrices are downstream outputs and must be regenerated from registries/fragments, not hand-edited.

## Gap Register

| Gap | Impact | Owner Lane | Fill Strategy |
|---|---|---|---|
| ChatGPT app vs desktop vs connector support is not distinguished enough. | Risk of overclaiming skill/MCP/plugin behavior. | `agents-c04-openai-harness` | Add separate ChatGPT surface rows and docs-source checklist. |
| Cursor agent web/CLI/background agent surfaces are collapsed into Cursor. | Risk of treating cloud/CLI agent behavior like editor rules. | `agents-c04-cursor-harness` | Split `cursor-editor`, `cursor-agent-web`, and `cursor-agent-cli` in planning fragments. |
| Copilot web/coding agent vs CLI surfaces are not independently validated. | Risk of fabricated install support or wrong config precedence. | `agents-c04-copilot-harness` | Separate web/coding-agent prompts from CLI config/MCP surfaces. |
| Claude Desktop global MCP merge is present but not fully separated from Claude Code plugin/skills support. | Risk of desktop support overstating skill projection. | `agents-c04-claude-harness` | Define Desktop as MCP-first with separate rollback and secret handling. |
| Perplexity Desktop is requested but not verified. | Unknown support and config format. | `agents-c04-experimental-harnesses` | Keep experimental until source/docs/user config inspection. |
| Cherry Studio has managed config/import surfaces but no support-tier fragment. | Risk of undocumented MCP import behavior. | `agents-c04-experimental-harnesses` | Create Cherry-specific experimental fragment and import/export fixture. |
| Cross-harness support tiers are not centralized in a Markdown planning matrix. | Child lanes can drift. | `agents-c01-registry-core` | Generate support-tier registry schema later; use this Markdown map now. |
| Config transaction model must cover live global desktop configs. | Incorrect merge can break user tools. | `agents-c06-config-safety` | Require preview/apply/rollback for every global merge surface. |
| External UI/control-plane repos need a unified data contract target. | Borrowed UI ideas may fragment. | `agents-c05-ux-cli`, `agents-c14-multiagent-ui-patterns` | Define common session/task/status/telemetry entities before building UI. |
| Official docs/source lookup is incomplete for new harnesses. | Lower confidence and stale assumptions. | all `agents-c04-*` lanes | Add docs-source ledger and `llms.txt` attempts per harness. |

## Research Workstreams

### Workstream A: Harness Evidence Ledger

Create one Markdown fragment per canonical harness surface under `planning/20-harness-registry/`. Each fragment must include files reviewed, docs checked, blind spots, support tier, generated/canonical surfaces, and fixture requirements.

### Workstream B: Projection Contract

Create a projection contract that answers, for each harness: how instructions, skills, agents, MCP, plugins, hooks, UI, and telemetry move from canonical repo assets to project/global surfaces.

### Workstream C: Config Safety Contract

Create transaction-safe config rules for project files and global desktop files. Every apply must have preview, backup, redaction, rollback, and no-secrets output.

### Workstream D: Docs Truth Contract

Define generated README/docs/support-matrix ownership. Generated docs should cite registry fragments and support tiers, never raw assumptions from external repos or UI-only behavior.
