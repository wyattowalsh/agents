# Runtime Compatibility

Use this reference when choosing frontmatter fields, invocation controls,
install paths, scripts, hooks, or distribution paths for a skill. The portable
skill folder can travel across runtimes, but not every frontmatter field or
permission behavior has the same meaning everywhere.

## Contents

1. [Compatibility Tiers](#1-compatibility-tiers)
2. [Runtime Matrix](#2-runtime-matrix)
3. [Invocation Controls](#3-invocation-controls)
4. [Scripts And Permissions](#4-scripts-and-permissions)
5. [Distribution Notes](#5-distribution-notes)
6. [Graceful Degradation](#6-graceful-degradation)

---

## 1. Compatibility Tiers

| Tier | Fields Or Behavior | Guidance |
| --- | --- | --- |
| `portable-core` | `name`, `description`, `license`, `compatibility`, `metadata` | Safe default for all new skills |
| `portable-but-variable` | `allowed-tools`, scripts, references, assets | Use with caveats; runtimes may prompt, ignore, or enforce differently |
| `runtime-specific` | Claude `user-invocable`, `disable-model-invocation`, `context`; Cursor `paths`; Codex `agents/openai.yaml`; hooks/plugins | Keep in runtime projections or with body-level fallback and compatibility note |

Unknown fields should degrade harmlessly. Do not rely on a runtime-specific field
as the only safety control.

## 2. Runtime Matrix

| Runtime | Skill Locations / Distribution | Notable Behavior |
| --- | --- | --- |
| Codex | `.agents/skills`, `$HOME/.agents/skills`, plugins, admin/system paths | Loads name, description, path first; explicit-only policy belongs in `agents/openai.yaml`, not skill frontmatter |
| Claude Code | `.claude/skills`, plugins, managed settings | Rich frontmatter; supports skill invocation controls, hooks, and forked context |
| VS Code / GitHub Copilot | `.github/skills`, `.claude/skills`, `.agents/skills`, user skill dirs | Supports scripts/resources and documented tool approval behavior |
| Cursor | `.agents/skills`, `.cursor/skills`, compatibility paths | Supports `paths` scoping and `disable-model-invocation` for explicit-only use |
| OpenCode | `.opencode/skills`, `~/.config/opencode/skills`, `.agents/skills`, `.claude/skills` | Recognizes a smaller field set; unknown fields are ignored |
| Gemini CLI | `.gemini/skills`, `.agents/skills`, extension/user/workspace skills | Uses activation consent and grants read access to bundled assets after approval |
| Microsoft Agent Framework / Foundry | Toolbox/MCP-hosted skills | Local folder layout matters less than published toolbox/MCP discovery and retrieval |

When current docs are unavailable, state the runtime as "best effort" and keep
the skill portable-core.

## 3. Invocation Controls

| Goal | Portable Guidance | Runtime Notes |
| --- | --- | --- |
| Normal user-facing skill | Omit invocation-control fields | Default slash and implicit behavior is usually correct |
| Manual-only side-effect skill | State manual-only in description/body | Claude/Cursor may use `disable-model-invocation`; Codex uses policy config |
| Background convention skill | State non-invocable role in body | Claude may use `user-invocable: false`; other runtimes may ignore it |
| File-scoped skill | Document scope in description and body | Cursor may use `paths`; others need normal trigger boundaries |

If a runtime ignores the control field, the first body section must still make
the boundary clear.

## 4. Scripts And Permissions

Scripts are portable resources, not portable permissions.

- Keep scripts self-contained and relative-path based.
- Use structured stdout and diagnostics on stderr.
- Document runtime requirements in `compatibility`.
- Use dry-run first for risky behavior.
- Expect some runtimes to prompt before execution, some to sandbox, and some to
  ignore `allowed-tools`.

Do not present `allowed-tools` as a universal security guarantee. It is a
request or hint unless the target runtime documents enforcement.

## 4.1 Runtime-Projected Hooks

Hook policy is runtime-specific unless the target package format explicitly
defines a portable hook execution model. Portable skill source may document the
validation behavior a hook should enforce, but executable hook commands belong
in repo-managed projection config such as `config/hook-registry.json` and the
harness settings generated from it.

Portable `SKILL.md` frontmatter must not depend on repo-root command paths such
as `uv run python skills/<name>/scripts/...`, `{repo_root}`, or
`${workspaceFolder}`. If a hook command is packaged, it must resolve from inside
the installed skill folder or be clearly marked as target-runtime projection
metadata outside the portable skill contract.

## 5. Distribution Notes

| Distribution | Use When |
| --- | --- |
| `npx skills add <source> --skill <name>` | Portable cross-agent install path for supported Skills CLI targets |
| Codex plugin | Bundling repo skills with Codex-specific metadata |
| Claude plugin / managed settings | Claude-native marketplace or managed fleet installs |
| VS Code / Cursor plugin | Editor distribution with skills, commands, agents, rules, or MCP servers |
| Gemini extension or `gemini skills install` | Gemini-specific install and activation flow |
| Microsoft toolbox/MCP publication | Hosted skill discovery through MCP/toolbox mechanisms |

Skill packaging should separate the source skill contract from projection or
plugin distribution metadata.

## 6. Graceful Degradation

Before declaring a skill portable, answer:

1. Does it work with only `name`, `description`, body, and referenced files?
2. If `allowed-tools` is ignored, does the body still prevent unsafe behavior?
3. If invocation-control fields are ignored, does the description still avoid
   accidental triggering?
4. If hooks are unsupported, are validation commands documented?
5. If scripts cannot run, is there a manual fallback or a clear compatibility
   requirement?
6. Are runtime-specific install paths documented without making absolute local
   paths part of the public skill?

Record limitations in `compatibility` or in the skill body. Do not hide them in
generated docs only.
