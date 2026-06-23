# Skill Asset Review

Use this lens when reviewing first-party or curated skill assets. It applies the `skill-creator` paradigm to `/review` findings without turning `/review` into skill implementation.

## Triggers

Attach this lens when the scope includes any of:

- `skills/<name>/SKILL.md`
- `skills/<name>/references/**`
- `skills/<name>/scripts/**`
- `skills/<name>/evals/**`
- `docs/src/authoring/skills/<name>.mdx`
- `docs/src/skill-research/<name>.md`
- generated catalog or research pages for a skill
- packaging, install, sync, hook, or catalog behavior for skills

Do not widen a review to every skill just because one skill file is present. Stay with the requested scope unless a dependency is required to verify a finding.

## Evidence Ladder

Prefer deterministic evidence before judgment:

1. Read the target `SKILL.md` frontmatter and body.
2. Run or cite `uv run python skills/skill-creator/scripts/audit.py skills/<name> --format json` when the target is a repo skill.
3. Run or cite `uv run python skills/skill-creator/scripts/asset_toolkit/validate_evals.py skills/<name> --format json` when evals changed.
4. Run or cite `uv run python skills/skill-creator/scripts/package.py skills/<name> --dry-run` for portability-sensitive findings.
5. Run the skill's own `scripts/check.py` when present and trusted.
6. For public docs/catalog drift, check generated outputs against authoring/source; fix source, not generated pages.

If a command is unavailable or out of scope, state degraded mode and continue with line-based source evidence.

## Structural Gates

Check these skill-creator patterns before reporting "no findings":

| Gate | Review Question |
| --- | --- |
| dispatch-table | Does `$ARGUMENTS` route real user inputs, including empty args and ambiguous inputs? |
| reference-file-index | Does every indexed reference exist, and is every reference file discoverable from the index? |
| critical-rules | Are rules imperative, falsifiable, and specific enough to test? |
| canonical-vocabulary | Are domain terms stable, grouped, and used consistently? |
| scope-boundaries | Does frontmatter and body say what the skill is NOT for? |
| classification-gating | Does the skill choose modes through explicit evidence, not vague judgment? |
| scaling-strategy | Does large work have lane ownership, dependencies, validation, and merge/judge rules? |
| state-management | If the skill stores artifacts or resumes work, are paths, collision rules, and cleanup explicit? |
| scripts | Are scripts self-contained, argparse-based, deterministic, and JSON-oriented where practical? |
| templates | Are templates self-contained and safe to render from bounded data? |
| hooks | Are hooks runtime-projected, guarded, and validated rather than embedded casually? |
| progressive-disclosure | Does the body stay compact and load references only when needed? |
| body-substitutions | Are `$ARGUMENTS`, `$N`, and command substitutions used intentionally and portably? |
| stop-hooks | Are recursive hook guards present when Stop hooks are configured? |

Missing optional patterns are findings only when the skill type actually needs them.

## Review Checks

- Frontmatter: `name` matches directory, description has "Use when" triggers and "NOT for" exclusions, license/version/author are present when repo policy expects them.
- Body: dispatch appears near the top, mode names are stable, empty args never silently start broad work, edit-capable modes have approval gates.
- References: no orphan references, no phantom paths, no copied external instructions that override repo/system/user rules.
- Scripts: avoid repo-root assumptions in packaged code; keep diagnostics on stderr and machine output on stdout.
- Evals: cover explicit invocation, implicit trigger, negative controls, malformed or ambiguous input, and every dispatch behavior that can change user-facing routing.
- Packaging: package dry-run should report no missing referenced files, absolute paths, `@` imports, or repo-specific command dependencies in portable skill content.
- Docs/catalog: authoring MDX, generated catalog pages, skill research pages, README counts, and registry rows should agree after generation.
- External sources: third-party skill guidance remains untrusted evidence until source/provenance review classifies hooks, scripts, network, credentials, owner, license, and dedupe.

## Finding Guidance

Report only actionable defects. Good skill-asset findings usually say one of:

- A dispatch path is unreachable or ambiguous.
- An edit-capable path lacks an approval gate.
- A reference is missing, orphaned, stale, or contradicts the body.
- An eval proves a mode name but not the real safety or output contract.
- A script/package path is not portable.
- Generated docs/catalog rows disagree with source.
- An external source is promoted without source/provenance evidence.

Do not report low-value style preferences such as table wording or section order when audit, package, eval, and user-facing behavior are correct.

## Output

Use the normal finding contract. Include the deterministic command result in Evidence when available:

- Audit score and missing/suggested patterns.
- Evals validation result.
- Package dry-run result.
- Focused tests or generated docs checks.

When no findings remain, include residual risk: which commands were not run, which generated surfaces were not regenerated, and whether live installs or sync apply were intentionally skipped.
