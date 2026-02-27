# Session Commands

In-session command protocols for Deep/Exhaustive interactive research sessions. Read when the user issues a command during an active session.

## Command Reference

| Command | Description |
|---------|-------------|
| `drill <#>` | Deep dive into a specific finding |
| `pivot <angle>` | Redirect research to a new sub-question |
| `counter <#>` | Search for evidence against a finding |
| `export` | Render HTML dashboard |
| `status` | Show current research state |
| `sources` | List all sources consulted |
| `confidence` | Show confidence distribution |
| `gaps` | List identified knowledge gaps |
| `?` | Show this command menu |

## Protocols

### `drill <#>`

Load finding RR-{#} from the current session. Spawn 2-3 targeted search subagents to find more sources on this specific claim. Each subagent uses a different search tool. Update the finding's evidence chain and recalculate confidence. Save updated journal.

### `pivot <angle>`

Add `<angle>` as a new sub-question to the current session. Spawn targeted search subagents scoped to this angle. Append results to the current wave. Do not discard existing findings. Save updated journal.

### `counter <#>`

Spawn a devil's advocate subagent for finding RR-{#}. The subagent explicitly searches for evidence AGAINST the claim using different search engines than those that found the original evidence. Report counter-evidence and adjust confidence: weakened -0.10, disproven set to 0.0, survives +0.05. Save updated journal.

### `export`

Read `references/dashboard-schema.md`. Format all current findings, contradictions, sources, and metadata as JSON matching the schema. Inject into the HTML dashboard template. Write to `~/.claude/research/exports/{journal-slug}.html`. Report the file path.

### `status`

Display without advancing research:
```
Current wave: [N]
Findings: [N] total ([N] high, [N] medium, [N] low confidence)
Contradictions: [N]
Leads pending: [N]
Gaps: [N]
Sources consulted: [N]
Next action: [description of what the next wave will do]
```

### `sources`

List all sources consulted in the current session:
```
| # | URL | Tool | Accessed | Referenced By |
|---|-----|------|----------|---------------|
| 1 | [url] | [tool] | [timestamp] | RR-001, RR-003 |
| 2 | [url] | [tool] | [timestamp] | RR-002 |
```

### `confidence`

Show confidence distribution across all current findings:
```
High   (0.8-1.0): [N] findings  ████████████████░░░░
Medium (0.5-0.7): [N] findings  ██████████░░░░░░░░░░
Low    (0.3-0.4): [N] findings  ████░░░░░░░░░░░░░░░░
Uncertain (<0.3): [N] findings  ██░░░░░░░░░░░░░░░░░░

Mean confidence: [0.XX]
```

### `gaps`

List all identified knowledge gaps from all waves:
```
1. [gap description] — identified in Wave [N], [N] search attempts
2. [gap description] — identified in Wave [N], [N] search attempts
```

### `?`

Display the command reference table from the top of this file.
