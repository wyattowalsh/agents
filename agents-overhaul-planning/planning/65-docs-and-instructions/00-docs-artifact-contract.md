# Docs Artifact Contract

## Artifact classes

| Class | Examples | Source of truth | CI gate |
|---|---|---|---|
| Source instruction | `instructions/global.md` | human-owned | lint + link check |
| Harness wrapper | `CLAUDE.md`, `GEMINI.md` | generated or thin wrapper | docs truth |
| Generated catalog | README skills table, docs skill pages | manifests + repo inventory | generation check |
| Support matrix | harness matrix | harness registry | schema + generation check |
| Audit report | MCP/skill audit docs | audit command output | freshness check |
| OpenSpec | proposal/design/tasks/specs | human + OpenSpec tooling | openspec validate |

## Required metadata for generated docs

Generated docs should include:

```text
Generated from: <manifest path>
Source hash: <hash>
Generated at: <timestamp>
Do not edit by hand.
```

## Required review

Docs changes touching support claims require Harness Registry Team review. Docs changes touching install commands require CLI/Adapter Team review. Docs changes touching security warnings require Security Team review.
