# Agents Platform Overhaul Release Notes

## Scope

This release note records the completed planning and control-plane waves for the agents platform overhaul. It is release evidence for readiness review and the OpenSpec archive pass; it does not perform generated docs regeneration or live harness config mutation.

## Current Committed Range

| Commit | Scope |
| --- | --- |
| `9758f19` | External repository intake foundation. |
| `3e432a8` | Docs instruction planning lane. |
| `6217274` | Cross-harness Chrome DevTools skills. |
| `7a53fc3` | Wave 1 planning lanes. |
| `fa20686` | Wave 2 planning lanes. |
| `9ac8ab5` | Release/archive readiness lane. |

These six commits were the original planning/control-plane wave range. Additional readiness and archive evidence landed after `9ac8ab5`; do not use a broad range from `9ac8ab5` to the current `HEAD` as release evidence because unrelated commits also landed before archive execution.

## Final Evidence

| Item | Status |
| --- | --- |
| C00/C01 required OpenSpec artifacts | Added as readiness evidence after baseline C09 readiness. |
| Release-note evidence | Added as readiness evidence after baseline C09 readiness. |
| Final readiness evidence commit | `6e29385 docs(openspec): complete platform readiness evidence`. |
| Archive execution commit | `841b9b1 docs(openspec): archive agents platform overhaul`. |
| Final rollback evidence | Revert `841b9b1` before `6e29385` when rolling back archive/readiness evidence; unrelated commits between `9ac8ab5` and `841b9b1` are not part of this release evidence set. |
| OpenSpec archive | Applied in `841b9b1` through `uv run wagents openspec archive <change> --yes --apply` for all `agents-*` child changes and parent `agents-platform-overhaul`. |

## Child Change Coverage

| Change | Release Evidence |
| --- | --- |
| `agents-c00-repo-sync` | Inventory and drift-ledger foundation completed with required OpenSpec artifacts. |
| `agents-c01-registry-core` | Registry schema and support-tier contracts completed with required OpenSpec artifacts. |
| `agents-c02-skills-lifecycle` | Skills lifecycle control-plane planning committed. |
| `agents-c03-mcp-audit` | MCP audit control-plane planning committed. |
| `agents-c04-*` | Claude, OpenAI, Copilot, Cursor, OpenCode/Gemini, and experimental harness planning lanes committed. |
| `agents-c05-ux-cli` | CLI UX output contracts committed. |
| `agents-c06-config-safety` | Config transaction, rollback, and redaction contracts committed. |
| `agents-c07-ci-evals-observability` | Quality gates, evals, and observability contracts committed. |
| `agents-c08-docs-instructions` | Docs and instruction sync planning committed. |
| `agents-c09-release-archive` | Release and archive readiness planning committed and archived. |
| `agents-c10-external-repo-intake` | External repo intake planning committed. |
| `agents-c11-knowledge-graph-context` | Knowledge graph context adoption planning committed. |
| `agents-c12-session-telemetry` | Session telemetry contract planning committed. |
| `agents-c13-skill-registry-intake` | Skill registry intake planning committed. |
| `agents-c14-multiagent-ui-patterns` | Multiagent UI pattern planning committed. |
| `agents-c15-security-quarantine` | Security quarantine planning committed. |

## Validation Evidence

| Check | Result |
| --- | --- |
| `uv run wagents openspec validate` | Passed 29/29 items before and after archiving; after archive, 4 active changes and 25 specs validate. |
| `uv run wagents openspec archive <change> --yes --apply` | Archived `agents-c00` through `agents-c15` and parent `agents-platform-overhaul`; spec deltas synced into `openspec/specs/`. |
| `git status --short --branch` | Clean before archive; archive pass produced only intended OpenSpec moves/spec updates and release-evidence edits. |
| Scoped review | Identified stale pre-archive evidence and plan-only blockers; release docs now distinguish archived planning work from follow-up runtime fixture validation. |

## Exclusions

- No root `README.md` regeneration in this release unit.
- No generated docs or support matrix regeneration in this release unit.
- No live user config, desktop config, credential, or harness apply mutation.
- No broad staging of unrelated files.
- No raw deletion of OpenSpec changes; archive was performed through the OpenSpec workflow.

## Known Risks

- Runtime fixture execution remains a follow-up validation concern for harnesses that still carry `fixture-plan-only` or `docs-ledger-required` statuses.
- Generated docs and instruction mirrors may need a separate docs-steward pass before public release.
- Future cleanup should preserve archived OpenSpec evidence under `openspec/changes/archive/` rather than deleting it as scratch material.
