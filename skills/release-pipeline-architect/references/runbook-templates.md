# Runbook and Checklist Templates

Use these templates in `cutover`, `hotfix`, and `checklist`.

## Cutover Runbook Template

```text
Release:
Artifact:
Rollback Point:
Release Lead:
Production Approver:
Rollout Operator:
Communications Owner:

1. Preflight
- Confirm freeze state
- Confirm artifact identity and evidence packet
- Confirm rollback point and restore owner

2. Promotion
- Promote artifact to target environment
- Confirm target version and environment state

3. Rollout
- Rollout pattern:
- Exposure checkpoint(s):
- Success signal(s):
- Abort signal(s):
- Max decision latency:

4. Verification
- Smoke checks:
- Customer-impact checks:
- Dependency checks:

5. Close or Roll Back
- If healthy, declare completion and archive evidence
- If unhealthy, execute rollback and capture follow-up work
```

## Hotfix Lane Template

```text
Incident:
Smallest repair:
Artifact:
Essential validation kept:
Checks skipped with justification:
Production approver:
Rollback point:
Immediate post-deploy checks:
Follow-up work to restore normal hygiene:
```

## Release Checklist Template

Use binary items only.

```text
Preparation
- [ ] Artifact identity recorded
- [ ] Required checks tied to artifact
- [ ] Production approver named
- [ ] Rollback point confirmed

Promotion
- [ ] Staging or pre-prod promotion completed
- [ ] Approval evidence reviewed

Rollout
- [ ] Rollout pattern selected
- [ ] Abort signals defined
- [ ] Communications owner ready if needed

Validation
- [ ] Smoke checks defined
- [ ] Customer-impact checks defined

Rollback Readiness
- [ ] Restore owner named
- [ ] Rollback steps verified current
```
