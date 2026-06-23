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
6. expected structural score impact
7. expected behavioral impact or benchmark signal
8. lifecycle packet summary: source evidence, trigger surface, eval plan, security posture, runtime matrix, and baseline
9. verification commands
10. explicit approval gate before edits

## Repo-Wide Planning Additions

When the request is repo-wide or multi-skill:

- inventory the current skill set first
- rank the work instead of listing it alphabetically
- identify shared authority surfaces and conflict zones
- group implementation into non-overlapping lanes
- include a graph of lane ids, owned paths, dependencies, artifacts, validation, and judge criteria
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
- `Lifecycle Packet`
- `Planned Changes`
- `Task Graph`
- `Security And Runtime Notes`
- `Verification`
- `Approval Gate`

## File Target Guidance

Prefer naming the real target surfaces explicitly, for example:

- `SKILL.md`
- `references/*.md`
- `evals/*.json` or `evals/evals.json`
- scripts or templates only when the finding actually requires them

## Lifecycle Packet

Include this section when a plan changes behavior, dispatch, scripts, hooks,
evals, packaging, or public workflow semantics.

| Field | Required Content |
| --- | --- |
| Source evidence | Real task, runbook, transcript, code convention, incident, external source, or exemplar grounding the change |
| Trigger surface | Positive triggers and near-miss negatives affected by the change |
| Eval plan | Trigger, output, regression, safety, and portability cases to add or update |
| Security posture | Permission posture, scripts/hooks/tools/network/credential risks, and risk tier |
| Runtime matrix | Portable-core fields plus runtime-specific caveats |
| Baseline | Current score plus `without_skill` or `old_skill` behavioral baseline when relevant |

If source evidence is missing, mark the plan `needs-evidence` instead of
inventing a broad generic skill.

## Task Graph Contract

For multi-file or multi-skill work, include a compact graph:

| Column | Meaning |
| --- | --- |
| ID | Stable lane id |
| Lane | research, plan, implement, verify, docs, judge |
| Task | Bounded action |
| Depends | Blocking lane ids |
| Writes | Owned paths or `none` |
| Artifact | Expected output or validation proof |

Use maximum verified independence. Same-file edits, generated docs, OpenSpec
schema decisions, hooks, packaging semantics, and live installs serialize unless
a lock/arbiter protocol is explicit.

## Security And Runtime Notes

Every plan must state whether:

- scripts, hooks, network, credentials, installs, or destructive actions are in scope
- `allowed-tools` is advisory or enforced by the target runtime
- invocation controls are portable or runtime-specific
- third-party sources require quarantine or provenance review
- OpenSpec is required before implementation

Security-governance blockers override projected audit-score gains.
