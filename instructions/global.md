# Global AI Agent Instructions

## General

- Review relevant `AGENTS.md` docs in every project you work in.
- Check for existing (code, servers, etc) before creating anything new.
- Verify, validate, and debug your work before ending your response.
- Use Context7 and relevant tools for up-to-date context; prefer latest dependency versions.
- Install skills: `npx skills add <source> --skill <name> -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode`
- Never sign or add self-attribution.

## Orchestration Core

Before any tool-mediated work:

1. **DECOMPOSE**: List every action needed.
2. **CLASSIFY**: Independent (no data dependency) vs dependent.
3. **MAXIMIZE**: Actively split actions further — find every opportunity to parallelize.
4. **CONFLICT CHECK**: Same-file edits → sequential. Everything else → parallel.
5. **DISPATCH**: Default to TeamCreate with parallel subagent waves inside each teammate (Pattern E). Use bare subagent waves only when a team adds no value. Single session only when there is literally 1 action.
6. **TRACK**: TaskCreate entries before every dispatch. `activeForm` in present continuous. Mark `in_progress` → `completed`. N dispatched = N resolved before advancing.

**Fast path**: Exactly 1 action → single session. All other cases → parallelize.
**Explore-first**: Cannot decompose → spawn parallel exploration team first, then re-enter this gate.

| Tier | Mechanism | Default for |
|------|-----------|-------------|
| **Team + nested waves** | TeamCreate + subagent waves per teammate | 2+ independent streams (DEFAULT) |
| **Subagent wave** | Task tool, parallel calls | 2+ actions, single domain, no coordination needed |
| **Single session** | Direct | Exactly 1 action |

**Model**: opus everywhere. No exceptions. Never downgrade model for any reason.
**Full guide**: `/orchestrator` for patterns A-F, recovery ladder, anti-patterns.
