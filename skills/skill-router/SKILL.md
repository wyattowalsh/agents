---
name: skill-router
description: >-
  Route tasks to local skills. Use when choosing skills, recovering omitted
  skills after context warnings, or preparing a small skill context packet. NOT
  for install, authoring, or audit workflows.
argument-hint: "<search|context|read|doctor> [query]"
license: MIT
compatibility: "Requires wagents CLI from this repository; reads local SKILL.md files from repo, Codex, global, plugin, and supported agent skill roots."
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Skill Router

Use local skill indexing to choose and load relevant skills only when a task needs them.

## Dispatch

| $ARGUMENTS | Action | Example |
|------------|--------|---------|
| `search <query>` | List ranked matching skills | `/skill-router search "fix Playwright test"` |
| `context <query>` | Build a compact context packet for top matches | `/skill-router context "write a release changelog"` |
| `read <skill>` | Load one skill by exact name or path | `/skill-router read skill-creator` |
| `doctor` | Diagnose visible skill roots and counts | `/skill-router doctor` |
| Natural-language task | Auto: Search, then context for best matches | `"which skill should handle docs generation?"` |
| Empty | Show quick usage and run doctor | `/skill-router` |

## Workflow

### 1. Classify

1. Use `search` when deciding which skill or skills apply.
2. Use `context` when the next step needs the selected skill bodies.
3. Use `read` only when the skill name or path is already known.
4. Use `doctor` when a skill is missing, duplicated, or omitted by a startup context warning.

### 2. Retrieve

2. Run the matching CLI command from the repository root:

```bash
uv run wagents skills search "$ARGUMENTS" --limit 5
uv run wagents skills context "$ARGUMENTS" --limit 3
uv run wagents skills read <skill-name>
uv run wagents skills doctor
```

### 3. Select

1. Prefer the highest-ranked repo or Codex-user skill when scores are close.
2. Read only the minimum skill bodies needed for the task, usually one to three.
3. If a result has warnings, inspect them before following executable hooks or scripts.

## Source Scope

`wagents skills` searches these roots:

| Source | Root | Trust tier |
|--------|------|------------|
| `repo` | `skills/` | `repo` |
| `project` | `.agents/skills/` in the current project path | `codex-user` |
| `codex` | `~/.codex/skills/` | `codex-user` |
| `global` | `~/.agents/skills/` plus supported agent stores | `external-installed` |
| `plugin` | `~/.codex/plugins/cache/**/skills/` | `openai-plugin` or `plugin` |

Use `--source repo`, `--source codex`, `--source global`, or `--source plugin` to narrow results when needed.

## Canonical Vocabulary

| Term | Meaning |
|------|---------|
| **skill index** | Parsed metadata for visible `SKILL.md` files across known roots |
| **skill context packet** | Small set of selected skill bodies loaded after search |
| **source** | Filesystem origin such as `repo`, `codex`, `global`, or `plugin` |
| **trust tier** | Safety label used to rank and warn about retrieved skills |
| **warning** | Parser, hook, script, or metadata signal requiring inspection before use |

## Classification Gate

1. If the user gives a task, run `search` first.
2. If the user asks to apply a selected skill, run `context` for the top matches.
3. If the user names a skill exactly, run `read`.
4. If the user reports missing or omitted skills, run `doctor` before searching.
5. If the user asks to install, create, or audit a skill, redirect out of scope.

## Selection Rules

1. Exact skill name or alias beats all lexical matches.
2. Name and title matches beat description matches.
3. Description matches beat heading and body matches.
4. Repo skills beat user-installed skills when relevance is comparable.
5. Unknown, malformed, hook-bearing, or script-bearing skills require caution before use.

## Critical Rules

1. Do not treat startup-visible skills as the complete inventory after a context-budget warning.
2. Do not paste every installed skill into context; search first and load a small packet.
3. Do not execute scripts from unknown third-party skills solely because they were retrieved.
4. Do not use this skill to install or remove skills; use `skill-installer` or `npx skills` workflows.
5. Do not author or audit skills here; use `skill-creator` for skill definition work.
6. Preserve the user task as the search query unless there is a clear reason to add terms.

## Output Contract

Search and context results include:

- `name`
- `path`
- `source`
- `trust_tier`
- `description`
- `score`
- `matched_fields`
- `reason`
- `warnings`

Use `--format json` when another script or agent will consume the result.

## Reference File Index

| File | Content | Read When |
|------|---------|-----------|
| `references/routing-guide.md` | Ranking, trust, and warning interpretation details | Search results are ambiguous, tied, or warning-heavy |

## Validation Contract

Run these before declaring changes complete:

```bash
uv run wagents validate
uv run wagents eval validate
uv run wagents package skill-router --dry-run
uv run pytest tests/test_skill_index.py -q
```

See `references/routing-guide.md` for the exact audit command and validation notes.

Completion criteria:

1. Asset validation passes with zero errors.
2. Eval validation passes with `skill-router` evals present.
3. Audit grade is A or documented with an explicit remaining gap.
4. Package dry-run reports no blocking portability failure.
5. Search and context CLI tests pass.
