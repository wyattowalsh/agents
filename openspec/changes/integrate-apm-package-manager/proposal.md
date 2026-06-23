# Proposal

## Why

AI agent setups need a package-manager model for remote primitives (skills, agents, instructions, plugins, MCP). Microsoft APM provides `apm.yml` + lockfile + `apm install/sync` with security scans and harness deployment for Copilot, Claude, Cursor, OpenCode, Codex, Gemini, Windsurf, etc. The agents repo already owns the canonical bundle at root (`agent-bundle.json`, Skills CLI, `wagents skills sync`) and must not duplicate trees or create conflicting install paths for its own `skills/`, `agents/`, `instructions/`, `mcp/`.

Current doctor and catalog surfaces do not recognize the `apm` CLI. Without tracked integration, docs, validation, and harness instructions can drift on remote vs. repo-owned semantics.

## What Changes

- Treat Microsoft APM as **primary deploy path** for repo agents/instructions/hooks on supported harnesses; **remote-only** for third-party packages (never repo `skills/`).
- Add `apm` CLI awareness to `wagents self doctor` (presence, version, policy notes optional).
- Add curated catalog row (authored MDX under docs + generate) documenting APM usage, install, and repo policy.
- Extend `agent-bundle.json` update/doctor commands with APM notes (no change to bundle components).
- Add `wagents apm materialize` + `wagents apm doctor` (materialize SSOT → `.apm/`; MCP stays MCPHub-owned with `mcp: []`).
- Document SSOT split: repo bundle via wagents/Skills CLI; remote packages via APM; no duplication of repo trees into `apm/` or vice-versa.
- Add harness instruction overlay guidance (AGENTS.md import pattern for `apm/AGENTS.md` where present) without altering bundle projection.
- Clarify OpenCode MCP: APM `apm-servers/` (or mcp: in apm.yml) remains separate from repo `config/mcp-registry.json` + MCPHub unless a later explicit merge is approved.
- Update sync-manifest, harness registry notes, and validation where APM surfaces appear.

## Impact

- Consumers gain a standard `apm install` path for third-party remote agent packages alongside this repo's bundle.
- Maintainers keep single SSOT at repo root; APM does not own or mirror `skills/`.
- Public docs and catalog expose APM as a complementary tool with explicit scope and trust notes.
- Minimal risk to existing harness coverage; Grok/Crush continue using repo sync (APM matrix omits them as first-class today).
- Adds optional global `apm` dep for users; repo validation treats it as non-blocking.

## Scope

- Docs, doctor, catalog entry, bundle metadata notes, policy wording.
- OpenSpec change artifacts + validation matrix.
- Architecture: CLI facade + import overlays (phased).

## Out Of Scope

- Routing repo `skills/` or bundle through `apm install` (never).
- Duplicating MCP registry into APM `dependencies.mcp` (MCPHub + `config/mcp-registry.json` remain SSOT; `apm.yml` keeps `mcp: []`).
- Adding Grok/Crush as APM targets (defer to APM upstream or explicit follow-up).
- Live `apm install` of arbitrary packages during this change unless explicitly scoped in waves.
- Changing `wagents skills sync` primary path.

## Affected Users And Tools

- Users installing agent context via global `apm` CLI or `npx skills add`.
- Harness users on supported APM targets (Copilot, Claude Code, Cursor, OpenCode, etc.).
- Maintainers of `wagents`, catalog generation, `agent-bundle.json`, instructions.
- Docs readers and `wagents self doctor` consumers.

## Generated Surfaces To Refresh

- README via `uv run wagents readme` (if doctor/catalog text changes surface).
- Docs catalog via `uv run wagents docs generate` (new APM CLI authoring MDX).
- `agent-bundle.json` (manual notes only, or small additive updateCommands).

## Risks

- Dual paths create user confusion: mitigate with clear "APM for remote only; repo bundle via Skills/wagents" wording in docs, doctor, and instructions.
- APM local deployment (`.apm/`, `apm_modules/`) could collide with repo paths: document `.gitignore` expectations and precedence (local .apm wins only for its declared content).
- MCP overlap: document separation; do not auto-merge `apm-servers` with MCPHub.
- Catalog row requires audit-style MDX + generate like other externals.
