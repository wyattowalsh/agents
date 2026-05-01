# Validation Matrix

| Gate | Command Or Evidence | Expected Result |
| --- | --- | --- |
| OpenSpec validity | `uv run wagents openspec validate` | All specs and changes valid. |
| C09 status | `uv run wagents openspec status --change agents-c09-release-archive --format json` | `isComplete: true`. |
| Markdown whitespace | `git diff --check -- planning/95-migration openspec/changes/agents-c09-release-archive` | No whitespace errors. |
| Scope review | Lane-scoped review of C09 files | No blockers; forbidden surfaces excluded. |
| Release readiness | `planning/95-migration/30-release-checklist.md` | Checklist covers pre-release, validation, docs, candidate, and post-merge gates. |
| Archive readiness | `planning/95-migration/40-openspec-archive-checklist.md` | Archive evidence, order, and stop conditions are defined. |

## Deferred Validation

Generated docs synchronization, archive execution, and live config transaction tests are deferred until an explicit release or archive operation requests those changes.
