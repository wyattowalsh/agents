# Review Finding Contract

Every reported issue must be a discrete, falsifiable finding. Do not report broad vibes, style preferences, or speculative concerns that cannot be tied to evidence.

## Required Fields

| Field | Requirement |
| --- | --- |
| `id` | Stable review ID such as `RV-S-001`, `RV-A-002`, `RV-PR-003`, or `RV-SRC-004` |
| `local_id` | Worker-local ID before Judge assigns a canonical `RV-*` ID |
| `lane_id` | Review lane or specialist lens that produced the finding |
| `shard_id` | Wave 0 shard assignment that scoped the work |
| `reviewer_id` | Reviewer or subagent role that produced the finding |
| `scope` | Exact file, source, PR hunk, URL, or command output reviewed |
| `coverage` | What was inspected, skipped, blocked, or degraded |
| `citation` | Verified source anchor, PR hunk, command-output anchor, or provenance URL |
| `reasoning` | Two or three sentences explaining why the issue matters before stating the issue |
| `finding` | One concise statement of what is wrong |
| `severity` | P0-P3 for defect priority and S0-S3 for scope/blast radius when useful |
| `confidence` | 0.0-1.0 score after verification |
| `evidence` | Tool/source/test/docs/research proof; include degraded-mode limitations |
| `recommendation` | Smallest safe next step |
| `status` | `reported`, `unconfirmed`, `discarded`, `self-verified`, or `suppressed-by-learning` |

## Severity

| Level | Meaning |
| --- | --- |
| P0 | Data loss, exploit, broken release, irreversible user harm, or production outage |
| P1 | High-impact correctness, security, compatibility, or reliability issue |
| P2 | Medium-risk defect, maintainability issue with clear cost, or missing test around risky code |
| P3 | Low-risk improvement, clarity issue, or localized test/documentation gap |
| S0 | Affects critical path, public contract, or security boundary |
| S1 | Affects multiple modules, workflows, or user-visible behavior |
| S2 | Affects one module or repeated internal path |
| S3 | Localized issue with small blast radius |

## Confidence

| Score | Treatment |
| --- | --- |
| >= 0.9 | Strongly verified by source plus tests/docs/research |
| 0.7-0.89 | Report as verified |
| 0.3-0.69 | Report only as unconfirmed when useful |
| < 0.3 | Discard unless P0/S0 evidence demands escalation |

## Reporting Rules

1. Reasoning comes before the finding statement.
2. Citation anchors must exist and must contain the described code or source fact.
3. If a finding depends on an external standard, library behavior, vulnerability, legal rule, pricing, or current platform behavior, verify against a current primary source when available.
4. If validation is unavailable, mark the finding degraded and cap confidence.
5. Do not turn a strength into an issue just to fill a report.
6. Do not hide P0/P1 findings to preserve a positive tone.
7. Worker artifacts use `local_id`; Judge assigns canonical `RV-*` IDs only after dedupe and conflict resolution.
