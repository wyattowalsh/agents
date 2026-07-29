# Change: Remove Gemini CLI, Antigravity, and GitHub Copilot Endorsement

## Why

The fleet no longer endorses Gemini CLI, Antigravity, or GitHub Copilot (web/cli)
as managed harnesses. Keeping sync writers, install matrices, hooks, docs, and
surface registries for those three increases maintenance cost and confuses
Chrome DevTools / MCP ownership. The repository will also stop accepting their
agent IDs as curated external skill targets.

## What Changes

- Drop `gemini-cli`, `antigravity`, and `github-copilot` from
  `site_model.SUPPORTED_AGENTS`, `SKILLS_CLI_NATIVE_AGENT_IDS`, and
  `external_skills.SUPPORTED_TARGET_AGENTS`.
- Freeze the managed-harness taxonomy at exactly `claude-code`, `codex`,
  `crush`, `cursor`, `grok`, and `opencode`; keep the Skills CLI-native subset
  at exactly the same set without `grok`, and describe MCP-only/hybrid clients
  separately instead of inflating either count.
- Remove sync/home/repo writers for the three harnesses; stop generating
  Copilot `.github` instruction/hook projections.
- Crush (+ AITK) MCP continues via `render_flat_mcp(..., harness="crush")`
  with flat map + `type: stdio` — never `render_client_mcp`.
- Strip removed harness IDs from registries/manifests/authoring install
  commands; preserve dirty candidate MCP WIP (`candidate-*` wrappers/servers).
- Remove residual active authored rows, fixtures, and generated projections for
  the retired harnesses, then run a bounded semantic scan that preserves only
  explicitly classified historical or change-control references.
- Smoke matrix drops `github-copilot` and `gemini-cli` only (no antigravity row).
- Keep OpenCode auth plugins, `gemini-api` skill, CI workflows/actions.
- Close generation only after AITK proves it receives the Crush-filtered
  Gemini-shaped `type: stdio` projection and the final APM lock check converges.

## Non-Goals

- Removing Crush, Cherry Studio, or LM Studio.
- Wiping `~/.gemini` / `~/.copilot`.
- Finishing unrelated candidate MCP feature work (surgical coexistence only).
- Git commits unless the user explicitly requests them.

## Breaking Change

Install/docs/sync no longer endorse Gemini CLI, Antigravity, or GitHub Copilot.
Curated external skill records and public install commands must use only the
remaining supported targets.
