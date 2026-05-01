# Streamlined UI/UX Blueprint

## Objective

Make the system easy to use without sacrificing safety.

## Core UX principle

Users should not need to know every harness-specific path. They should choose intent, preview changes, and let the system explain what will happen.

## Command surface

```bash
wagents doctor
wagents catalog browse
wagents catalog explain <capability-id>
wagents skill add <source> --preview
wagents skill add <source> --apply
wagents mcp inspect <id>
wagents mcp enable <id> --preview
wagents sync --agent claude-code --preview
wagents sync --agent claude-code --apply
wagents rollback
wagents docs check
wagents openspec status
```

## UX flows

### One-command health check

`wagents doctor` should show:

- detected harnesses;
- missing prerequisites;
- stale generated files;
- unsafe MCPs;
- unvalidated skills;
- OpenSpec active changes;
- suggested next command.

### Skill browser

`wagents catalog browse` should support:

- skill/plugin/MCP filter;
- support-tier filter;
- harness compatibility filter;
- risk filter;
- install preview;
- source/trust summary.

### Sync preview

`wagents sync --preview` should show:

- files to create/update/delete;
- generated docs changes;
- config writes;
- risks and required approvals;
- rollback snapshot plan.

### Guided remediation

When validation fails, show:

- root cause;
- affected harness;
- exact file/setting;
- safe remediation command;
- docs link.

## Optional dashboard

The dashboard should render the same registry and transaction state as the CLI:

- harness support matrix;
- skill catalog;
- MCP audit board;
- config drift board;
- transaction history;
- OpenSpec status;
- CI/eval reports.
