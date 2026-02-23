# Audit Guide

Procedures for auditing individual skills, comparative rankings, dashboards, and the gallery view.

## Contents

1. [Audit (Single Skill)](#audit-single-skill)
2. [Grade Thresholds](#grade-thresholds)
3. [Audit All](#audit-all)
4. [Dashboard](#dashboard)
5. [Gallery](#gallery)

---

## Audit (Single Skill)

Score a single skill using deterministic analysis + AI review.

### Steps

1. **Run audit script:**
   ```bash
   uv run python skills/skill-creator/scripts/audit.py skills/<name>/
   ```
   Produces a JSON report with 10 scored dimensions, detected patterns, and suggested patterns.

2. **AI review** — supplement the script's findings with judgment-based assessment:
   - Description quality: Is the CSO optimization effective? Does it enable discovery?
   - Route clarity: Can an agent unambiguously route to the right mode?
   - Imperative voice: Does the body use imperative voice consistently?
   - Pattern fitness: Are detected patterns appropriate? Are suggested patterns genuinely needed?
   - Content relevance: Do references contain actionable, domain-specific guidance?
   - Token efficiency: Is every line earning its keep?

3. **Pressure testing** — load `references/evaluation-rubric.md` Pressure Testing Protocol. Apply:
   - **Ambiguity pressure:** Find 3 inputs that could misroute. Do the dispatch rules handle them?
   - **Scale pressure:** What happens with 0, 1, 10, 100 items? Does the skill degrade gracefully?
   - **Adversarial pressure:** What if the user provides contradictory instructions? Malformed input?

4. **Report** — present the graded report:
   - Letter grade (A-F) with numeric score
   - Dimension breakdown (10 dimensions with scores and findings)
   - Pattern checklist (13 patterns: present/absent/suggested)
   - Top 3 improvement opportunities (highest impact)
   - Pressure test results

---

## Grade Thresholds

See `references/evaluation-rubric.md` § 3 for the full grading scale with interpretation guidance.

**Quick reference:** A (90+), B (75-89), C (60-74), D (40-59), F (<40).

---

## Audit All

Score every skill in the repository and produce a comparative ranking.

### Steps

1. **Run audit script:**
   ```bash
   uv run python skills/skill-creator/scripts/audit.py --all --format table
   ```

2. **Present comparative table** — sorted by score descending:

   | Skill | Score | Grade | Lines | Refs | Scripts | Patterns |
   |-------|-------|-------|-------|------|---------|----------|

3. **Summary statistics** — mean score, median, range. Identify the strongest and weakest skill.

4. **Improvement roadmap** — for skills scoring below B, list the single highest-impact improvement for each.

> **Note:** Audit All mode runs deterministic scoring only (via `audit.py`). It does not include the qualitative AI review component that single-skill Audit mode provides.

---

## Dashboard

Render a visual creation process monitor or audit quality dashboard.

### Process Monitor (active session)

When a creation session is active (`~/.claude/skill-progress/<name>.json` exists):

1. **Quick open (recommended):**
   ```bash
   uv run python skills/skill-creator/scripts/progress.py serve --skill <name>
   ```
   This reads current session state, injects it into the dashboard template, writes a
   temporary HTML file, and opens it in the default browser. Use `--no-open` to suppress
   the browser launch and just print the file URL. Use `--state-dir <path>` to read from
   a custom state directory.

2. **Manual setup** (alternative):
   1. Read progress: `uv run python skills/skill-creator/scripts/progress.py read --skill <name>`
   2. Copy template: `cp skills/skill-creator/templates/dashboard.html /tmp/skill-dashboard.html`
   3. Inject progress JSON into `<script id="data">` block. Dashboard auto-detects process mode from `phases` field.
   4. For live polling, set `data-poll-url` attribute on the script tag.
   5. Render via Playwright screenshot or browser open.

### Audit Dashboard (no active session)

When no creation session exists, fall back to the audit quality overview:

1. Run: `uv run python skills/skill-creator/scripts/audit.py --all`
2. Copy template, inject audit JSON with `"skills": [...]` array.
3. Dashboard auto-detects audit overview mode.
4. Render via Playwright screenshot or browser open.

---

### Gallery

When arguments are empty, present the skill inventory with scores and available actions.

See SKILL.md § Gallery for the full procedure (runs `audit.py --all --format table`, displays results, offers mode menu).
