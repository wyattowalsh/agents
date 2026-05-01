# Design

## Overview

The release/archive lane turns completed child-lane planning into a safe release readiness package. It defines what must be true before release, how migration and rollback should work, and when OpenSpec archive actions are allowed.

## Artifact Model

| Artifact | Role |
| --- | --- |
| Phased rollout plan | Orders readiness, validation, release candidate, post-merge verification, and archive phases. |
| Migration guide | Maps current surfaces to planned control-plane contracts without applying live changes. |
| Rollback playbook | Defines non-destructive rollback paths for commits, config transactions, generated artifacts, and archive moves. |
| Release checklist | Captures pre-release, validation, docs, candidate, and post-merge gates. |
| Archive checklist | Defines evidence, order, and stop conditions for OpenSpec archive. |
| Release notes | Records child lane coverage, commit range evidence, validation evidence, exclusions, and known risks. |

## Safety Boundaries

- This lane is markdown-only.
- It does not archive changes; it prepares the archive gate.
- It does not regenerate derived docs or instruction mirrors.
- It does not mutate live configs or global desktop surfaces.
- It preserves unrelated dirty work by requiring exact pathspecs.

## Completion Criteria

The lane is complete when all six planning artifacts exist, C09 tasks are checked, OpenSpec validation passes, release evidence is current, and a scoped review finds no blockers.
