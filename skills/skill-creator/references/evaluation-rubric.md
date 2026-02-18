# Evaluation Rubric

Audit scoring system for skill quality. Defines what `audit.py` measures deterministically, what AI review adds subjectively, and how to pressure-test a skill before shipping.

## Contents

1. [Overview](#1-overview)
2. [Scoring Dimensions](#2-scoring-dimensions)
3. [Grade Thresholds](#3-grade-thresholds)
4. [Pressure Testing Protocol](#4-pressure-testing-protocol)
5. [Rationalization Audit](#5-rationalization-audit)
6. [AI Review Checklist](#6-ai-review-checklist)

---

## 1. Overview

Skill quality is assessed through two complementary checks run in sequence:

1. **`wagents validate`** -- structural correctness (pass/fail). Checks that `name` matches the directory, `description` is non-empty, and the body is non-empty. A skill that fails validation is broken and cannot be audited. Always run this first.

2. **`audit.py`** -- quality scoring (graded A--F). Measures how well the skill follows proven patterns and best practices across 10 weighted dimensions. Produces a deterministic numeric score and a letter grade. Run against a single skill (`audit.py skills/<name>`) or all skills (`audit.py --all`).

Always run both. A skill that passes validation but scores D or F needs significant rework. A skill that scores B but fails validation has a naming or metadata bug that must be fixed before distribution.

### Weighted Normalization + Bonus

Raw scores are not summed directly. Each dimension's raw score is multiplied by its weight, producing a weighted total. The weighted total is then normalized to a 0--100 scale: `(total_weighted / max_weighted) * 100`. Up to +3 bonus points from the Canonical Vocabulary dimension are added after normalization, so the theoretical maximum is 103. This means a skill can exceed 100 if it earns bonus points, even if its weighted raw scores are not perfect.

---

## 2. Scoring Dimensions

| # | Dimension | Weight | Max | What `audit.py` Checks | What AI Reviews |
|---|-----------|--------|-----|------------------------|-----------------|
| 1 | Frontmatter Completeness | 1x | 9 | Required fields present, cross-platform fields, name/dir match, agentskills.io name rules (no `--`, no leading/trailing hyphens, no reserved words), no XML tags in description | -- |
| 2 | Description Quality | 2x | 20 | Length (50--200 chars optimal), action verbs, "Use when" trigger words, "NOT for" exclusion, third-person voice | CSO optimization, keyword coverage, specificity vs vagueness |
| 3 | Dispatch Table | 1x | 10 | `$ARGUMENTS` table present, empty-args handler row, >=3 rows | Route clarity, coverage of common inputs, auto-detect logic |
| 4 | Body Structure | 1.5x | 15 | Line count <=500 (below frontmatter), heading hierarchy valid, >=3 `##` sections | Imperative voice, logical flow, information density |
| 5 | Pattern Coverage | 1.5x | 15 | Pattern markers detected (13 patterns, 2 pts each, capped at 15) | Fitness for skill type -- are the RIGHT patterns present? |
| 6 | Reference Quality | 1x | 10 | Index table present, no orphan files, no missing files, file sizes 50--500 lines | Content relevance, depth, self-containedness |
| 7 | Critical Rules | 1x | 10 | Section present with heading, >=5 numbered items | Testability (each rule can be verified), completeness, no overlap |
| 8 | Script Quality | 0.5x | 5 | If `scripts/` exists: argparse present, JSON output pattern, dependency check | Error handling, edge cases, documentation |
| 9 | Conciseness | 0.5x | 5 | No duplicate headings, no repeated content blocks | Token efficiency, information density, dead text |
| 10 | Canonical Vocabulary | -- | +3 bonus | Terms/vocabulary section present | Consistency of term usage throughout |

**Total: 99 raw points + 3 bonus. Final score is normalized:
`(total_weighted / max_weighted * 100) + bonus`, producing a 0-103 scale.**

### Dimension Details

**1. Frontmatter Completeness (9 pts, 1x weight)**

- **Full marks (9):** `name` present, valid kebab-case, <=64 chars, matches directory. `description` present and non-empty. `license`, `metadata.author`, and `metadata.version` all populated. No XML tags in description.
- **Common deductions:** Missing `license` (-1), missing `metadata.author` (-1), missing `metadata.version` (-1), name/directory mismatch (-1), consecutive hyphens in name (-1).
- **Zero:** Missing `name` field entirely, or name and description both absent.

**2. Description Quality (20 pts, 2x weight)**

- **Full marks (20):** 50--200 chars, starts with action verb, includes "Use when" trigger, includes "NOT for" exclusion, third-person voice, keyword-rich for agent discovery.
- **Common deductions:** Missing "NOT for" clause (-3), too short <50 chars (-3 to -5), too long >300 chars (-2 to -4), starts with "I" or "You" (-4), no action verbs (-4).
- **Zero:** Empty description, "TODO" placeholder, or description under 10 chars with no meaningful content.

**3. Dispatch Table (10 pts, 1x weight)**

- **Full marks (10):** `$ARGUMENTS` routing table present with >=3 data rows and an explicit empty-args handler row.
- **Common deductions:** Missing empty-args handler (-3), fewer than 3 rows (-2), table present but missing `$ARGUMENTS` keyword (-4).
- **Zero:** No dispatch table found anywhere in the body.

**4. Body Structure (15 pts, 1.5x weight)**

- **Full marks (15):** Body <=500 lines, valid heading hierarchy (no `####` before `##`), >=3 `##` sections, and >=2 `###` sub-sections providing good depth.
- **Common deductions:** Body exceeds 500 lines (-3), fewer than 3 `##` sections (-3 to -5), invalid heading hierarchy (-3), no sub-sections (-3).
- **Zero:** No headings found in body, or body is empty.

**5. Pattern Coverage (15 pts, 1.5x weight)**

- **Full marks (15):** 8+ of the 13 patterns detected (2 pts each, capped at 15). Patterns: dispatch-table, reference-file-index, critical-rules, canonical-vocabulary, scope-boundaries, classification-gating, scaling-strategy, state-management, scripts, templates, hooks, progressive-disclosure, body-substitutions.
- **Common deductions:** Each missing pattern costs 2 pts (until floor of 0). Skills with only 3--4 patterns score 6--8 raw.
- **Zero:** Fewer than 1 pattern detected. Indicates a stub or skeleton skill.

**6. Reference Quality (10 pts, 1x weight)**

- **Full marks (10):** Reference index table in body, no orphan files (on disk but not mentioned), no missing files (mentioned but not on disk), all reference files between 50--500 lines.
- **Common deductions:** Orphan reference files (-2), missing reference files (-2), no index table (-3), files outside 50--500 line range (-1 each).
- **Zero:** No `references/` directory exists.

**7. Critical Rules (10 pts, 1x weight)**

- **Full marks (10):** "Critical Rules" heading present, >=5 numbered items, and >=3 items contain actionable imperative verbs (never, always, must, ensure, require, check).
- **Common deductions:** Fewer than 5 rules (-2 to -4), rules lack imperative verbs (-2 to -3), heading present but no numbered items (-7).
- **Zero:** No "Critical Rules" section found in the body.

**8. Script Quality (5 pts, 0.5x weight)**

- **Full marks (5):** `scripts/` directory exists with Python files, scripts use `argparse`, produce JSON output (`json.dump`/`json.dumps`), have module docstrings, and multiple scripts present.
- **Common deductions:** No argparse (-1), no JSON output (-1), no docstrings (-1), single script only (-1).
- **Zero:** No `scripts/` directory, or directory exists but contains no `.py` files.

**9. Conciseness (5 pts, 0.5x weight)**

- **Full marks (5):** No duplicate headings, no repeated consecutive content blocks (3+ identical non-empty lines).
- **Common deductions:** Duplicate heading text (-2), repeated paragraph blocks (-3).
- **Zero:** Both duplicate headings and repeated content blocks detected.

**10. Canonical Vocabulary (+5 bonus)**

- **Full bonus (+5):** A dedicated "Canonical Terms," "Canonical Vocabulary," or "Vocabulary" section exists (heading or bold block).
- **No bonus (0):** No vocabulary section found. This is not penalized -- it is purely additive.

---

## 3. Grade Thresholds

| Grade | Score Range | Meaning |
|-------|------------|---------|
| A | 90--100+ | Production-ready. Follows all patterns appropriate for its type. Ready for distribution via `npx skills add`. |
| B | 75--89 | Good quality. Minor gaps in optional patterns. Ready for use, could improve with polish. |
| C | 60--74 | Functional but missing important patterns. Needs improvement before distribution. |
| D | 40--59 | Incomplete. Missing critical patterns or has structural issues. Needs significant work. |
| F | <40 | Broken or stub. Needs rewrite. Likely fails `wagents validate` as well. |

A skill should target B or above before merging. A grade is expected for skills intended for public distribution.

> **Bonus interaction:** The +3 bonus from Canonical Vocabulary is added after normalization, so scores above 100 are possible. A skill with a weighted normalized score of 88 and full bonus would reach 91, placing it in the A tier even though its raw weighted score alone falls in the B range.

---

## 4. Pressure Testing Protocol

> **Scope note:** Pressure testing is qualitative only and does not affect the `audit.py` score. It is a manual review complement to the deterministic scoring, intended to surface weaknesses that static analysis cannot detect.

Three types of pressure testing that AI review adds on top of deterministic scoring. Run these manually after `audit.py` produces its score.

### Ambiguity Pressure

Present the skill with edge-case inputs that sit between modes:

- **Cross-mode input:** Input that could trigger Create or Improve (or two adjacent modes). Does the dispatch table have an auto-detection heuristic? Does it ask for clarification?
- **Borderline scope:** Input that is borderline in-scope vs out-of-scope. Does the "NOT for" clause catch it? Does the skill refuse or proceed with a warning?
- **Empty or near-empty input:** A single word, a question mark, or no arguments at all. Does the empty-args handler activate cleanly?
- **Pass criteria:** The dispatch table handles all three cases without silent failure. At least one case produces an explicit clarification prompt.

### Scale Pressure

Test how the skill handles different input sizes:

- **Trivial input:** 1 file, 1 mode, no ambiguity. The skill should complete quickly without unnecessary ceremony.
- **Medium input:** 5 files, mixed modes, some ambiguity. The skill should scale its output proportionally without collapsing into a single-mode treatment.
- **Large input:** 20+ files, complex interactions, multiple modes active. The skill should have a scaling strategy (Pattern 7) that delegates to subagents or batches work.
- **Pass criteria:** The skill has an explicit scaling strategy. Large inputs do not cause the skill to silently truncate, skip files, or exceed context limits. Graceful degradation is documented.

### Adversarial Pressure

Test how the skill handles attempts to misuse it:

- **Scope violation:** Ask the skill to do something explicitly listed in its "NOT for" clause. The skill should refuse with a specific redirect ("Use X instead").
- **Malformed input:** Provide invalid paths, non-existent files, garbled arguments. The skill should produce a clear error, not hallucinate output.
- **Format mismatch:** Request output in a format the skill does not support. The skill should state its supported formats and default to one.
- **Pass criteria:** The skill refuses gracefully in all three cases. Refusals include a redirect or suggestion, not just "I can't do that."

### Combined Pressure

Layer multiple pressures simultaneously:

- **Ambiguous input at scale:** 10 files with borderline scope, no explicit mode specified. Does the skill classify each file individually or bail out entirely?
- **Adversarial input that looks like a valid edge case:** A request that superficially matches a valid mode but actually asks for something out of scope. Does the skill catch the subtlety?
- **Pass criteria:** The skill handles at least one combined scenario without breaking. Most skills will reveal a weakness here -- document it as a known limitation rather than ignoring it.

---

## 5. Rationalization Audit

For each critical rule, ask: "How would a smart model rationalize NOT following this rule?"

| # | Rule | Likely Dodge | Counter |
|---|------|-------------|---------|
| 1 | [rule text] | "This case is simple enough to skip" | [explicit counter] |
| 2 | [rule text] | "I already checked this mentally" | [explicit counter] |
| 3 | [rule text] | "The user didn't ask for this" | [explicit counter] |
| 4 | [rule text] | "It would make the output too verbose" | [explicit counter] |
| 5 | [rule text] | "The previous step already covers this" | [explicit counter] |

**How to fill this table:**

1. Copy each critical rule from the skill's "Critical Rules" section into the "Rule" column.
2. For each rule, imagine the most plausible reason a model would skip it. Write that in "Likely Dodge."
3. Write a specific, actionable counter -- not "just do it" but a concrete check or forcing function. Good counters reference observable artifacts: "The output must contain a section header named X" or "The JSON output must include field Y."
4. Fill this table for every skill with 5+ critical rules.
5. Reference the rationalization table from the superpowers `using-superpowers` skill as the gold standard for counter specificity.

**Counter quality criteria:**

- **Good:** "The output file must contain a `## Trade-offs` section with at least 2 bullet points per option."
- **Bad:** "Make sure to include trade-offs."
- **Good:** "Run `audit.py` and verify the Critical Rules dimension scores >= 7/10."
- **Bad:** "Check the rules are good."

---

## 6. AI Review Checklist

What the AI reviewer checks beyond what `audit.py` can measure. Run this checklist after deterministic scoring is complete.

1. **Voice consistency** -- Is the entire body in imperative voice? Flag any sentence that uses passive voice or second person ("you should") instead of direct commands ("Run the script").
2. **Information flow** -- Does information appear where you would expect it? Dispatch table at top, workflows in the middle, rules near the end, reference index last.
3. **Cross-reference integrity** -- Do references match what the body claims? If the body says "see `references/foo.md` for details on X," does that file actually cover X?
4. **Rule testability** -- Can every critical rule be verified by an observer reading the output? Rules like "write clean code" fail this test. Rules like "label all outputs as exploratory" pass.
5. **Pattern fitness** -- Are the patterns present the RIGHT ones for this skill type? A multi-mode skill without a dispatch table is wrong. A single-mode skill with classification-gating is unnecessary overhead.
6. **Description CSO** -- Would this description trigger on the right user inputs? Test by imagining 3 realistic user requests and checking whether the description's keywords would match.
7. **Conciseness** -- Could any section be 30% shorter without losing information? Flag sections that repeat the same idea in different words.
8. **Completeness** -- Are there obvious gaps the user would notice? Missing error handling, undocumented modes, unaddressed edge cases.
9. **Self-exemplar** -- Does the skill follow its own advice? A code-review skill that violates its own review criteria is disqualifying.
10. **Edge case coverage** -- What happens with unusual inputs? Unicode, very long strings, paths with spaces, empty repositories, monorepos with 100+ packages.
