# Validation Matrix

## Run and green this session

| ID | Wave | Command | Result |
|----|------|---------|--------|
| V-001 | W0 | `uv run wagents openspec validate` | see summary in final report |
| V-002 | W1 | `just verify-fast` | see summary in final report |
| V-003 | W1 | `uv run wagents validate` | see summary in final report |
| V-004 | W1 | `uv run ruff check` | see summary in final report |
| V-005 | W1 | `uv run wagents eval validate --format json` (evidence: command exists, exercised standalone since `ci.yml` is not edited this session) | see summary in final report |
| V-006 | W1 | `uv run wagents eval adequacy --strict --format json` | see summary in final report |
| V-007 | W1 | `uv run wagents hooks validate --harness all --format json` | see summary in final report |
| V-008 | W1 | `actionlint .github/workflows/dependency-review.yml` (new standalone workflow) | see summary in final report |

## Deferred gates (future wave sessions)

| ID | Wave | Command | Expected |
|----|------|---------|----------|
| V-010 | W2 | `uv run wagents docs generate --check` | reports artifacts fresh |
| V-020 | W3 | `uv run wagents docs build` | all `/reports/*` build |
| V-030 | W4 | FastMCP Inspector smoke per Now server | handshake + list-tools |
| V-040 | W5 | link check catalog routes | no orphan catalog pages |
| V-050 | W6 | `skills/cross-agent-install-smoke` dry-run | JSON report valid |
| V-060 | W7 | `uv run wagents validate` (new skills) | frontmatter valid |
| V-070 | W8 | `uv run wagents validate` (new agents) | frontmatter valid |
| V-080 | W9 | golden snapshot pytest | no unexpected diffs |
| V-090 | W10 | FastMCP Inspector smoke per Next server | handshake + list-tools |
| V-100 | W11 | `wagents validate --format sarif` schema check | valid SARIF 2.1.0 |
| V-110 | W12 | `uv run wagents validate` (Next skills/agents) | frontmatter valid |
| V-120 | W13 | Later-tier scoped tests | per-item, see `tasks.md` |
| V-130 | W14 | maintainer dashboard | all sections populated |
| V-999 | W15 | `uv run wagents validate && uv run pytest && uv run wagents openspec validate` | all green |

## Notes

- CI wiring for V-005/V-006/V-007 is deferred to `SA-CI` (see `design.md`
  `ci.yml` collision section) — the commands themselves are validated
  standalone this session, not yet gated in CI.
- `dependency-review.yml` runs `actions/dependency-review-action` on
  `pull_request` only (no `push`/`workflow_dispatch` need) and does not touch
  `ci.yml`'s existing job graph.
