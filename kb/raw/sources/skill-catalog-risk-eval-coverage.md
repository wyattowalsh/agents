---
title: Skill Catalog Risk Eval Coverage
tags:
  - kb
  - source
  - skills
  - evals
aliases:
  - Skill risk source
  - Eval coverage source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Skill Catalog Risk Eval Coverage

## Source Record

| Field | Value |
|-------|-------|
| source_id | `skill-catalog-risk-eval-coverage` |
| original_location | `wagents/cli.py`; `wagents/skill_index.py`; `tests/test_eval_cli.py`; `tests/test_skill_index.py`; `tests/test_skill_creator_audit.py`; `skills/skill-creator/scripts/audit.py`; selected `skills/*/evals/evals.json`; selected high-risk `skills/*/SKILL.md` |
| raw_path | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` |
| capture_method | repo-local pointer summary from read-only research and CLI-result evidence reported by subagent |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local skill, CLI, test, and eval material |
| intended_wiki_coverage | [[skill-catalog-risk-and-eval-coverage]], [[skill-authoring-and-validation]], [[validation-and-test-coverage]], [[known-risks-and-open-gaps]] |

## Summary

Skill eval presence is not the same as risk-adjusted coverage. The repository has CLI surfaces for eval validation and coverage, deterministic skill-audit checks, and examples of strong eval manifests that test invocation, refusal, no-mutation, and approval behavior. Research also found that several integration or high-consequence skills have no eval coverage by current coverage output.

The KB should track two labels independently: risk tier and eval coverage tier. This makes it possible to say that a low-risk prompt-only skill can be acceptable with lighter coverage, while browser, Gmail, filesystem cleanup, external-skill audit, security, or research workflows should have stronger coverage of refusal, approval, no-mutation, and boundary behavior.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents eval` implements list, validate, and coverage surfaces for skill evals. | `wagents/cli.py`; `tests/test_eval_cli.py` | implementation and tests | Subagent also reported current CLI counts. |
| Skill index code detects hooks and scripts but does not assign risk tiers or eval adequacy. | `wagents/skill_index.py`; `tests/test_skill_index.py` | implementation and tests | KB synthesis fills this gap. |
| Skill-creator audit scores evaluation coverage and validation contract dimensions. | `skills/skill-creator/scripts/audit.py`; `skills/skill-creator/references/evaluation-rubric.md`; `tests/test_skill_creator_audit.py` | implementation, reference, tests | Existing quality model. |
| Strong eval examples cover approval, no-edit, headless, untrusted-source, and external-script boundaries. | `skills/skill-creator/evals/evals.json`; `skills/nerdbot/evals/evals.json`; `skills/docs-steward/evals/evals.json`; `skills/external-skill-auditor/evals/evals.json`; `skills/agent-runtime-governance/evals/evals.json` | eval manifests | Representative evidence. |
| Some higher-risk integration skills currently lack eval coverage according to the research pass. | `skills/email-whiz/SKILL.md`; `skills/chrome-devtools/SKILL.md`; `skills/files-buddy/SKILL.md`; `skills/research/SKILL.md` | skill definitions and coverage result | Requires future coverage work, not fixed in this KB batch. |
