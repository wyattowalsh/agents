---
title: Validation And Test Coverage
tags:
  - kb
  - validation
  - tests
aliases:
  - Test coverage map
kind: concept
status: active
updated: 2026-05-01
source_count: 7
---

# Validation And Test Coverage

## Scope

This page maps validation gates and test families. It is not a claim that the full test suite currently passes.

## Summary

The repo has layered validation. `wagents validate` checks a minimal asset structure contract, while packaging checks stricter portability requirements. Generated README and docs have check commands and tests. OpenSpec wrapper behavior, skill inventory, external skill parsing, hooks, evals, catalog integrity, and Nerdbot workflow contracts each have dedicated pytest coverage.

Use this distinction when assessing a change: passing `wagents validate` does not imply portable skill packaging, docs freshness, or live harness sync safety. For Nerdbot KB work, the targeted verification is `uv run --project skills/nerdbot nerdbot inventory --root ./kb` followed by `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered`.

Hooks and evals are related but distinct: hooks enforce runtime/projection policy, while evals provide skill behavior regression coverage. Eval counts should not be treated as adequate without considering the risk tier of each skill.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents validate` has a smaller contract than packaging. | `kb/raw/sources/asset-validation-coverage.md` | raw source note | Key authoring gotcha. |
| Pytest files map to CLI, docs, package, OpenSpec, skills, hooks, evals, catalog, and Nerdbot contracts. | `kb/raw/sources/tests-and-validation.md` | raw source note | Source inventory only. |
| pytest, Ruff, ty, and uv docs are relevant upstream tooling sources. | `kb/raw/sources/external-tooling-docs.md` | external source note | Upstream semantics, not local pass/fail evidence. |
| Nerdbot KB work uses targeted inventory and lint checks. | `kb/raw/sources/nerdbot-runtime-contracts.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Distinct from full repo CI. |
| Hooks and evals form a control plane for runtime policy and regression coverage. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Dedicated hooks/evals source. |
| Skill eval coverage should be interpreted relative to skill risk. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | Adequacy gap. |

## Related

- [[developer-commands]]
- [[skill-authoring-and-validation]]
- [[wagents-cli-and-automation]]
- [[hooks-evals-control-plane]]
- [[skill-catalog-risk-and-eval-coverage]]
- [[known-risks-and-open-gaps]]
