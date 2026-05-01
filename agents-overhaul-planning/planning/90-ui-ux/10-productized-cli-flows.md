# Productized CLI Flows

## Objective

Make `wagents` feel like a coherent product rather than a collection of scripts.

## Core flows

### First-run bootstrap

```bash
wagents doctor
wagents catalog list skills --recommended
wagents sync --preview --agent claude-code --agent cursor-agent
wagents sync --apply --agent claude-code --agent cursor-agent
```

### Skill install

```bash
wagents skills search docs
wagents skills explain github/awesome-copilot documentation-writer
wagents skills preview github/awesome-copilot documentation-writer
wagents skills install github/awesome-copilot documentation-writer --pin v1.2.0 --agent github-copilot-cli --preview
wagents skills install github/awesome-copilot documentation-writer --pin v1.2.0 --agent github-copilot-cli --apply
```

### MCP audit

```bash
wagents mcp audit --from mcp.json
wagents mcp classify --replaceable
wagents mcp scan --tool mcp-scan
wagents mcp sync --preview --profile docs-lookup
```

### Rollback

```bash
wagents rollback --last
wagents rollback <transaction-id>
```

## UX principles

- Show what will change before changing it.
- Prefer recommendations with rationale over raw lists.
- Make support tier and risk visible in every catalog row.
- Collapse advanced fields by default.
- Provide `--json` for automation.
