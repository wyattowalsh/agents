# Affected Surfaces

## Source Of Truth

- `agent-bundle.json` — bundle manifest; will carry complementary APM notes and update commands.
- `instructions/global.md` — primary policy SSOT for distribution, bundle, external tools, and sync semantics (harness mirrors generated from it).
- `wagents/cli.py`, `wagents/self.py` (or context/doctor modules) — doctor command and self subcommands.
- `docs/src/authoring/skills/` (new `apm-cli.mdx` or equivalent) — Bucket A authoring SSOT for the APM CLI catalog row.
- `config/sync-manifest.json` — declares canonical/generated paths (may list new policy or catalog surfaces).
- `config/harness-surface-registry.json` — support tier and projection notes (APM informational overlay).
- `wagents/docs.py`, `wagents/site_model.py`, catalog index generators — emit APM tool row.
- `scripts/sync_agent_stack.py` — MCP and harness projections (MCP separation concerns).
- `AGENTS.md` — high-level distribution rules (§2.1) cross-reference.
- `openspec/changes/integrate-apm-package-manager/` — this change.

## Generated Outputs

- `README.md` (via `uv run wagents readme`) — if doctor or distribution text changes.
- `docs/public/generated-registries/skills-catalog-index.json` and catalog MDX pages (via `uv run wagents docs generate --no-installed`).
- Harness instruction mirrors (e.g., `instructions/codex-global.md`, `instructions/opencode-global.md`, `.github/copilot-instructions.md`, etc.) when global.md is updated.
- `opencode.json` / other generated only if MCP notes require (unlikely in scope).

## Downstream Harness Artifacts

- User global `apm` installs and per-project `apm.yml` / `apm.lock.yaml` / `.apm/` / `apm_modules/` (consumer-owned; repo does not mutate).
- Per-harness MCP/plugin locations when users run `apm install` against their manifests (separate from repo MCPHub projections).
- Live OpenCode `~/.config/opencode/opencode.json` may receive APM MCP entries; repo sync must not clobber them (document separation).

## Tests

- `tests/test_cli_integration.py` (doctor APM row)
- `tests/test_distribution_metadata.py` (bundle notes, catalog presence)
- Site model / catalog tests for external/tool row
- `tests/` for facade policy when implemented

## Validation Commands

- `uv run wagents self doctor`
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `uv run wagents docs generate`
- `uv run wagents readme --check`
- `uv run pytest -k "doctor or distribution or catalog" -q`
- `npx skills --help` (for Skills CLI parity context, not direct APM)
- `apm --version || echo "apm not installed (expected in some envs)"`

## Review

- Catalog review for new APM row visibility and wording.
- Docs-steward or equivalent after generate if public pages change.
