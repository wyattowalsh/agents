# Proposal

## Problem

Skill validators and packaging depended on repo-root paths and wagents CLI references,
breaking portable ZIP installs and SKILL_PORTABLE_CI gates.

## Intent

Bundle asset_toolkit per in-scope skill, standardize scripts/check.py with portable CI mode,
enforce P7 body operator path hygiene, and gate CI via pytest.

## Validation

- make skill-portability-check
- make skill-toolkit-sync-check
- SKILL_PORTABLE_CI=1 uv run pytest tests/test_skill_portability.py -q
- uv run wagents validate
