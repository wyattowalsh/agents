# OpenSpec Archive Checklist

## Archive Gate

Do not archive until all release checklist validation passes after merge or after the final approved release commit lands on `main`.

Release deferrals are not archive deferrals. Any parent or child task deferred for release must be resolved, removed through an approved scope update, or recorded as a new follow-up change before archive.

## Required Evidence

- [x] Parent change and all child changes show complete status.
- [x] `uv run wagents openspec validate` passes.
- [x] `planning/95-migration/50-release-notes.md` identifies every child change plus exact readiness and archive evidence commits.
- [x] Known deferred work has an owner, reason, and follow-up location.
- [x] Specs receiving archived deltas are reviewed for duplicate or conflicting requirements.
- [x] Generated artifacts are either committed intentionally or confirmed out of scope.

## Archive Order

1. Archive leaf child changes first.
2. Validate after each high-risk archive batch.
3. Archive parent `agents-platform-overhaul` last.
4. Re-run full OpenSpec validation.
5. Commit archive moves as a single archive-focused commit if the diff is coherent; split if specs are unrelated.

## Child Changes

| Change | Archive Condition |
| --- | --- |
| `agents-c00-repo-sync` | Foundation state committed and validated. |
| `agents-c01-registry-core` | Registry contracts complete and validated. |
| `agents-c02-skills-lifecycle` | Wave 1 skills lifecycle planning committed. |
| `agents-c03-mcp-audit` | Wave 1 MCP audit planning committed. |
| `agents-c04-*` | Harness planning lanes committed. |
| `agents-c05-ux-cli` | Wave 2 CLI UX contracts committed. |
| `agents-c06-config-safety` | Config transaction safety contracts committed. |
| `agents-c07-ci-evals-observability` | Quality gates and observability contracts committed. |
| `agents-c08-docs-instructions` | Docs instruction planning committed. |
| `agents-c09-release-archive` | This readiness lane committed, validated, and archived. |
| `agents-c10-external-repo-intake` | External intake planning committed. |
| `agents-c11` to `agents-c15` | Research and control-plane planning committed and archived. |

## Stop Conditions

- Any child change is incomplete.
- Archive would overwrite active uncommitted work.
- OpenSpec validation fails after archive.
- A spec delta conflicts with the current source of truth.
