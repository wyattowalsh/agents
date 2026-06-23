# SKILL.md Frontmatter Field Catalog

Complete field reference for SKILL.md YAML frontmatter in this repository.

## Contents

1. [Required Fields](#1-required-fields)
2. [Compatibility Tiers](#2-compatibility-tiers)
3. [Cross-Platform Fields](#3-cross-platform-fields-agentskillsio-spec)
4. [Runtime-Specific Extensions](#4-runtime-specific-extensions)
5. [Invocation Control Matrix](#5-invocation-control-matrix)
6. [Decision Tree](#6-decision-tree)
7. [Golden Example](#7-golden-example)

---

## 1. Required Fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | kebab-case (`^[a-z0-9][a-z0-9-]*$`), max 64 chars, must match directory name |
| `description` | string | non-empty, max 1024 chars |

**`name`:** Lowercase alphanumeric and hyphens only. No consecutive hyphens (`--`), no leading/trailing hyphens. Must exactly match the enclosing directory name under `skills/`. Reserved words prohibited: `anthropic`, `claude`.

> **Note:** In Claude Code, the `name` field is technically optional -- Claude Code derives the skill name from the directory name. However, it should always be populated for cross-agent compatibility.

**`description`:** No XML tags. CSO-optimized for discovery: write in third person, cover what the skill does, when to use it, and when NOT to use it. Include keyword variations for agent/search matching. Use YAML block scalar (`>-`) for multi-line descriptions.

---

## 2. Compatibility Tiers

Use `references/runtime-compatibility.md` for the full runtime matrix.

| Tier | Fields / Behavior | Guidance |
|------|-------------------|----------|
| `portable-core` | `name`, `description`, `license`, `compatibility`, `metadata` | Safe default for all new skills |
| `portable-but-variable` | `allowed-tools`, scripts, references, assets | Support varies; document fallback behavior |
| `runtime-specific` | Claude `user-invocable`, `disable-model-invocation`, `context`, `agent`, `hooks`; Cursor `paths`; Codex `agents/openai.yaml`; plugins/settings | Add only when needed and include a body-level fallback |

Unknown fields should degrade harmlessly. Do not rely on a runtime-specific field
as the only safety or invocation control.

---

## 3. Cross-Platform Fields (agentskills.io spec)

Always populate for multi-agent installability via `npx skills add`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `license` | string | -- | SPDX identifier (e.g., `MIT`, `Apache-2.0`) or `SEE LICENSE IN <filename>` |
| `compatibility` | string | -- | Environment requirements, max 500 chars |
| `allowed-tools` | string | -- | Space-delimited tool allowlist; experimental and runtime-dependent |
| `metadata.author` | string | -- | Skill author name or handle |
| `metadata.version` | string | -- | Semantic version string (e.g., `"1.0.0"`) |
| `metadata.internal` | boolean | `false` | If true, hidden unless `INSTALL_INTERNAL_SKILLS=1` |

```yaml
metadata:
  author: username
  version: "1.0.0"
```

---

## 4. Runtime-Specific Extensions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `argument-hint` | string | -- | Shown during autocomplete (e.g., `"[query]"`, `"<mode> [name]"`) |
| `model` | string | -- | Model override: `sonnet` \| `opus` \| `haiku` |
| `context` | string | -- | `fork` to run in an isolated subagent |
| `agent` | string | -- | Subagent type when `context: fork` (e.g., `Explore`) |
| `user-invocable` | boolean | `true` | Set `false` to hide from `/` menu |
| `disable-model-invocation` | boolean | `false` | Set `true` to prevent auto-invocation |
| `hooks` | object | -- | Runtime-specific lifecycle hooks scoped to this skill |
| `paths` | list/string | -- | Cursor-style file scope; use only for runtimes that document it |

- **`model`** -- `opus` for complex multi-step skills; `sonnet` for focused tasks. Omit to inherit session default.
- **`context: fork`** -- Use when skill produces verbose output or needs isolation from the user's state.
- **`agent`** -- Only meaningful when `context: fork` is set. Names the agent definition the subagent loads.
- **`argument-hint`** -- Angle brackets for required args (`<mode>`), square brackets for optional (`[path]`).
- **`hooks`** -- `PreToolUse` / `PostToolUse` matchers for runtimes that support skill-scoped hooks. Prefer repo-managed hook projection for portable distribution.
- **`disable-model-invocation`** -- Supported by some runtimes for manual-only skills. Codex uses external policy config instead of this field.
- **`allowed-tools`** -- Treat as a permission request or hint unless the target runtime documents enforcement.

```yaml
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - command: "test -f SKILL.md || (echo 'ERROR: SKILL.md not found' >&2; exit 2)"
```

Do not put repo-root commands such as `uv run python skills/<name>/scripts/...`,
`{repo_root}`, or `${workspaceFolder}` in portable skill frontmatter. Keep those
commands in runtime projection config, or make the command resolve from inside
the packaged skill folder.

---

## 5. Invocation Control Matrix

| `user-invocable` | `disable-model-invocation` | Visibility | Use Case |
|---|---|---|---|
| `true` (default) | `false` (default) | Slash command + auto | Most skills -- available everywhere |
| `true` | `true` | Slash command only | Should not auto-fire (e.g., destructive ops) |
| `false` | `false` | Auto-invocation only | Background knowledge (conventions, style guides) |
| `false` | `true` | Effectively disabled | Maintenance or deprecated skills |

Defaults are correct for most skills. Override only when a skill has side effects requiring explicit opt-in (`disable-model-invocation: true`) or provides passive context only (`user-invocable: false`).

---

## 6. Decision Tree

```
Modifies files / side effects?  YES --> Document hook behavior or add runtime-projected hooks
Complex / multi-step?           YES --> model: opus
Verbose output?                 YES --> context: fork
Background knowledge only?      YES --> user-invocable: false
Manual-only invocation?         YES --> disable-model-invocation: true
Accepts arguments?              YES --> Add argument-hint
Distributed to other agents?    YES --> Populate cross-platform fields
Restrict available tools?       YES --> Set allowed-tools and document fallback
Runtime-specific invocation?    YES --> Add field plus body fallback
```

- **`allowed-tools`:** Set to a space-delimited list of tool names the agent is permitted to use while the skill is active when the runtime supports it (e.g., `Read Grep Glob Bash`). Omit when no restriction is needed. Never present it as a universal security guarantee.

All NO answers mean omit that field (use defaults).

---

## 7. Golden Example

```yaml
---
name: my-analyzer
description: >-
  Analyze codebases for architectural patterns, anti-patterns, and
  improvement opportunities. Modes: scan for quick overview, deep
  for comprehensive analysis, compare for cross-project benchmarking.
  Use when reviewing architecture, onboarding to a new codebase, or
  preparing for refactoring. NOT for runtime profiling or debugging.
argument-hint: "<mode> [path]"
model: opus
license: MIT
compatibility: "Requires git. Python 3.10+ for optional scripts."
metadata:
  author: username
  version: "1.0.0"
allowed-tools: Read Grep Glob Bash
---
```

**Why each field is set:**

- `model: opus` -- multi-mode skill with deep analysis requires strong reasoning.
- `argument-hint` -- `<mode>` is required (scan/deep/compare), `[path]` is optional (defaults to cwd).
- Cross-platform fields populated for distribution via `npx skills add`.
- `allowed-tools` -- documents the intended tool boundary, but the body must still describe fallback behavior for runtimes that ignore it.
- Hook behavior belongs in the body or runtime projection config unless the target runtime and package format both support portable skill-scoped hooks.
- `user-invocable` / `disable-model-invocation` omitted -- defaults are correct for a user-facing interactive skill.
