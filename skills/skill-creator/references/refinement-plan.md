# Standalone Refinement Plan

Use this reference when `skill-creator` is asked to plan improvements for one
existing skill, a group of related skills, or the whole repo.

## Output Contract

Every refinement plan must include:

1. target skill or skill cluster
2. baseline audit score and grade
3. highest-value findings to address
4. exact file targets
5. rationale for each change
6. expected score impact
7. verification commands
8. explicit approval gate before edits

## Repo-Wide Planning Additions

When the request is repo-wide or multi-skill:

- inventory the current skill set first
- rank the work instead of listing it alphabetically
- identify shared authority surfaces and conflict zones
- group implementation into non-overlapping lanes
- produce one standalone refinement plan per promoted skill or tightly related cluster

## Approval Rule

Planning mode is read-only.

Do not:

- edit any skill
- regenerate docs
- update evals
- start implementation

until the user has approved the plan.

## Recommended Sections

- `Summary`
- `Baseline`
- `Ranked Findings`
- `Planned Changes`
- `Verification`
- `Approval Gate`

## File Target Guidance

Prefer naming the real target surfaces explicitly, for example:

- `SKILL.md`
- `references/*.md`
- `evals/*.json` or `evals/evals.json`
- scripts or templates only when the finding actually requires them
