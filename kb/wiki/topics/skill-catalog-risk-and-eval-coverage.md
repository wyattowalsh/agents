---
title: Skill Catalog Risk And Eval Coverage
tags:
  - kb
  - skills
  - evals
  - risk
aliases:
  - Skill risk coverage
  - Eval coverage matrix
kind: concept
status: active
updated: 2026-05-01
source_count: 1
---

# Skill Catalog Risk And Eval Coverage

## Scope

This page defines a practical risk-adjusted way to discuss skill eval coverage. It does not add missing evals or certify current coverage as sufficient.

## Risk And Coverage Labels

| Label | Meaning |
|-------|---------|
| `R0` | Prompt-only or advisory skill with no expected mutation. |
| `R1` | Local read-only analysis or audit workflow. |
| `R2` | Local file/package/docs mutation after normal approval. |
| `R3` | External systems, browser, network, harness config, or package execution. |
| `R4` | High-consequence mutation involving email, deletion, secrets, deploys, credentials, or broad filesystem cleanup. |
| `E0` | No evals under `skills/<name>/evals/`. |
| `E1` | Legacy eval JSON files present. |
| `E2` | Canonical `evals/evals.json` manifest present and valid. |
| `E3` | Behavioral coverage includes explicit invocation, implicit trigger, negative control, and refusal cases. |
| `E4` | Risk-backed coverage includes approval gates, no-mutation fallback, untrusted-input handling, destructive-action refusal, and credential/network boundaries. |

## Summary

Eval presence should be interpreted relative to skill risk. A low-risk prompt-only skill can have lighter coverage, but browser, Gmail, filesystem cleanup, external-skill audit, security, and research workflows should target stronger behavior and boundary coverage.

The current CLI can report eval coverage and validate manifest shape. It does not by itself grade risk-adjusted adequacy across all skills, so the KB uses this page to preserve that distinction for future authoring and audit work.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Eval validation and coverage are implemented in `wagents`. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | CLI and tests. |
| Existing audit logic already scores evaluation coverage and validation contracts. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | Skill-creator audit reference. |
| Some higher-risk integration skills lack eval coverage and need future work. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | Research finding; not fixed here. |

## Related

- [[skill-authoring-and-validation]]
- [[validation-and-test-coverage]]
- [[hooks-evals-control-plane]]
- [[known-risks-and-open-gaps]]
