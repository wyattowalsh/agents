# Release Pipeline Failure Modes

Use this file in `review` mode to identify structural release risk quickly.

## Common Structural Failures

### Rebuild Per Environment

- Symptom: staging and production use separate builds from the same commit.
- Why it matters: production behavior is no longer tied to the tested artifact.
- Correction: build once, promote the same immutable artifact end-to-end.

### Missing Rollback Point

- Symptom: the team can deploy forward but cannot name the last known-good release.
- Why it matters: rollback becomes improvised during production impact.
- Correction: define rollback candidate, restore steps, and decision owner before rollout starts.

### Weak Approval Surface

- Symptom: production approval is informal or evidence is scattered across tools.
- Why it matters: high-risk releases go live without a shared go/no-go checkpoint.
- Correction: define one approver, one approval packet, and explicit abort criteria.

### Unbounded Hotfix Lane

- Symptom: “emergency” releases bypass provenance, essential validation, or rollback prep.
- Why it matters: the recovery path becomes another unsafe change.
- Correction: keep hotfix scope narrow and preserve evidence, essential tests, and rollback readiness.

### Hidden Stateful Change

- Symptom: migrations, cache format changes, queue semantics, or worker behavior are not represented in rollout planning.
- Why it matters: app rollback may not restore system behavior.
- Correction: surface stateful dependencies in the release design and choose rollout shape accordingly.

### No Post-Release Verification

- Symptom: release completes after deploy success without customer-impact checks.
- Why it matters: bad releases linger until customers report them.
- Correction: define smoke checks, business signals, and maximum time to declare release health.

### Freeze Window Without Ownership

- Symptom: freeze is declared, but exception handling and scope control are unclear.
- Why it matters: parallel changes erode the release baseline during cutover.
- Correction: name who can grant exceptions and what qualifies as release-critical work.

## Review Shortcut

When reviewing an existing pipeline, ask in order:

1. Is one immutable artifact promoted?
2. Is production approval explicit and evidence-backed?
3. Is rollback prepared before rollout?
4. Are stateful dependencies accounted for?
5. Is post-release verification part of the release, not an afterthought?
