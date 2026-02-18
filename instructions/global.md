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

1. **DECOMPOSE**: List the actions needed.
2. **CLASSIFY**: Independent (no data dependency) vs dependent.
3. **DISPATCH**: 2+ independent → parallel Task calls in one message. Mix → parallel first, dependent after. All dependent → single session.
4. **CONFLICT CHECK**: Two actions editing the same file → sequential.
5. **TRACK**: For orchestrated work, create TaskCreate entries before dispatch.

**Fast path**: Single-action → skip to single session.
**Explore-first**: Can't decompose without exploration → parallel explore subagents first.

| Tier | Mechanism | Use when |
|------|-----------|----------|
| **Team + waves** | TeamCreate | 3+ domain-crossing streams, coordination needed |
| **Subagent wave** | Task tool, parallel calls | 2+ independent actions |
| **Single session** | Direct | Only 1 action, or all share file dependencies |

**Models**: opus (default), sonnet (routine/mechanical only), haiku (trivial zero-risk only). Never reduce quality to save cost.
**Progress**: TaskCreate before execution. `activeForm` in present continuous. Mark `in_progress` → `completed`. Account for ALL agents (N dispatched = N resolved) before advancing.
**Full guide**: `/orchestrator` for patterns A-F, anti-patterns, team best practices, failure recovery.
