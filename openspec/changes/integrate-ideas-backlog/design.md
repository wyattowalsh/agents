# Design

## Lane model (subagent roles, from source plan)

| Lane | Code | Owns | Max parallel |
|------|------|------|---------------|
| Program | SA-L0 | OpenSpec, manifests, research refresh | 1 |
| Docs reports | SA-DOC | `wagents/docs_reports.py`, reports MDX, sidebar | 4 |
| Docs catalog | SA-CAT | `/catalog/*`, architecture pages, compose coordination | 3 |
| MCP shared | SA-MCP0 | `wagents/mcp_shared/`, registry schema extensions | 1 |
| MCP servers | SA-MCP* | One subagent per `mcp/<name>/` | 6 (Now), 5 (Next), 4 (Later) |
| CI/Infra | SA-CI | `.github/workflows/*`, attestations, reusable workflows | 2 (serialized on `ci.yml`) |
| Skills | SA-SKL | `skills/<name>/` tooling skills | 6 |
| Agents | SA-AGT | `agents/<name>.md` | 4 |
| CLI | SA-CLI | `wagents/cli.py`, SARIF schema | 2 |
| Tests | SA-TST | `tests/**` mirrors | 8 |
| Workflows | SA-WF | runbooks, PR templates, ADR template | 4 |
| Integration | SA-INT | Runs gate checks, no file edits | 1 |

Same-file edits within a lane are serialized; different lanes proceed in
parallel once their upstream wave gate passes.

## Collision map (serialize these)

| Serial owner | Rule |
|---|---|
| `.github/workflows/ci.yml` | **SA-CI only.** Not touched by this session (see below). |
| `wagents/docs.py` | **SA-DOC** merges reports-pipeline PRs one at a time. |
| `config/mcp-registry.json` | **SA-MCP0** batch-registers after each wave's parallel server lanes complete (never per-server). |
| `docs/src/generated-sidebar.mjs` | Regenerated only, after SA-DOC's `docs generate` run. |

## `ci.yml` collision — this session's resolution

At scaffold time, `git diff --stat .github/workflows/ci.yml` shows an
**uncommitted, in-flight** 28-line addition (the `hook-perf` job) from the
concurrent `fleet-hooks-performance` program. Editing `ci.yml` in this session
would either collide with that uncommitted diff or silently overwrite it.
Per the source plan's own coordination rule ("No `ci.yml` edits in W1 until
[the] hooks program lands or SA-CI rebases"), this program does **not** edit
`ci.yml` this session.

The exact addition SA-CI should apply to the `validate` job once `ci.yml`
stabilizes (commands already exist and were verified locally — see
`validation-matrix.md`):

```yaml
  validate:
    steps:
      # ... existing steps ...
      - run: uv run wagents eval validate --format json
      - run: uv run wagents eval adequacy --strict --format json
      - run: uv run wagents hooks validate --harness all --format json
```

No new dependencies; all three subcommands are implemented in
`wagents/cli.py` (`eval_validate`, `eval_adequacy`, `hooks_validate`).

### Update (W1 continuation) — interim standalone workflow shipped

`ci.yml` still carries the same uncommitted `fleet-hooks-performance` diff
(confirmed unchanged via `git diff --stat .github/workflows/ci.yml` at the
start of this continuation session). Rather than leave T-100a-c permanently
blocked, this continuation adds a standalone
[`ideas-quality-gates.yml`](../../../.github/workflows/ideas-quality-gates.yml)
workflow that runs the same three commands on `push`/`pull_request`/
`workflow_dispatch`, independent of `ci.yml`. This satisfies "add to CI" for
T-100a-c without touching the colliding file. Once `fleet-hooks-performance`
lands (or SA-CI rebases `ci.yml`), fold these three `run:` steps into
`ci.yml`'s `validate` job (exact diff above) and delete
`ideas-quality-gates.yml`.

## Coordination with in-flight work

| Active change | Relationship |
|---|---|
| `compose-harness-catalog-pages` (W2) | W5 catalog work merges into compose's composed-page pipeline; does not duplicate composed page logic. |
| `fleet-hooks-performance` | No `ci.yml` edits until it lands or rebases (see above). No edits to `wagents/hooks/**`, `hooks/**`, or `config/hook-registry.json` from this program — those are fully owned by that change. |
| `public-release-prod-readiness` | W11 attestations/OIDC scope aligns with its fail-closed validation parity goals rather than duplicating gates. |

## IDEAS → task mapping (complete coverage index)

Full per-item task ID mapping (MCP.md's 15 servers, DOCS.md's 12 items,
WORKFLOWS.md's 9 items, AGENTS.md's 15 agents, SKILLS.md's 15 skills, CLI.md's
8 items, TESTING.md's 8 items, INFRA.md's 8 items) is preserved verbatim from
the source plan and lives in `tasks.md` under each wave section. Items already
shipped are marked `SKIP` in `tasks.md` with an evidence pointer instead of
being re-implemented:

- CLI `--format json` / `doctor` / `--check`,`--dry-run` semantics →
  `wagents/cli.py` (verified: `eval_validate`, `eval_adequacy`, `hooks_validate`,
  `docs_generate --check`, `catalog index --check` all exist and pass locally).
- Docs: skills catalog generation and Starlight plugin wiring →
  `docs/astro.config.mjs`, `wagents/catalog.py`.
- Infra: SHA-pinned GitHub Actions → `.github/workflows/ci.yml` (already
  commit-SHA pinned, verified by reading the file).
- Agent analogues already shipped: `code-reviewer`, `docs-writer`,
  `release-manager`, `orchestrator` (repo-reviewer, docs-curator,
  release-checker map onto these — no new agent files for those three).

## Reports pipeline anchor (for W2, not implemented this session)

`wagents/docs_reports.py` should be modeled on the existing
`write_harness_support_page()` pattern in `wagents/docs.py`: a pure builder
function that returns MDX text plus a parallel JSON payload, called from
`_docs_generate_impl()`, registered in `config/docs-artifact-registry.json`,
and wired into `_docs_generate_stale_reasons()` so `docs generate --check`
flags stale reports. Dual output (MDX + `docs/public/generated-reports/*.json`)
keeps reports both human-browsable and machine-consumable by the future
`mcp-docs-index`/`mcp-eval-results` servers (W4/W10).

## MCP shared library anchor (for W4/W9, not implemented this session)

`wagents/mcp_shared/read_only_paths.py` (prefix allowlist reused by every
read-only MCP server) and `wagents/mcp_shared/catalog_readers.py` (thin
wrappers over `wagents/catalog.py` and `wagents/skill_index.py`) must land in
W2 **before** any W4 server lane starts, to avoid six servers independently
reinventing path-guard and catalog-read logic.
