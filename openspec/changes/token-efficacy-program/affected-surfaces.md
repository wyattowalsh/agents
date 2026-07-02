# Affected Surfaces

## OpenSpec (Wave 0)

- `openspec/changes/token-efficacy-program/proposal.md`
- `openspec/changes/token-efficacy-program/design.md`
- `openspec/changes/token-efficacy-program/tasks.md`
- `openspec/changes/token-efficacy-program/validation-matrix.md`
- `openspec/changes/token-efficacy-program/affected-surfaces.md`
- `openspec/changes/token-efficacy-program/specs/downstream-tooling/spec.md`
- `openspec/changes/token-efficacy-program/specs/docs-instructions/spec.md`

## Repo-Owned Source (Wave 2–4, future)

- `config/rtk-integration.json` — RTK fleet policy (read during apply; no Wave 0 edits).
- `config/opencode-dcp.jsonc` — DCP canonical config (Wave 4 conditional).
- `scripts/sync_agent_stack.py` — T040 `--with-rtk` / `RTK_ENABLED=1` integration.
- `wagents/rtk.py` — doctor/sync/gain CLI (consume only in Wave 2+).
- `AGENTS.md` — token budget, layer taxonomy, decision gates (Wave 3).
- `docs/src/content/docs/harness-config/` — token posture hub MDX (Wave 3).
- `instructions/global.md` — standing-context trim candidates from R3 (Wave 3+, gated).
- `.claude/rules/`, `.cursor/rules/`, `.github/instructions/` — sync projections after instruction edits (Wave 3).

## Tests (Wave 2–5, future)

- `tests/test_rtk_cli.py` — RTK apply, init-only, doctor/sync regressions.
- Potential new validation for `@RTK.md` shared-corpus grep (T043).

## Related OpenSpec Change

- `openspec/changes/integrate-rtk-harness-fleet/` — parent RTK integration; Wave 4 tasks T040–T044 completed under this program.

## Local User-Owned Surfaces (Wave 2 apply targets; not edited by repo)

- `~/.claude/RTK.md`, Claude shell hooks
- `~/.cursor/hooks.json`
- `~/.config/opencode/plugins/rtk.ts`
- `~/.codex/RTK.md`, Codex instruction hooks
- `~/.gemini/hooks/`, `~/.gemini/settings.json`
- `~/.copilot/hooks/`
- `~/.grok/hooks/` (T041 Grok shim, schema-gated)

## Research Artifacts (local, not committed)

- `~/.claude/research/` — compare matrices, landscape track journal, MCP/host-panel notes
- `~/.config/opencode/logs/dcp/` — DCP evidence for R5

## Generated Surfaces (Wave 3)

- `README.md` — via `wagents readme`
- `docs/public/generated-registries/` — via `wagents docs generate --no-installed`
- `.github/copilot-instructions.md` — via `sync_agent_stack.py --targets repo`

## Explicitly Out Of Scope For Repo Edits

- Installing Sleev, Headroom, Cozempic, mcp-compressor, jCodeMunch without gated approval
- `@RTK.md` in shared instruction corpus
- RTK entry in `opencode.json` plugin array
- Vendoring third-party token tools into `skills/`
