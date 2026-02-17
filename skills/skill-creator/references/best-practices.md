# Skill-Writing Best Practices

Condensed from Anthropic's official skill-writing guidance and superpowers methodology.

## Contents

1. [Conciseness Hierarchy](#1-conciseness-hierarchy)
2. [Degrees of Freedom](#2-degrees-of-freedom)
3. [Description Engineering / CSO](#3-description-engineering--cso)
4. [Progressive Disclosure](#4-progressive-disclosure)
5. [Evaluation-Driven Development](#5-evaluation-driven-development)
6. [Rationalization Tables](#6-rationalization-tables)
7. [Cross-Model Considerations](#7-cross-model-considerations)
8. [Context Budget Awareness](#8-context-budget-awareness)
9. [Common Anti-Patterns](#9-common-anti-patterns)
10. [Cross-Agent Awareness](#10-cross-agent-awareness)

---

## 1. Conciseness Hierarchy

The context window is shared between ALL active skills, conversation history, tool results, and retrieved documents. Every line must earn its keep.

**Rules:**

1. Claude is smart -- don't explain concepts it already knows from training
2. Skill descriptions consume ~100 tokens each; all are loaded simultaneously (~2% of context)
3. Activated skill body: stay under 5,000 tokens. Hard limit: 500 lines below frontmatter
4. Reference files: 50-500 lines each. Split if longer
5. If you can say it in 5 words, don't use 15
6. Delete anything the agent already knows (e.g., "markdown uses # for headings")
7. Prefer tables over prose for structured information
8. Use imperative voice ("Check the output" not "You should check the output")

**Conciseness checklist before finalizing any skill file:**

| Check | Action |
|-------|--------|
| Line count >500? | Move detail to `references/` |
| Paragraph >3 sentences? | Convert to table or bullet list |
| Instruction states the obvious? | Delete it |
| Two sections say the same thing? | Merge into one |
| Adverbs and filler words? | Remove ("simply", "just", "basically", "very") |

---

## 2. Degrees of Freedom

Match instruction specificity to task fragility.

| Level | Fragility | Style | Example |
|-------|-----------|-------|---------|
| **Narrow bridge** | High | Exact steps, exact format, exact tools | "Run `uv run wagents validate` -- if exit code is non-zero, fix all errors before proceeding." |
| **Guided path** | Medium | Structure with room for judgment | "Generate 3-5 expert personas. Each must have distinct intellectual traditions and genuine points of disagreement." |
| **Open field** | Low | State the goal, let the agent choose | "Organize the reference material into logical sections." |

**When to use each:**

- **Narrow bridge:** API calls, file formats, validation steps, tool invocations, output schemas
- **Guided path:** Multi-step workflows where quality matters but approach is flexible
- **Open field:** Creative writing, code architecture, user interaction, exploratory analysis

**Common mistake:** Over-constraining creative tasks (forcing exact phrasing) or under-constraining mechanical tasks (leaving exact commands to the agent's judgment). Audit every instruction: "If the agent does this differently than I intended, does it matter?" If no, widen the constraint.

---

## 3. Description Engineering / CSO

The `description` field is the skill's search-engine listing. It determines whether the agent invokes the skill automatically and how it appears in slash-command search.

**CSO (Context-Search Optimization) principles:**

1. Write in third person ("Analyzes codebases..." not "I analyze codebases...")
2. Front-load the primary action verb
3. Include "Use when" trigger phrases -- keywords the agent matches against user intent
4. Include "NOT for" exclusion phrases -- prevents false positive invocations
5. Cover synonyms and phrasings the user might try
6. Aim for 150-300 chars (max 1024, but shorter is higher signal-to-noise)
7. Think of it as a search query match target: what would the user type?

**Template:**

```
<primary action verb> <what it does>. <Additional capabilities>.
<Modes or variations>.
Use when <trigger conditions>.
NOT for <exclusion conditions>.
```

**Good example:**

```
Analyze codebases for architectural patterns, anti-patterns, and
improvement opportunities. Modes: scan for quick overview, deep for
comprehensive analysis. Use when reviewing architecture, onboarding
to new codebases, or preparing for refactoring. NOT for runtime
profiling, debugging, or writing new code.
```

**Bad example:**

```
A tool for code analysis.
```

Why it's bad: no action verb, no trigger phrases, no exclusions, no modes. The agent cannot distinguish this from any other analysis skill.

---

## 4. Progressive Disclosure

Four layers of information, each loaded only when needed.

| Layer | File | Loaded When | Token Budget |
|-------|------|-------------|--------------|
| 1. Metadata | Frontmatter fields | All skills loaded simultaneously | ~100 tokens per skill |
| 2. Body | SKILL.md content below `---` | Skill is activated (slash command or auto) | <5,000 tokens |
| 3. References | `references/*.md` | On-demand per reference index | 500-3,000 tokens each |
| 4. Artifacts | `scripts/`, `templates/` | Invoked via Bash (never loaded into context) | 0 tokens (executed, not read) |

**Key principles:**

- Never put reference-level detail in the body (wastes tokens on every invocation)
- Never put body-level routing in references (forces unnecessary file loads)
- Each layer has a specific purpose: metadata for discovery, body for dispatch, references for knowledge, artifacts for execution
- Include a reference index table in the body so the agent knows what's available without reading every file

---

## 5. Evaluation-Driven Development

TDD for skills: write test cases before writing the skill body.

**RED-GREEN-REFACTOR cycle:**

1. **RED:** Define eval scenarios. Write 3+ JSON eval files in `evals/`:
   - Explicit invocation: `/skill-name create foo` with expected behavior
   - Implicit trigger: Natural language that should activate the skill
   - Negative control: Input that should NOT trigger the skill
2. **GREEN:** Write the minimal SKILL.md that satisfies all evals
3. **REFACTOR:** Optimize conciseness, add patterns, improve structure

**Eval format (Anthropic-recommended):**

```json
{
  "skills": ["skill-name"],
  "query": "Realistic user request that should trigger this skill",
  "expected_behavior": [
    "Agent activates skill-name",
    "Agent produces output matching X criteria",
    "Agent does NOT do Y"
  ]
}
```

No built-in runner exists -- evals serve as manual test cases and documentation of intent. Run them by pasting the query into a fresh session with the skill installed and checking behavior against expected outcomes.

The negative control eval is the most commonly skipped and the most valuable. It prevents the skill from becoming a catch-all.

---

## 6. Rationalization Tables

Predict how the model will dodge your rules, then write explicit counters.

**Method:** For each critical rule, ask: "How would a smart model rationalize NOT following this?" Then add the counter.

**Template:**

| Rule | Likely Rationalization | Counter |
|------|----------------------|---------|
| Always run validation before committing | "The changes are trivial" | No change is trivial. Validation catches format errors humans miss. |
| Never skip the audit step | "I already know the score is high" | Memory is unreliable. Run the script -- it takes 2 seconds. |
| Load reference files before acting | "I remember the content from last session" | Skills evolve between sessions. Always read the current version. |
| Use the dispatch table for routing | "The user's intent is obvious" | Obvious intent still needs consistent output format. Follow the table. |
| Stay within scope boundaries | "This is closely related" | Adjacent is not identical. Suggest the correct skill instead. |

This technique is borrowed from the superpowers methodology. Place rationalization tables in the "Critical Rules" section of SKILL.md or in a dedicated reference file for skills with many rules.

**When to use:** Any rule the model might bend. Especially: validation steps, format constraints, scope boundaries, and tool-use requirements.

---

## 7. Cross-Model Considerations

Different models need different levels of structure in skill instructions.

| Model | Characteristics | Skill Implications |
|-------|----------------|-------------------|
| Opus | Handles ambiguity well, follows complex multi-step workflows, strong judgment | Use open-field instructions, principles over rules, complex dispatch tables |
| Sonnet | Good at focused tasks, needs more explicit structure, may shortcut multi-step processes | Prefer numbered steps, explicit phase gates, less room for interpretation |
| Haiku | Fast but needs tight constraints, may miss nuance, best for mechanical tasks | Very explicit instructions, simple dispatch, minimal branching logic |

**Setting the `model` frontmatter field:**

- `model: opus` -- complex multi-mode skills, skills requiring judgment or creative output
- `model: sonnet` -- focused single-task skills, automation wrappers, formatting tasks
- Omit `model` -- inherits from session default (correct for most skills)

**Practical implication:** If your skill targets Sonnet, replace open-field instructions with guided-path or narrow-bridge equivalents. If targeting Opus, you can trust principles and let the model figure out the implementation.

---

## 8. Context Budget Awareness

Understanding the token economy across a full session.

| Component | Token Cost | Frequency |
|-----------|-----------|-----------|
| Each skill description (all loaded) | ~100 tokens | Always |
| 20 installed skill descriptions | ~2,000 tokens | Always |
| Activated skill body | 2,000-5,000 tokens | Per invocation |
| Each reference file load | 500-3,000 tokens | On demand |
| Conversation history | Grows over session | Cumulative |
| Tool results (file reads, searches) | Variable | Per tool call |

**Implications:**

- Keep descriptions information-dense (every word matters for routing accuracy)
- Body should be self-sufficient for common cases (avoid forcing reference loads for simple invocations)
- Include quick-reference examples inline to reduce reference file loads
- If a skill has 5+ reference files, the body's reference index becomes critical for selective loading
- Total context pressure grows as conversations lengthen -- front-loaded skills (clear dispatch in body) perform better late in sessions

---

## 9. Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Body >500 lines | Wastes context, buries key information | Move detail to `references/` files |
| Dead references | Files on disk but not in body index -- never loaded | Audit with `audit.py`, add to index or delete |
| Untestable rules | "Write good code" -- no way to verify | Make rules binary: "Run X -- if Y, then Z" |
| TODO descriptions | `description: TODO` -- agent can't route to the skill | Write real description before anything else |
| Nested reference dirs | `references/sub/deep/file.md` -- hard to discover | One level deep only: `references/*.md` |
| Time-sensitive info | "As of 2024..." -- ages immediately | Use reference files for stable patterns, not current facts |
| Monolithic SKILL.md | Everything in one file, no references | Split: body for routing + dispatch, references for domain knowledge |
| Copy-paste instructions | Same text duplicated across sections | Single source of truth, reference by section heading |
| Over-engineering | 500-line skill for a 3-step task | Start minimal, add complexity only when evals fail |
| Missing empty-args handler | User invokes `/skill` with no args -- confusion | Always define default behavior in dispatch table |
| Vague scope boundaries | No "NOT for" clause -- skill fires on tangential requests | Add explicit exclusions to description and body |
| No reference index | References exist but body doesn't list them | Add a table mapping filenames to purposes |

---

## 10. Cross-Agent Awareness

Skills in this repo are Claude Code-primary (dispatch tables, `$ARGUMENTS` routing, tool references). Distribution paths:

1. **Filesystem agents:** `npx skills add wyattowalsh/agents --skill <name> -y -g -a <agents>` for Claude Code, Cursor, Gemini CLI, Codex, and other compatible agents.
2. **Claude API:** `/v1/skills` endpoints for programmatic upload/versioning.
3. **Project-local:** Direct commit to `.claude/skills/` for single-project use.

Always populate cross-platform frontmatter fields (`license`, `metadata.author`, `metadata.version`) to enable multi-agent installability. Note which Claude Code-specific features are used (dispatch tables, body substitutions, hooks) so other agents can degrade gracefully.

---
