# External UX Pattern Intake

## Objective

Use the best external UIs and control planes as inspiration for a simpler `wagents` UX without importing unnecessary complexity.

## Patterns to Extract

| Pattern | Candidate Sources | Planned `wagents` Surface |
|---|---|---|
| Agent team kanban | `claude_agent_teams_ui`, `open-cowork`, `agtx` | `wagents dashboard`, future web UI |
| Session sidebar | `opensessions`, `ccmanager`, `cmux` | `wagents sessions` |
| Replay/export | `claude-replay`, `codeg` | `wagents replay export` |
| Token/cost/context telemetry | `agentlytics`, `tokscale`, `context-mode` | `wagents telemetry report` |
| Knowledge graph explorer | `graphify`, `soulforge`, `codebase-memory-mcp` | `wagents context graph` |
| Skill browser/package manager | `skillkit`, `OpenPackage`, `awesome-agent-skills` | `wagents catalog browse/explain/install` |
| Terminal board/canvas | `horizon`, `opentui`, `muxy` | optional TUI dashboard |
| One-click install/sync | `open-cowork`, `caveman`, `open-design` | `wagents bootstrap`, `wagents sync --preview/--apply` |

## Final UX Flows

```text
wagents doctor
wagents bootstrap --preview
wagents bootstrap --apply
wagents catalog browse
wagents catalog explain <id>
wagents skill add <id> --preview
wagents skill add <id> --apply
wagents external audit <repo-url>
wagents mcp inspect <id>
wagents mcp audit --replaceable
wagents context graph --build
wagents sessions list
wagents replay export <session>
wagents sync --preview
wagents sync --apply
wagents rollback
wagents docs check
wagents openspec status
wagents openspec doctor
```

## Transaction Model

All mutating flows must implement:

```text
discover -> resolve -> render -> diff -> backup -> apply -> validate -> rollback -> audit
```
