---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Skill Packaging and Portability

## Packaging requirements

- Preserve the Agent Skills canonical `SKILL.md` format.
- Add repo-specific metadata in `metadata.*`, not new top-level fields unless harness-specific.
- Keep `allowed-tools` marked experimental and harness-dependent.
- Package scripts with deterministic dependency instructions.
- Store large context in `references/`.

## Portability targets

| Target | Preferred path |
|---|---|
| canonical project | `.agents/skills/<name>/SKILL.md` |
| Claude Code compatibility | `.claude/skills/<name>/SKILL.md` |
| OpenCode compatibility | `.opencode/skills/<name>/SKILL.md` or `.agents/skills` |
| Copilot CLI compatibility | `.github/skills`, `.claude/skills`, or `.agents/skills` |
| Antigravity candidate | `.agents/skills` or verified Antigravity path |

## Validation

- frontmatter schema
- name/directory match
- description length
- references exist
- scripts have shebangs or explicit runner
- no accidental secrets
