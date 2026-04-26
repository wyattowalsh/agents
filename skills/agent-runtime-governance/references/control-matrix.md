# Agent Runtime Control Matrix

Use this reference when designing or auditing production agent runtime controls.

## 1. Risk Tiers

| Tier | Meaning | Default Control |
|---|---|---|
| Low | Read-only, local, reversible, no sensitive data | Allow with logging |
| Medium | Writes local files, changes internal state, or reads sensitive context | Require scoped approval or policy guard |
| High | External writes, user messaging, credential access, deploys, or money movement | Require explicit approval and audit trail |
| Critical | Destructive, public, irreversible, regulated, or broad-account action | Require human review, dry run, rollback plan, and post-action verification |

## 2. Tool Permission Review

- Name every tool and the operations it can perform.
- Distinguish read-only from write-capable behavior.
- Identify hidden writes such as cache updates, generated files, telemetry uploads, and global installs.
- Require allowlists or wrappers for tools with broad filesystem, network, or shell access.
- Deny or gate commands that bypass review, such as force pushes, destructive git operations, or silent package installs.

## 3. Approval Gates

Approval should be explicit when an action is:

- irreversible or hard to rollback
- public or user-visible
- credential-bearing
- financial or quota-consuming
- destructive to data, files, cloud resources, or account state
- based on low-confidence inference

Every gate needs: trigger condition, approver, evidence shown before approval,
execution command, and verification after execution.

## 4. Memory And State

- Use the narrowest memory scope that serves the workflow.
- Store decisions and stable preferences, not secrets or raw sensitive payloads.
- Define retention and invalidation rules for stale facts.
- Separate user memory from project memory and local scratch state.
- Treat memory reads as evidence only when freshness and provenance are clear.

## 5. Telemetry And Auditability

Capture:

- tool call, arguments, timestamp, and outcome
- approval prompts, approval/denial result, and evidence shown
- model or agent handoffs where supported
- failed commands and retry decisions
- containment actions such as rollback, quarantine, or abort

Avoid logging secrets, raw PII, or large source payloads unless explicitly required.

## 6. Evals And Failure Containment

Minimum eval scenarios:

- attempts destructive tool use without approval
- uses stale memory when fresh repo evidence contradicts it
- receives prompt injection from an external document
- tries to persist or reveal credentials
- fails a command and claims success anyway
- needs rollback after a partially completed action

Containment plans should define stop conditions, rollback commands, owner
notification, evidence capture, and post-incident learning.
