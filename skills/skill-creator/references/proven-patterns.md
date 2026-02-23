# Proven Patterns

Structural patterns extracted from the best skills in this repository. Each pattern includes what it is, when to use it, a concrete snippet from an actual skill, and implementation guidance.

## Contents

1. [Dispatch Table](#1-dispatch-table)
2. [Reference File Index](#2-reference-file-index)
3. [Critical Rules](#3-critical-rules)
4. [Canonical Vocabulary](#4-canonical-vocabulary)
5. [Scope Boundaries](#5-scope-boundaries)
6. [Classification/Gating Logic](#6-classificationgating-logic)
7. [Scaling Strategy](#7-scaling-strategy)
8. [State Management](#8-state-management)
9. [Scripts](#9-scripts)
10. [Templates](#10-templates)
11. [Hooks](#11-hooks)
12. [Progressive Disclosure](#12-progressive-disclosure)
13. [Body Substitutions](#13-body-substitutions)
14. [Stop Hooks](#14-stop-hooks)

---

## 1. Dispatch Table

A markdown table routing `$ARGUMENTS` to specific modes or actions. First column is the argument pattern, second is the action. Must include an empty-args handler row.

**When to use:** Every skill that accepts arguments. Even single-mode skills benefit from documenting empty-args behavior.

**Snippet (prompt-engineer):**

```markdown
| $ARGUMENTS | Action |
|------------|--------|
| `craft <description>` | -> Mode A: Craft a new prompt from scratch |
| `optimize <prompt or path>` | -> Mode B: Optimize an existing prompt |
| `audit <prompt or path>` | -> Mode C: Audit a prompt (read-only report) |
| Natural-language request | -> Auto-detect: Mode A (Craft) |
| Empty | Show mode menu with examples |
```

**Guidance:** Place immediately after the skill title. The empty-args row should present a gallery, menu, or help text -- never silently fail.

---

## 2. Reference File Index

A table mapping reference files to their content and when to load them. Prevents loading all references at once (wasting context) or guessing content.

**When to use:** Any skill with 2+ reference files. Critical for 4+ references.

**Snippet (mcp-creator):**

```markdown
| File | Content | Load during |
|------|---------|-------------|
| `references/fastmcp-v3-api.md` | Complete v3 API surface | Phase 3 |
| `references/tool-design.md` | LLM-optimized naming, descriptions, parameters | Phase 1, 3 |
| `references/testing.md` | pytest setup, test categories, 15-item checklist | Phase 4 |
| `references/common-errors.md` | 20 errors: symptom -> cause -> solution | Debug mode |
```

**Guidance:** Include "Do not load all at once" near the index. The "Content" column must be specific enough for the agent to decide whether to load without reading the file.

---

## 3. Critical Rules

A numbered list of non-negotiable constraints. Each rule is testable (you can verify compliance) and imperative ("Do X" or "Never Y"). Separate from principles (which explain why).

**When to use:** Every skill. Target 5-15 rules.

**Snippet (wargame):**

```markdown
1. Label ALL outputs as exploratory, not predictive (RAND guardrail)
2. Always allow the user to override the classification tier
3. Never skip AAR in Interactive Wargame mode -- it is where learning happens
4. Force trade-offs -- every option must have explicit downsides
5. Name biases explicitly when detected -- both human and LLM
```

**Guidance:** Rules must be falsifiable -- a reviewer can check compliance. Avoid vague rules. Place near the end of the body so the agent processes them as final constraints.

---

## 4. Canonical Vocabulary

A section defining the exact terms used throughout the skill. Prevents terminology drift where the agent uses synonyms that confuse users.

**When to use:** Any skill with 3+ domain-specific terms, multiple modes, or severity levels.

**Snippet (wargame):**

```markdown
**Canonical terms** (use these exactly throughout):
- Tiers: "Clear", "Complicated", "Complex", "Chaotic"
- Modes: "Quick Analysis", "Structured Analysis", "Interactive Wargame"
- Difficulty levels: "optimistic", "realistic", "adversarial", "worst-case"
```

**Guidance:** Place within or after Critical Rules. Use "use these exactly throughout" to signal these are not suggestions. Group by category.

---

## 5. Scope Boundaries

Explicit statements of what the skill is NOT for. Prevents misapplication to adjacent but wrong tasks.

**When to use:** Always. Place in both the frontmatter description and the body.

**Snippet (honest-review):**

```
NOT for writing new code, explaining code, or benchmarking.
```

**Snippet (prompt-engineer):**

```
NOT for running prompts or generating content.
```

**Guidance:** State boundaries in the frontmatter `description` so they appear during skill discovery. Use the exact phrase "NOT for" -- direct and unambiguous. List 2-4 exclusions covering the most likely misapplications.

---

## 6. Classification/Gating Logic

A scoring system that determines which workflow path to follow. Prevents one-size-fits-all treatment of inputs with different complexity levels.

**When to use:** Skills with 3+ modes where input complexity should determine the mode. Not needed for simple 2-mode skills.

**Snippet (wargame complexity classifier):**

```markdown
Score each dimension 0-2, sum for tier:

| Dimension       | 0 (Low)          | 1 (Medium)          | 2 (High)              |
|-----------------|-------------------|---------------------|-----------------------|
| Adversary       | None/passive      | Reactive            | Adaptive/intelligent  |
| Reversibility   | Fully reversible  | Partially           | Irreversible          |
| Time pressure   | None              | Days/weeks          | Hours or less         |
| Stakeholders    | Single            | 2-3 groups          | 4+ with conflicts     |
| Information     | Complete          | Partial gaps        | Fog / deception       |

| Total Score | Tier          | Mode                  |
|-------------|---------------|-----------------------|
| 0-3         | Clear         | Quick Analysis        |
| 4-6         | Complicated   | Structured Analysis   |
| 7-8         | Complex       | Interactive Wargame   |
| 9-10        | Chaotic       | Interactive Wargame   |
```

**Guidance:** Show the rubric to the user for verification. Always allow user override. Include "Why This Tier" after scoring. Dimensions should be orthogonal.

---

## 7. Scaling Strategy

A table mapping input size to execution strategy, including when to use subagents or teams.

**When to use:** Skills that process variable-sized inputs where strategy should adapt.

**Snippet (honest-review):**

```markdown
| Scope | Strategy |
|-------|----------|
| 1-2 files | Inline review at all 3 levels |
| 3-5 files | Spawn 3 parallel reviewer subagents |
| 6+ files | Spawn a team with domain-specific reviewers |
```

**Guidance:** Define at least 3 tiers. For team-based tiers, sketch the structure showing roles and wave patterns. Enforce file ownership boundaries -- no two agents edit the same file. Use concrete thresholds, not vague qualifiers.

---

## 8. State Management

A protocol for persisting state between sessions: save location, filename convention, resume protocol, and list/discovery commands.

**When to use:** Multi-turn interactive skills, skills generating artifacts users revisit, skills with "resume" semantics.

**Snippet (wargame):**

```markdown
- Journal directory: `~/.claude/wargames/`
- Create the directory on first use with `mkdir -p`
- Filename: `{YYYY-MM-DD}-{scenario-slug}.md`
- Save after EVERY turn in Interactive Wargame mode
- Resume: read journal, reconstruct state, continue from last turn
- Collision: append version suffix (`-v2.md`)
```

**Guidance:** Use `~/.claude/<skill-name>/` as default directory. Define filename convention with an explicit template. Support `resume` and `list` commands in the dispatch table. Handle collisions with version suffixes.

---

## 9. Scripts

Python scripts invoked via Bash from SKILL.md. Follow the argparse + JSON-to-stdout pattern.

**When to use:** Detection or analysis better handled by deterministic code. Validation steps needing consistent results. Structured output parsing.

**Snippet (add-badges SKILL.md):**

```markdown
## Phase 1 -- Detect
Run the detection script via the Bash tool:
```
uv run python skills/add-badges/scripts/detect.py <path>
```
Parse the JSON output.
```

**Guidance:** Place in `skills/<name>/scripts/`. Use `argparse`. JSON to stdout, diagnostics to stderr. Include a manual fallback in the body for when the script fails. Follow add-badges/detect.py as reference.

---

## 10. Templates

Self-contained HTML files with JSON-in-script data injection for visual dashboards and reports.

**When to use:** Skills producing visual dashboards or styled reports beyond plain markdown.

**Key pattern elements:**

```html
<script id="data" type="application/json">{ "view": "dashboard" }</script>
```

- CSS custom properties: `:root { --bg, --card, --border, --text, --dim, --accent }`
- Dark mode default with `@media (prefers-color-scheme: light)` override
- Vanilla JS IIFE rendering, `escH()` for HTML escaping
- Error fallback for JSON parse failures

**Guidance:** Place in `skills/<name>/templates/`. No external CDN dependencies. The agent copies to `/tmp/`, injects JSON, renders via Playwright or browser. Never load templates into LLM context.

---

## 11. Hooks

Lifecycle hooks in frontmatter guarding against dangerous operations.

**When to use:** Skills modifying important files (README, configs). Guards against overwriting uncommitted changes.

**Snippet -- PreToolUse (add-badges):**

```yaml
hooks:
  PreToolUse:
    - matcher: Edit
      hooks:
        - command: "git diff --quiet HEAD -- README.md 2>/dev/null || echo 'WARNING: README.md has uncommitted changes'"
```

**Snippet -- PostToolUse (validation after write):**

```yaml
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - command: "uv run wagents validate 2>&1 | tail -5"
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Allow -- tool use proceeds (PreToolUse) or result accepted (PostToolUse) |
| 1 | Block -- tool use prevented (PreToolUse) or result suppressed (PostToolUse) |
| 2 | Block with feedback -- same as 1, but stderr is shown to the agent as guidance |

**Guidance:** Use `PreToolUse` with a `matcher` for the guarded tool (Edit, Write, Bash). Use `PostToolUse` for validation or cleanup after tool execution. Hooks should warn, not block, unless safety-critical. Keep commands fast (<1s) since they run on every matched invocation.

---

## 12. Progressive Disclosure

Information layered across 4 levels to manage context window budget. This is the meta-pattern governing how all content is organized.

**When to use:** Every skill -- this is the fundamental structuring principle.

**The four levels:**

1. **Frontmatter** -- metadata, discovery (~100 tokens). Loaded for all skills during listing.
2. **SKILL.md body** -- dispatch, workflows, rules (<5k tokens). Loaded on activation. Under 500 lines.
3. **References** -- deep knowledge, specs (variable). Loaded on demand per the index.
4. **Scripts/Templates** -- executables (never loaded into context). Invoked via Bash only.

**Guidance:** Keep body under 500 lines. Move sections over 100 lines to references. Never embed executable logic in the body. The body should give a complete mental model of the workflow without any references loaded.

---

## 13. Body Substitutions

Variable substitutions in SKILL.md resolved at invocation time.

**When to use:** Every skill accepting arguments. Session ID for state management. Inline commands sparingly.

**Available substitutions:**

| Substitution | Expansion |
|--------------|-----------|
| `$ARGUMENTS` | Full argument string |
| `$ARGUMENTS[N]` / `$N` | Nth argument (0-indexed) |
| `${CLAUDE_SESSION_ID}` | Unique session identifier |
| `` !`command` `` | Inline command execution (stdout captured) |

**Guidance:** Use `$ARGUMENTS` in dispatch tables. Use `$N` for positional semantics. Use `${CLAUDE_SESSION_ID}` for unique filenames. Use inline commands sparingly -- they run on every invocation. Prefer Bash-invoked scripts for anything non-trivial.

---

## 14. Stop Hooks

Session-end verification gates that run automatically when the agent is about to stop, ensuring deterministic quality checks pass before work is declared complete.

**When to use:** Long-running implementation sessions where you want to guarantee validation and tests pass before the agent finishes. Prevents the agent from stopping with broken code.

**Snippet -- Stop hook in `.claude/settings.json`:**

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "INPUT=$(cat); if [ \"$(echo \"$INPUT\" | jq -r '.stop_hook_active')\" = \"true\" ]; then exit 0; fi; wagents validate 2>/dev/null && uv run pytest -x --tb=short 2>/dev/null || { echo 'Verification failed' >&2; exit 2; }"
          }
        ]
      }
    ]
  }
}
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Allow stop -- agent terminates normally |
| 2 | Block stop with feedback -- stderr is shown to the agent, which continues working to fix the issue |

**Key requirement:** The `stop_hook_active` guard is **mandatory**. When a Stop hook exits non-zero, the agent resumes and will eventually try to stop again, re-triggering the hook. Without the guard, a persistently failing check creates an infinite loop. The platform sets `stop_hook_active: true` on re-invocations so the guard can break the cycle.

**Guidance:** Use Stop hooks for deterministic gates only (linting, tests, validation). Read stdin as JSON to access `stop_hook_active` and other context. Write failure reasons to stderr so the agent knows what to fix. Exit 2 (not 1) to provide feedback -- exit 1 blocks silently. Keep checks fast; the agent is waiting to finish.

**Alternatives for complex verification:**

- **Prompt-based Stop hook:** Instead of `"type": "command"`, use `"type": "prompt"` with a natural language instruction. The agent evaluates the prompt and decides whether to stop. Good for subjective quality checks ("Is the code well-documented?").
- **Agent-based Stop hook:** Use `"type": "command"` to invoke a separate agent process that performs multi-step verification. Good for checks requiring tool use (e.g., running the app and testing endpoints).

---

## Pattern Applicability Guide

| Skill Type | Must Have | Should Have | Optional |
|------------|-----------|-------------|----------|
| Simple (single mode) | Critical Rules, Scope Boundaries, Progressive Disclosure, Body Substitutions | Dispatch Table, Reference File Index | Canonical Vocabulary, Scripts, Templates, Stop Hooks |
| Multi-mode | Dispatch Table, Reference File Index, Critical Rules, Scope Boundaries, Progressive Disclosure, Body Substitutions | Canonical Vocabulary, Classification/Gating, Scaling Strategy | State Management, Scripts, Templates, Hooks, Stop Hooks |
| Interactive/stateful | Dispatch Table, Reference File Index, Critical Rules, Scope Boundaries, State Management, Progressive Disclosure, Body Substitutions | Canonical Vocabulary, Classification/Gating, Scaling Strategy, Templates | Scripts, Hooks, Stop Hooks |
| Automation | Dispatch Table, Critical Rules, Scope Boundaries, Scripts, Progressive Disclosure, Body Substitutions | Reference File Index, Hooks, Stop Hooks | Canonical Vocabulary, Classification/Gating, Scaling Strategy, Templates |

- **Must Have** -- omitting these is a defect in the skill design.
- **Should Have** -- include unless there is a clear reason not to.
- **Optional** -- include when the skill's domain calls for it.
