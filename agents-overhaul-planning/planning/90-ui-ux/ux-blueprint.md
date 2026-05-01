---
status: planning
owner: ux-automation-team
last_updated: 2026-05-01
---

# UX Automation Blueprint

## Product principles

- Prefer one command over manual config editing.
- Always offer dry-run preview before writing user-level config.
- Explain why an extension is skill, plugin, MCP, or unsupported.
- Generate support matrices from registries.
- Treat drift as diagnosable and repairable.

## Core commands

| Command | Behavior |
|---|---|
| `wagents doctor` | Detect harnesses, runtimes, config paths, stale versions, missing auth, unsupported experimental surfaces. |
| `wagents sync --preview` | Render desired config and show structured diff without writing. |
| `wagents sync --apply` | Apply transactionally with backup, post-write validation, and rollback-on-failure. |
| `wagents rollback` | Restore latest snapshot for selected harness or all harnesses. |
| `wagents catalog browse` | Browse skills/plugins/MCPs with support badges and installability. |
| `wagents catalog explain <id>` | Explain source, provenance, risk, install path, and support tier. |
| `wagents install-skill <id>` | Use `npx skills` where supported; otherwise render exact manual/project projection. |
| `wagents mcp inspect <id>` | Show transport, auth, install command, risk, and smoke-test status. |
| `wagents openspec status` | Show active changes, spec coverage, task completion, and drift vs planning graph. |

## Drift detection

Compare:

- registry desired state
- generated config snapshots
- actual user/project harness config
- lock/provenance records
- docs generated at last commit
- OpenSpec task status

## Dashboard abstraction

The docs site should expose:

- harness support matrix
- skill/plugin/MCP catalog
- one-click/copyable install snippets
- support-tier and trust-tier badges
- risk warnings
- OpenSpec change status
- task graph progress
