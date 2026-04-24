---
name: simplify
description: >-
  Simplify working code without changing behavior. Analyze, apply, or explain
  clarity fixes. Use when recent code feels complex. NOT for review
  (honest-review) or debt scans (tech-debt-analyzer).
argument-hint: "[mode] [target]"
model: opus
license: MIT
compatibility: "Pre/Post hooks inspect edited files when metadata exists and no-op outside git repos. Stop hook intentionally runs repo-wide git diff --check hygiene inside git repos."
metadata:
  author: wyattowalsh
  version: "1.1.0"
hooks:
  PreToolUse:
    - matcher: "Write|Edit|MultiEdit"
      hooks:
        - command: 'bash -c ''if [ -z "$TOOL_INPUT_file_path" ] || ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then exit 0; fi; if git diff --quiet HEAD -- "$TOOL_INPUT_file_path" 2>/dev/null; then exit 0; else echo "WARNING: $(basename "$TOOL_INPUT_file_path") has uncommitted changes" >&2; exit 0; fi'''
  PostToolUse:
    - matcher: "Write|Edit|MultiEdit"
      hooks:
        - command: 'bash -c ''if [ -z "$TOOL_INPUT_file_path" ] || ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then exit 0; fi; git diff --stat -- "$TOOL_INPUT_file_path" 2>/dev/null || true'''
  Stop:
    - hooks:
        - type: command
          command: 'bash -c ''input=$(cat); if printf "%s" "$input" | grep -q "\"stop_hook_active\"[[:space:]]*:[[:space:]]*true"; then exit 0; fi; if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then exit 0; fi; git diff --check --cached && git diff --check'''
---

# Simplify

Simplify recently modified code for clarity, consistency, and maintainability while preserving exact behavior.

NOT for bug hunting (`honest-review`), debt inventory (`tech-debt-analyzer`), or performance-only investigation (`performance-profiler`).

## Canonical Vocabulary

Use these terms exactly throughout all modes:

| Term | Meaning |
|------|---------|
| **recent scope** | The code changed in the current task, current diff, or explicit user target; default operating scope |
| **simplification pass** | A behavior-preserving cleanup focused on clarity, structure, or redundant machinery |
| **behavior preservation** | Keeping the same externally observable behavior, contracts, outputs, side effects, and error boundaries |
| **semantic change** | Any change that alters behavior, API shape, validation rules, ordering guarantees, error semantics, or security posture |
| **mechanical cleanup** | Low-risk edits like removing obvious redundancy, flattening nesting, renaming for clarity, or deleting dead comments |
| **redirection** | Explicitly refusing out-of-scope work and naming the correct skill to use instead |

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| `analyze <path, symbol, or snippet>` | -> Mode A: Analyze simplification opportunities (read-only) |
| `apply <path, symbol, or snippet>` | -> Mode B: Apply a simplification pass |
| `explain <path, symbol, or snippet>` | -> Mode C: Explain why something feels complex and how to simplify it |
| `Simplify this code` / `Make this clearer` / `Refine this implementation` | -> Auto-detect: Mode B only when the Apply Eligibility Gate passes; otherwise Mode A or ask |
| Natural-language request asking what should be simplified | -> Auto-detect: Mode A |
| Empty | Show mode menu with examples |

### Auto-Detection Heuristic

If no explicit mode keyword is provided:

1. Simplification verbs plus a single-file, single-symbol, pasted-snippet, or clearly bounded recent diff that passes the Apply Eligibility Gate -> **Mode B: Apply**
2. Simplification verbs without a concrete target -> **Mode A: Analyze**
3. Simplification verbs plus a multi-file, wide recent scope, or risky active diff -> **Mode A: Analyze** first, or ask before editing
4. Requests centered on explanation, trade-offs, or coaching -> **Mode C: Explain**
5. If the request mixes a pasted snippet with a file-backed target, ask whether the snippet is illustrative or the actual edit scope before editing
6. If the target path is missing/invalid, the proof boundary is weaker than invariant reasoning, or the work would cross risky boundaries -> ask before editing

### Apply Eligibility Gate

Apply only when all checks pass:

| Check | Passes When | Otherwise |
|-------|-------------|-----------|
| **Target** | One concrete file, symbol, snippet, or tightly bounded recent diff is identified | Analyze first or ask for the target |
| **Intent** | The request is only a **simplification pass** | Redirect or ask if it includes bugs, features, API changes, validation changes, security, or perf tuning |
| **Behavior invariants** | The unchanged outputs, contracts, ordering, side effects, and error boundaries can be stated before editing | Analyze first and list unknowns |
| **Validation basis** | Existing tests/checks, type contracts, or invariant reasoning cover the narrow target | Ask before editing if weaker than invariant reasoning |
| **Scope risk** | No mixed snippet/file target, missing path, public API shift, policy boundary, or cross-module rewrite is required | Ask before editing |

## Snippet Contract

- `analyze` on a snippet: stay read-only, classify simplification opportunities inside the pasted code only, and state any assumptions explicitly.
- `explain` on a snippet: explain what feels complex and what a safer simpler shape would look like without implying repo-backed edits.
- `apply` on a snippet: treat the snippet as the whole scope, simplify only within the pasted text, and verify by invariant reasoning or explicit limitation when project checks are unavailable.
- Mixed snippet plus file/diff context: do not auto-apply until the user clarifies whether the snippet is the edit target or an example of a broader issue.

### Example Invocations

```bash
/simplify analyze src/auth/session.py
/simplify apply src/routes/session.ts
/simplify explain internal/auth/session.go
/simplify
```

### Empty Arguments

When `$ARGUMENTS` is empty, present the mode menu:

| Mode | Command | Purpose |
|------|---------|---------|
| Analyze | `analyze <target>` | Find the highest-confidence simplification opportunities without editing |
| Apply | `apply <target>` | Make a behavior-preserving simplification pass |
| Explain | `explain <target>` | Explain why the code feels complex and what a safer simpler shape looks like |

> Paste code, point at a file or symbol, or pick a mode above.

## Core Principles

**Preserve functionality first** — The simplify contract is narrow: never change what the code does; change only how clearly it expresses the same behavior.

**Prefer clarity over cleverness** — Explicit control flow, obvious names, and readable structure beat compact tricks. Avoid nested ternaries, dense one-liners, and abstraction layers that hide trivial work.

**Stay inside recent scope by default** — Start with the current task's changes, current diff, or explicit target. Only widen scope when the user asks or the simplification is impossible without a clearly related nearby edit.

**Honor project standards** — Simplify into the codebase's existing conventions, helpers, and error-handling patterns. Do not impose a generic style if the project already has a better one.

## Progressive Disclosure

Load only the layer needed for the mode:

| Mode | Load |
|------|------|
| Analyze | `references/simplification-taxonomy.md` and `references/output-formats.md` |
| Apply | `references/simplification-taxonomy.md`, `references/behavior-preservation.md`, and `references/output-formats.md` |
| Explain | `references/simplification-taxonomy.md` and `references/output-formats.md` |

## Mode A: Analyze

Read-only simplification report.

1. Determine the **recent scope** from `$ARGUMENTS`, current context, or active diff.
2. Read the target and load `references/simplification-taxonomy.md`.
3. Classify opportunities by category, confidence, and blast radius.
4. Filter out anything that would require a **semantic change**.
5. Present only the highest-value opportunities using the Analyze template in `references/output-formats.md`.
6. Recommend Mode B only when the opportunities are behavior-safe and well-scoped.

## Mode B: Apply

Make a behavior-preserving simplification pass.

1. Determine the narrowest target. Default to the **recent scope**.
   If the target is a pasted snippet, treat the snippet itself as the whole scope and verify by invariant reasoning when no project checks exist.
2. Load:
   - `references/simplification-taxonomy.md`
   - `references/behavior-preservation.md`
   - `references/output-formats.md`
3. Confirm the Apply Eligibility Gate passes and write the invariant ledger from `references/behavior-preservation.md` before editing.
4. Build a short plan of high-confidence, low-blast-radius edits.
5. Prefer transformations like:
   - flattening nested conditionals into guard clauses
   - removing dead comments, dead code, and dead wrappers
   - inlining single-use abstractions or pass-through plumbing
   - extracting duplicate logic across branches into one clear path
   - replacing hand-rolled mechanics with existing helpers or stdlib equivalents
   - renaming for clarity when names are part of the complexity
6. Do **not** mix simplification with bug fixes, feature work, API redesign, validation changes, security changes, or performance-only rewrites.
7. Apply the smallest coherent set of edits that materially improves clarity.
8. If the verification basis is weak, the diff is risky, or the target boundary is still fuzzy, stop and use the Apply deferred template instead of editing further.
9. Run the narrowest relevant existing validation available. If no automation exists, state the verification basis explicitly.
10. Present the result with the Apply template from `references/output-formats.md`.

## Mode C: Explain

Coaching and rationale, no edits.

1. Determine the target from `$ARGUMENTS` or pasted code.
2. Explain what makes the code feel complex using terms from `references/simplification-taxonomy.md`.
3. Separate safe simplifications from risky or semantic ones.
4. Show a likely simpler shape without requiring edits.
5. Present the result with the Explain template in `references/output-formats.md`.

## Scaling Strategy

| Scope | Strategy |
|-------|----------|
| 1 file or 1 symbol | Work inline in a single simplification pass |
| 2-5 files | Split by file ownership; simplify in parallel only when files do not overlap |
| 6+ files or multi-layer refactor | Use `/orchestrator` for a wave-based plan before editing |

## Scope Boundaries

Use `simplify` for working code that needs to become clearer without changing behavior.

Do **not** use `simplify` for:

- correctness, security, or defect hunting (`honest-review`, `security-scanner`)
- debt inventories, prioritization, or roadmap work (`tech-debt-analyzer`)
- profiling, benchmarking, caching strategy, or perf-only optimization (`performance-profiler`)
- new features, behavior changes, migrations, or architecture rewrites

When a request is outside scope, redirect explicitly instead of stretching the skill.

## Reference File Index

Do not load all references at once. Read only what the current mode needs.

| File | Content | Read When |
|------|---------|-----------|
| `references/simplification-taxonomy.md` | Categories of simplification opportunities, preferred transformations, and anti-patterns to avoid | Analyze, Apply, Explain |
| `references/behavior-preservation.md` | Verification hierarchy, stop conditions, approval boundaries, and behavior-safety checklist | Apply, risky Analyze findings |
| `references/output-formats.md` | Output templates for analyze/apply/explain, empty-args menu, and redirection responses | All modes |

## Critical Rules

1. Never change behavior intentionally. If simplification requires a bug fix, feature addition, or contract change, stop and ask.
2. Default to the **recent scope** unless the user explicitly widens it.
3. Never apply until the Apply Eligibility Gate passes; use Analyze or ask when the gate fails.
4. Prefer explicit readable code over compact clever code; avoid nested ternaries when clearer branching exists.
5. Remove abstractions only when they are redundant, single-use, or purely pass-through; keep abstractions that protect real policy, validation, ownership, or API boundaries.
6. Do not bundle unrelated cleanups, migrations, or style sweeps into a simplification pass.
7. Preserve project naming, typing, error-handling, and module conventions while simplifying.
8. Reuse existing helpers and standard library facilities before inventing new abstractions.
9. When existing validation exists, run the narrowest relevant checks after edits. If you cannot run checks, state that plainly and explain the remaining risk.
10. Redirect out-of-scope requests to the correct skill by name instead of doing approximate work.
11. Summaries stay concise: what changed, why it is simpler, and what stayed the same.
