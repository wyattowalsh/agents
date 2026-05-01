---
status: planning
owner: skill-portability-team
last_updated: 2026-05-01
---

# Skill Portability Layer

## Objective

Project one canonical skill package into harness-specific locations and semantics without losing provenance or support-tier information.

## Projection targets

| Target | Projection behavior |
|---|---|
| Claude Code | copy/symlink skill package; preserve `allowed-tools` only when supported |
| Copilot CLI | project to `.github/skills`, `.agents/skills`, or personal path |
| OpenCode | project to `.opencode/skills` or shared `.agents/skills` |
| Cursor | project as `.agents/skills` plus rules/instructions where needed |
| Codex | project as repo instruction and skills catalog where supported |
| Gemini CLI | wrap as extension/context where pure skills are not native |
| ChatGPT | render as Custom GPT instructions or Apps SDK guidance, not direct local package |

## Portability hazards

- Same skill may have different permission semantics per harness.
- `allowed-tools` is not universally honored.
- Local skill folders may not sync across desktop/web surfaces.
- Some harnesses require restart or reload.
- Some harnesses load both `AGENTS.md` and product-specific instruction files; avoid contradiction.

## Required UX

`wagents install-skill <id>` should show:

- target harnesses
- exact file writes
- permission notes
- reload/restart requirements
- rollback snapshot
- unsupported surfaces
