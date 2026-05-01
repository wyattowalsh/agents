# Dashboard Information Architecture

## Objective

Define an optional dashboard that visualizes the same manifests used by the CLI.

## Views

| View | Purpose |
|---|---|
| Overview | health, drift, support tiers, pending OpenSpec changes |
| Skills | local/external skills, audit status, install targets, provenance |
| MCP | current servers, risk, transport/auth, replacement candidates |
| Harnesses | support matrix and config status per AI tool |
| Transactions | preview/apply/rollback history |
| Docs Truth | stale generated docs and README/instruction drift |
| Task Graph | clusters, critical path, owners, CI gates |
| Source Ledger | official/community sources and freshness |

## Streamlining features

- One-click copy of install commands.
- Risk badges next to every external component.
- “Why not MCP?” explanation for skill-preferred decisions.
- Drift repair wizard.
- Harness detection wizard.
- OpenSpec status panel.
