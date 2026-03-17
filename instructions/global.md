# Global AI Agent Instructions

## General

- Review relevant `AGENTS.md` docs in every project you work in.
- Check for existing (code, servers, etc) before creating anything new.
- Verify, validate, and debug your work before ending your response.
- Use Context7 and relevant tools for up-to-date context; prefer latest dependency versions.
- Install skills: `npx skills add <source> --skill <name> -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode`
- After non-trivial changes in a project with a `docs-steward` skill (`skills/docs-steward/` or `.claude/skills/docs-steward/`), invoke `/docs-steward` to sync dev docs and nested agent instructions.
- Never sign or add self-attribution.

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
5. **DISPATCH**: Default is Pattern E (TeamCreate + nested subagent waves per teammate). Pre-approve permissions before spawning. Use bare subagent waves only when single domain, no coordination, no context pressure. Single session only when there is literally 1 action.
6. **TRACK**: TaskCreate entries before every dispatch. `activeForm` in present continuous. Mark `in_progress` → `completed`. N dispatched = N resolved before advancing.

**Fast path**: Exactly 1 action → single session. All other cases → parallelize.
**Explore-first**: Cannot decompose → spawn parallel exploration team first, then re-enter this gate.

| Tier | Mechanism | Default for |
|------|-----------|-------------|
| **Team + nested waves (Pattern E)** | TeamCreate + subagent waves per teammate — up to ~50 agents total | 2+ independent streams — THE DEFAULT |
| **Subagent wave** | Task tool, parallel calls | 2+ actions, single domain, no coordination, no context pressure |
| **Single session** | Direct | Exactly 1 action |

**Model**: opus everywhere. No exceptions. Never downgrade model for any reason.
**Full guide**: `/orchestrator` for patterns A-F, recovery ladder, anti-patterns.

## Skill Accuracy

### Type Inventory Verification

Before documenting enum values, signal types, or category lists in a skill, read the actual implementation code (classifier prompts, keyword fallbacks, DB enum definitions). Types that exist only in the skill documentation but not in the code are **phantom types** — they will cause silent failures when the agent tries to use them.

### Encryption and Security Claims

Always verify encryption claims against the actual cryptography library and function calls used in the codebase. Common inaccuracies:
- "AES-256" when the code uses Fernet (AES-128-CBC)
- "encrypted" when the code uses XOR or base64 encoding
- "secure storage" when tokens are stored in plaintext

Read the import statements and function calls; do not trust comments or docstrings alone.

### LLM Classifier Documentation

When a skill wraps an LLM-based classifier, document all four of:
1. **Model** — exact model identifier (e.g., `claude-haiku-4-5-20251001`)
2. **Fallback mode** — what happens when the API key is missing or the call fails (e.g., keyword matching)
3. **Confidence threshold** — the minimum score to act on a result (e.g., >= 0.6)
4. **Failure handling** — how the agent should handle classification failures or ambiguous results

## Browser Tools

Prefer `chrome-devtools` MCP for browser automation, testing, and debugging. Fallback: Playwright → Fetcher/Fetch → WebFetch.
