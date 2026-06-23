# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| APM research baseline | Read microsoft/apm README, docs, apm.yml examples, harness list | Accurate mapping to repo model | Anchor only on official sources; capture HEAD/ref. |
| Doctor integration | `uv run wagents self doctor` (or `uv run pytest ...::test_doctor...`) | APM row present (installed or "not found"); non-blocking; policy note | Optional dep. |
| Catalog authoring | Author MDX + `uv run wagents docs generate` | APM CLI row in `skills-catalog-index.json` and generated catalog | Follow Bucket A process; trust_tier, scope, "remote only". |
| README/docs parity | `uv run wagents readme --check` | Pass; content reflects doctor/catalog if surfaced | Generator only. |
| Bundle metadata | `cat agent-bundle.json \| jq '.adapters'` | APM notes/commands visible where added | Additive, non-breaking. |
| Policy in instructions | `grep -i apm instructions/global.md` (and spot-check mirrors) | Clear SSOT split + remote-only + no-dupe language | |
| OpenCode MCP split | Inspect `config/mcp-registry.json`, `mcp.json`, `scripts/sync...` render for opencode; run sample APM mcp scenario in dry context | No auto-overwrite of MCPHub group; separation documented | Evidence only; no live APM mcp apply required. |
| Facade (Wave 3) | `uv run wagents apm --help`; policy tests | Delegates or errors helpfully; blocks self-bundle | Dry-run friendly. |
| Asset validation | `uv run wagents validate` | Pass | |
| OpenSpec validation | `uv run wagents openspec validate` | Pass (this change + others) | |
| Python quality | `uv run ruff check wagents/ tests/ --fix`; `uv run ty check`; `uv run pytest -q -k apm or doctor or catalog` | Clean | |
| Skills sync orthogonality | `uv run wagents skills sync --dry-run` | Reports only repo + curated; no APM remote packages leaked | |
| Full pytest | `uv run pytest -q` | Pass (no regression on changed surfaces) | |

## Blockers

- Plan-mode or restricted envs may block live `apm` global install or network `apm install` during validation. Use presence checks and `--dry-run` where supported; document absence.

## Evidence To Capture

- `wagents self doctor` JSON or text output (redact sensitive).
- Generated catalog row JSON snippet for APM entry (name, description, install_command, source, notes).
- Diffs of `agent-bundle.json`, `instructions/global.md`, catalog index (if any).
- Command traces for facade (help, simulated policy guard).
- MCP render evidence showing separation for OpenCode.
- `uv run wagents openspec validate` output.
- Date-stamped full validation run summary.

## Deferred / Future

- Publishing this repo itself as an APM package (would use GitHub ref or marketplace).
- Bridging APM MCP declarations into MCP registry (explicit later change).
- First-class Grok/Crush entries in APM upstream.
- `apm` as a skill-creator target or recipe source.
