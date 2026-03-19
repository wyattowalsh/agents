# Global AI Agent Instructions

## General

- Review relevant `AGENTS.md` docs in every project you work in.
- Check for existing (code, servers, etc) before creating anything new.
- Verify, validate, and debug your work before ending your response.
- Use llms.txt, Context7, and relevant tools for up-to-date context; prefer latest dependency versions.
- After changes to public APIs, file structure, agent definitions, or skill definitions, invoke `/docs-steward` if available.
- When skills need installing, surface the command to the user: `npx skills add <source> --skill <name> -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode`
- Never sign or add self-attribution.
- Use hooks for deterministic enforcement; reserve instructions for intent and heuristics that require judgment.
- **Precedence**: explicit user instructions override all rules → Clarification Gate governs ambiguous decisions → platform bridge files override global.md on the same topic.

## Clarification Gate

Act on evidence, not belief. Every decision about intent, scope, constraints, approach, and success must trace to the codebase, user's words, or verified conventions. What traces only to inference or defaults is an assumption — and every assumption becomes a question.

**Context-first**: Read code and conventions to ground assumptions in evidence before asking.

**Questions**: Numbered multiple-choice, 2-4 options each with trade-offs and downstream consequences. Batch all at once.

**"Probably" and "obviously" are not evidence.** Surface them as choices.

**Fast path**: Fully grounded → act.

## Orchestration Core

Before any tool-mediated work:

1. **DECOMPOSE**: List every action needed.
2. **CLASSIFY**: Independent (no data dependency) vs dependent.
3. **MAXIMIZE**: Actively split actions further — find every opportunity to parallelize. Each independent action = its own subagent.
4. **CONFLICT CHECK**: Same-file edits → sequential. Everything else → parallel.
5. **DISPATCH**: When team/subagent tools are available (TeamCreate, TaskCreate), default to Pattern E (team + nested subagent waves). Otherwise, maximize parallel tool calls within a single session. Single session only when there is literally 1 action.
6. **TRACK**: Track entries before every dispatch. Mark `in_progress` → `completed`. N dispatched = N resolved before advancing.

**Fast path**: Exactly 1 action → single session. All other cases → parallelize.
**Explore-first**: Cannot decompose → spawn parallel exploration first, then re-enter this gate.

**Model**: opus by default. Platform-specific bridge files may override.
**Full guide**: `/orchestrator` for patterns A-F, recovery ladder, anti-patterns.

## Commit Discipline

In git repositories, commit after each completed logical unit of work — not at the end of the session.

- **Atomic**: one logical change per commit (a feature, a fix, a refactor — not all three)
- **Conventional messages**: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:` prefixes with concise scope and description

## Docs Lookup (`llms.txt`)

For unfamiliar tools/APIs, check `{docs_url}/llms.txt` (index) and `llms-full.txt` (full docs) before web search. Try `{domain}/llms.txt`, `docs.{domain}/llms.txt`, `{domain}/docs/llms.txt`. A 404 is expected — move to the next source.

**Resolution order:** `llms.txt` / `llms-full.txt` → Context7 / doc-search MCP → web search. Prefer `llms-full.txt` over web search — authoritative, versioned, no SEO noise.
