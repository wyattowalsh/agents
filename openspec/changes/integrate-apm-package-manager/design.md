# Design

## Approach

Integrate APM as a **complementary optional CLI** for consuming remote agent packages, while preserving the repo's canonical bundle + sync model as the SSOT for repo-owned assets. Use a thin `wagents apm` facade for policy-aware delegation. Add presence checks to doctor and a catalog entry. Do not project repo skills/agents into APM manifests or duplicate harness plugin trees.

## SSOT Split

- **Repo bundle (SSOT for this project):** `agent-bundle.json`, `skills/`, `agents/`, `instructions/`, `mcp/`, `config/*-registry.json`. Installed via `npx skills add github:wyattowalsh/agents ...` or native plugin adapters, reconciled by `wagents skills sync`.
- **APM (for remote packages):** Users declare third-party `apm` packages (or raw primitives) in their own `apm.yml`; `apm install` deploys them to detected harnesses. This repo may document or facade APM but does not make `apm.yml` the root for its own `skills/`.
- **No duplication rule (AGENTS.md §2.1):** Never copy `skills/`, `agents/`, `mcp/`, `instructions/` trees into per-harness plugin folders or into a project-local `apm/` for distribution of this bundle.
- Local project `.apm/` (if created by a consumer) deploys only local primitives declared for that consumer project; this repo's bundle root remains independent.

## wagents Complement

- `wagents` remains the control plane for repo bundle (validate, docs, skills sync, self).
- New optional `wagents apm <cmd>` (Wave 2+) delegates to `apm` binary (if present) after applying repo policy (allowed sources, no self-bundle, MCP separation notes).
- `wagents self doctor` adds an APM row (installed? version? `apm --version` or `which apm`; policy note; non-fatal).
- Catalog surface: add authoring MDX for "apm-cli" (or similar) under Bucket A so `wagents docs generate` emits a visible external/tool row with install, scope, and "remote packages only" guidance.
- `wagents skills sync --dry-run` remains orthogonal; it reconciles repo + curated-externals, not APM remote deps.

## OpenCode MCP Merge

- APM supports declaring MCP servers under `mcp:` in `apm.yml` and deploys via `apm-servers/` or harness integration points.
- Repo MCP model: `config/mcp-registry.json` (canonical) → MCPHub (`scripts/mcphub/...`) → generated `mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, OpenCode via sync, etc.
- **Split:** Treat APM-managed MCPs as user/consumer declared remote servers. Do not auto-populate repo `mcp-registry` from APM nor project `apm.yml` from registry in this change.
- OpenCode specific: repo `opencode.json` + live `~/.config/opencode/opencode.json` own runtime plugins and (via sync) some MCP. APM may add MCP entries to OpenCode-detected locations; keep ownership notes so sync does not fight APM-deployed MCPs. Future bridge would be explicit (e.g., opt-in projection) and tracked separately.
- Precedence: repo-managed "harness-safe" group via MCPHub stays default for repo surfaces.

## Data And Control Flow

1. User clones repo → uses `wagents` or `npx skills` for bundle.
2. User may `npm i -g apm` (or equiv) and `apm install <remote-pkg>` for third-party skills/agents/MCP.
3. `wagents self doctor` surfaces APM presence for diagnostics.
4. Harness instructions may `@import ./apm/AGENTS.md` (if consumer created `apm/` layout) for progressive context; repo instructions remain SSOT and import only policy notes.
5. `apm sync` / `apm install` operates on consumer `apm.yml` + lockfile; does not mutate repo `skills/`.

## Integration Points

- `agent-bundle.json`: additive notes for APM install/doctor commands.
- `wagents/cli.py` (or dedicated `wagents/apm.py`): doctor extension + facade skeleton.
- `docs/src/authoring/skills/apm-cli.mdx` (or equivalent id): curated entry (generated via docs generate).
- `instructions/global.md` and harness globals: add "APM for remote" policy paragraph + import guidance.
- `config/sync-manifest.json`: declare any new APM-related generated or canonical paths if introduced (e.g., optional apm notes).
- `config/harness-surface-registry.json`: note APM support tiers for overlapping harnesses (informational).
- Validation: `wagents validate`, `wagents openspec validate`, doctor tests.

## Alternatives Rejected

- Make APM the primary installer for this repo bundle: rejected — violates repo distribution model and existing adapter matrix in agent-bundle.json.
- Mirror repo skills into APM package format for distribution: rejected — duplicates ownership; Skills CLI + bundle already cover.
- Auto-merge APM MCP declarations into mcp-registry: rejected — blurs ownership, security, and sync surfaces.
- Require `apm` globally: rejected — keep optional; doctor and catalog note presence.

## Migration Or Compatibility Notes

- Existing `wagents skills sync --dry-run` output and catalog rows continue to describe repo + curated externals.
- APM users of this repo can reference it via GitHub refs in `apm.yml` if/when this bundle is published as an APM package (future, out of scope).
- Grok/Crush paths: continue via current sync; document that APM matrix currently lists other harnesses.
- Lockfile + hash integrity from APM is valuable for remote packages; repo uses its own asset validation.
- Add `.apm/` and `apm_modules/` to guidance for `.gitignore` consumers (already typical for such tools).
