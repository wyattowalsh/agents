# Provenance and Evidence Checklist

Use this file when defining what evidence a production approver must see in `design`, `review`, `cutover`, `hotfix`, or `checklist`.

## Artifact Identity

Every release record should name:

- version or release candidate identifier
- source commit or merge SHA
- build job identifier
- artifact digest or immutable package reference
- target environments

## Build and Verification Evidence

Capture:

- build success record for the promoted artifact
- test and verification status tied to the same artifact
- signing, packaging, or attestation record when required
- exception log for any skipped checks in a hotfix lane

## Approval Evidence

Before production, name:

- release lead
- production approver
- rollout operator
- communications owner for customer-facing risk
- exact go/no-go evidence the approver reviewed

## Release-Day Evidence

Record:

- start time and freeze confirmation
- artifact promoted to each environment
- rollout pattern and exposure checkpoints
- success signals, abort signals, and rollback point
- post-release smoke checks and customer-impact verification

## Post-Release Closure

Complete the release record with:

- final rollout outcome
- whether rollback was needed
- incidents or follow-up actions opened
- hygiene restoration tasks after any hotfix lane

## Approval Rule

If an approver cannot answer “what artifact is going live, what evidence supports it, and what rollback point exists,” the release is not ready.
