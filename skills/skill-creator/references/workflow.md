# Skill Development Workflow

Unified process for creating new skills and improving existing ones.
Steps 1-3 branch on new vs existing. Steps 4-6 are identical for both.

## Contents

1. [Step 1: Understand](#step-1-understand)
2. [Step 2: Plan](#step-2-plan)
3. [Step 3: Scaffold](#step-3-scaffold-new-skills-only)
4. [Step 4: Build](#step-4-build)
5. [Step 5: Validate](#step-5-validate)
6. [Step 6: Iterate](#step-6-iterate)

> **Quick Build fast-path:** For simple single-mode skills with no scripts/templates:
> Skip Steps 2-3, go straight to Step 4 with `wagents new skill <name>`, build the body,
> then validate (Step 5). The audit will flag any missing patterns.

---

> **Progress tracking (initialization):**
> `uv run python skills/skill-creator/scripts/progress.py init --skill <name>`

## Step 1: Understand

### New Skill

- Ask clarifying questions about use cases and triggers
- Avoid asking too many questions at once (2-3 per round)
- Define scope: IS for / NOT for (minimum one "NOT for" clause)
- Identify target audience and expected invocation patterns

### Existing Skill

- Run audit: `uv run python skills/skill-creator/scripts/audit.py skills/<name>/`
- Read the current SKILL.md and all reference files
- Understand the user's specific intent: full improvement or targeted change
- Note the baseline score and grade for comparison

> **Progress tracking:**
> Start: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase understand --status active`
> End: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase understand --status completed --notes "<summary>"`

---

## Step 2: Plan

### New Skill

1. **Validate name** — kebab-case, 2-64 chars, no consecutive hyphens, no leading/trailing hyphens, no reserved words ("anthropic", "claude"). Check `skills/` for conflicts.
2. **Write description** — CSO-optimized for discovery: third person, what the skill does + when to use it + when NOT to use it. Max 1024 chars. Include action verbs and trigger phrases ("Use when..."). Load `references/best-practices.md` Description Engineering section.
3. **Classify patterns** — Which of the 13 patterns from `references/proven-patterns.md` apply to this skill type? At minimum: dispatch table, critical rules.
4. **Plan directory structure** — SKILL.md, references/, scripts/, templates/, evals/. Decide which are needed.

### Existing Skill

1. **Extract findings** — from audit report: missing patterns, low-scoring dimensions, rule violations, structural issues
2. **Scope the work** — for targeted requests, focus plan on what the user asked. Note any P0 issues elsewhere but don't force them.
3. **Present improvement plan** — each item includes: what to change, why, expected score impact, which file(s) to modify
4. **Approval gate** — show projected before/after score. Wait for user approval. Do NOT implement until approved.

Each improvement item must include:
- **File(s):** Which files will be modified
- **Finding:** What the audit or analysis identified
- **Change:** What will be done
- **Rationale:** Why this change improves the skill
- **Score impact:** Expected point improvement
- **Risk:** What could go wrong (low/medium/high)

> **Progress tracking:**
> Start: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase plan --status active`
> End: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase plan --status completed --notes "<summary>"`

---

## Step 3: Scaffold (new skills only)

Skip this step for existing skills.

1. Run `uv run wagents new skill <name>` to scaffold `skills/<name>/SKILL.md`
   Update metrics: `uv run python skills/skill-creator/scripts/progress.py metric --skill <name> --key files_created --value 1`
2. Configure frontmatter — load `references/frontmatter-spec.md` for the full field catalog and decision tree. At minimum: `name`, `description`, `license: MIT`, `metadata.author`, `metadata.version`, `argument-hint`.
3. If `--from <source>` was specified, read the source skill as a structural template. Copy applicable structure, replace all domain-specific content.

> **Progress tracking:**
> Start: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase scaffold --status active`
> End: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase scaffold --status completed`
> For existing skills: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase scaffold --status skipped`

---

## Step 4: Build

Apply to both new and existing skills. Work through each applicable area.

**Parallel execution strategy:**

- **Wave 1 (sequential):** Complete 4a (Frontmatter) and 4b (Body) first — body establishes dispatch table and section structure that other areas depend on.
- **Wave 2 (parallel):** Dispatch 4c-4f as parallel subagents:
  - Subagent: References (4c)
  - Subagent: Scripts (4d)
  - Subagent: Templates (4e)
  - Subagent: Evals (4f)

Track wave/agent progress:
> `uv run python skills/skill-creator/scripts/progress.py agent --skill <name> --wave wave-1 --agent agent-body --status active`
> On completion: `uv run python skills/skill-creator/scripts/progress.py agent --skill <name> --wave wave-2 --agent agent-refs --status completed --summary "6 reference files"`

> **Progress tracking:**
> Start: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase build --status active`
> End: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase build --status completed`

### 4a. Frontmatter

- Required: name, description
- Cross-platform: license, metadata.author, metadata.version
- Extensions: argument-hint, model (load `references/frontmatter-spec.md` for decision tree)

### 4b. Body

Load `references/proven-patterns.md`. Apply:

- **Mandatory patterns** — every skill gets:
  - Dispatch table with `$ARGUMENTS` routing, example invocations, and empty-args handler
  - Critical rules section with 5+ numbered, testable rules
  - Reference file index (if references exist) with "Read When" column
- **Conditional patterns** — apply as classified in Step 2:
  - Classification/gating logic (if input varies in complexity)
  - Scaling strategy (if workload varies in size)
  - State management (if skill persists data across invocations)
  - Canonical vocabulary (if domain has specific terms)
  - Core principles (if why-level guidance is needed)
  - Scope boundaries (if misrouting risk is high)
- **Body substitutions** — use where applicable:
  - `$ARGUMENTS` — full argument string after the skill name
  - `$ARGUMENTS[N]` — Nth argument (0-indexed)
  - `$N` — shorthand for `$ARGUMENTS[N]`
  - `${CLAUDE_SESSION_ID}` — unique session identifier
  - `` !`command` `` — shell command output substitution
- **Line budget** — body must stay under 500 lines below frontmatter. Move detail to references if approaching.

### 4c. References

- Self-contained, 100-450 lines each, contents index at top
- No time-sensitive info, no orphans, no phantoms
- Every reference indexed in SKILL.md's Reference File Index
- One level deep from SKILL.md: `references/*.md`

### 4d. Scripts (if applicable)

- Python, argparse, JSON to stdout, warnings to stderr
- Follow `add-badges/scripts/detect.py` pattern: single-file, self-contained, clear output schema

### 4e. Templates (if applicable)

- Self-contained HTML with no external dependencies
- JSON-in-script data injection via `<script id="data" type="application/json">`
- CSS custom properties for theming, dark mode default with `prefers-color-scheme: light`
- Vanilla JS rendering. Follow `wargame/templates/dashboard.html` pattern.

### 4f. Evals

- **New skills:** generate 3+ JSON evals:
  - 1 explicit invocation eval (tests `/skill-name <args>` dispatch)
  - 1 implicit trigger eval (natural language that should activate the skill)
  - 1 negative control eval (input that should NOT trigger the skill)
- **Existing skills:** update/extend evals to cover any changed dispatch behavior or new modes
- Format: `{ "skills": [...], "query": "...", "files": [], "expected_behavior": [...] }`

---

## Step 5: Validate

1. Run `uv run wagents validate` — must pass with zero errors
2. Run `uv run python skills/skill-creator/scripts/audit.py skills/<name>/` — target A (90+)
3. Run `uv run wagents readme` — regenerate README
4. Delegate docs to docs-steward — auto-triggers on skill file changes. Do NOT call `wagents docs generate` directly.

### Portability Check

Run `wagents package <name> --dry-run` to verify the skill is distributable:
- All 7 portability checks must pass (see `references/packaging-guide.md`)
- Fix any warnings before declaring the skill complete

> **Progress tracking:**
> Start: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase validate --status active`
> Inject audit: `uv run python skills/skill-creator/scripts/progress.py audit --skill <name> --inject`
> End: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase validate --status completed`

### Completion Criteria

- `wagents validate` passes with zero errors
- `audit.py` scores the skill at A (90+)
- `wagents readme --check` exits 0 (README is current)

---

## Step 6: Iterate

1. Test the skill on realistic tasks — try common invocations and edge cases
2. Note where it struggles, misroutes, or produces poor output
3. Loop back to Step 4 with findings
4. Re-validate after each iteration (Step 5)
5. For existing skills: compare current score against baseline from Step 1

> **Progress tracking:**
> Start: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase iterate --status active`
> After each iteration: `uv run python skills/skill-creator/scripts/progress.py metric --skill <name> --key iteration_count --value +1`
> End: `uv run python skills/skill-creator/scripts/progress.py phase --skill <name> --phase iterate --status completed`

---

## Error Recovery

Common errors and their fixes during skill development.

### Corrupted State File

**Symptom:** `progress.py` commands fail with JSON decode errors.
**Fix:** Delete `~/.claude/skill-progress/<name>.json` and reinitialize with `progress.py init --skill <name>`.

### Broken Reference Links

**Symptom:** `audit.py` reports missing reference files.
**Fix:** Either create the missing file or remove the stale reference from the SKILL.md body and Reference File Index.

### Validation Failures After Refactoring

**Symptom:** `wagents validate` fails after renaming a skill.
**Fix:** Ensure the directory name matches the `name:` field in frontmatter. Both must be kebab-case and identical.

### Audit Score Drops After Adding Content

**Symptom:** Score decreases after adding new sections.
**Fix:** Check body length (must be under 500 lines). Move detail to reference files. Run `audit.py` to identify which dimension dropped.

### Template Rendering Fails

**Symptom:** Dashboard template shows blank or errors.
**Fix:** Verify `templates/dashboard.html` exists. Check that `progress.py serve --skill <name>` can read the state file. Try `progress.py read --skill <name>` first.
