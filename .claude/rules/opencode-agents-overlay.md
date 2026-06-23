---
paths:
  - "**/*"
---

# OpenCode Agent Runtime Overlay

This file contains OpenCode-specific runtime configuration for the agents defined in `agents/*.md`. It is loaded exclusively by the OpenCode harness and is ignored by Codex, Claude Code, and Grok routes.

## Purpose

The portable agent contract (documented in `AGENTS.md`) defines a minimal, cross-platform schema. OpenCode extends this schema with runtime-specific keys for subagent behavior, UI theming, and granular permission rules. These extensions are stored here to keep the canonical agent definitions portable.

## Custom Keys (OpenCode-only)

| Field         | Type   | Description                                 | Values                              |
| ------------- | ------ | ------------------------------------------- | ----------------------------------- |
| `mode`        | string | Subagent execution mode                     | `subagent`                          |
| `temperature` | float  | Sampling temperature for the agent          | `0.1` (focused) or `0.2` (balanced) |
| `color`       | string | UI color token in the OpenCode TUI          | `primary`, `secondary`, etc.        |
| `permission`  | object | Nested permission rules for tool categories | `edit`, `bash`, `webfetch`, `task`  |

## Agent Runtime Configuration

### researcher

```yaml
mode: subagent
temperature: 0.1
color: primary
permission:
  edit: deny
  bash:
    "*": ask
    "ls *": allow
    "rg *": allow
    "git log*": allow
  webfetch: allow
```

### orchestrator

```yaml
mode: subagent
temperature: 0.1
color: primary
permission:
  edit: deny
  bash: ask
  webfetch: ask
  task:
    "*": deny
    "general": allow
    "explore": allow
    "planner": allow
    "researcher": allow
    "code-reviewer": allow
    "docs-writer": allow
    "security-auditor": allow
    "release-manager": allow
    "performance-profiler": allow
```

### planner

```yaml
mode: subagent
temperature: 0.1
color: info
permission:
  edit: deny
  bash:
    "*": ask
    "ls *": allow
    "rg *": allow
    "git status*": allow
    "git diff*": allow
    "git log*": allow
  webfetch: ask
```

### code-reviewer

```yaml
mode: subagent
temperature: 0.1
color: warning
permission:
  edit: deny
  bash:
    "*": ask
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "rg *": allow
  webfetch: deny
```

### security-auditor

```yaml
mode: subagent
temperature: 0.1
color: error
permission:
  edit: deny
  bash:
    "*": ask
    "git diff*": allow
    "git log*": allow
    "rg *": allow
  webfetch: allow
```

### performance-profiler

```yaml
mode: subagent
temperature: 0.1
color: secondary
permission:
  edit: deny
  bash:
    "*": ask
    "git diff*": allow
    "rg *": allow
  webfetch: ask
```

### release-manager

```yaml
mode: subagent
temperature: 0.1
color: success
permission:
  bash:
    "*": ask
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "git tag*": ask
    "gh release*": ask
  webfetch: ask
```

### docs-writer

```yaml
mode: subagent
temperature: 0.2
color: accent
permission:
  bash:
    "*": ask
    "ls *": allow
    "rg *": allow
  webfetch: ask
```

## Notes

- These configurations are applied at runtime by the OpenCode harness when the corresponding agent is invoked via the `task` tool or subagent delegation.
- Model selection is **not** stored here. It belongs in `opencode.json` (root `model` / `small_model` or per-agent `model` overrides in the TUI).
- Permission rules use a simple `allow` / `ask` / `deny` vocabulary. Patterns support globs (`*`) and exact command prefixes.
- This file is **not** part of the portable agent contract. It is an implementation detail of the OpenCode harness integration.

## Maintenance

When a new agent is added to `agents/`, add its runtime configuration here if it uses custom keys. Keep the portable frontmatter in the `.md` file minimal (`name`, `description`, and any documented optional fields).
