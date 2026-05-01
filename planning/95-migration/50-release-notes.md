# Agents Platform Overhaul Release Notes

## Scope

This release note records the completed planning and control-plane waves for the agents platform overhaul. It is release evidence for readiness review; it does not perform OpenSpec archive, generated docs regeneration, or live harness config mutation.

## Current Committed Range

| Commit | Scope |
| --- | --- |
| `9758f19` | External repository intake foundation. |
| `3e432a8` | Docs instruction planning lane. |
| `6217274` | Cross-harness Chrome DevTools skills. |
| `7a53fc3` | Wave 1 planning lanes. |
| `fa20686` | Wave 2 planning lanes. |
| `9ac8ab5` | Release/archive readiness lane. |

The branch was ahead of `origin/main` by these six commits when this evidence was prepared. Additional readiness evidence may appear after `9ac8ab5`; use `git log --oneline 9ac8ab5..HEAD` during release review to identify the exact final evidence commits. No archive move has been performed in this release note.

## Pending Final Evidence

| Item | Status |
| --- | --- |
| C00/C01 required OpenSpec artifacts | Added as readiness evidence after baseline C09 readiness. |
| Release-note evidence | Added as readiness evidence after baseline C09 readiness. |
| Final rollback range | Use reverse `git log` order for any post-`9ac8ab5` readiness evidence commits. |

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
| `agents-c09-release-archive` | Release and archive readiness planning committed. |
| `agents-c10-external-repo-intake` | External repo intake planning committed. |
| `agents-c11-knowledge-graph-context` | Knowledge graph context adoption planning committed. |
| `agents-c12-session-telemetry` | Session telemetry contract planning committed. |
| `agents-c13-skill-registry-intake` | Skill registry intake planning committed. |
| `agents-c14-multiagent-ui-patterns` | Multiagent UI pattern planning committed. |
| `agents-c15-security-quarantine` | Security quarantine planning committed. |

## Validation Evidence

| Check | Result |
| --- | --- |
| `uv run wagents openspec validate` | Passed 29/29 items after the C00/C01 artifact and release evidence updates. |
| `uv run wagents openspec status --change agents-c00-repo-sync --format json` | `isComplete: true` after adding required artifacts. |
| `uv run wagents openspec status --change agents-c01-registry-core --format json` | `isComplete: true` after adding required artifacts. |
| `uv run wagents openspec status --change agents-platform-overhaul --format json` | Parent change remains `isComplete: true`. |
| Scoped dirty-worktree audit | Confirmed unrelated dirty files remain unstaged and must not be swept into release staging. |

## Exclusions

- No root `README.md` regeneration in this release unit.
- No generated docs or support matrix regeneration in this release unit.
- No live user config, desktop config, credential, or harness apply mutation.
- No broad staging of unrelated dirty files.
- No OpenSpec archive move until archive approval and post-release gates pass.

## Known Risks

- The worktree contains unrelated dirty tracked and untracked files, so every follow-up must stage explicit pathspecs only.
- Generated docs and instruction mirrors may need a separate docs-steward pass before public release.
- OpenSpec archive remains blocked until final validation evidence is re-run and archive approval is explicit.
