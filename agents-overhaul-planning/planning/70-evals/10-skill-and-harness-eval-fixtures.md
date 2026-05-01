# Skill and Harness Eval Fixtures

## Objective

Validate that skills and harness projections activate correctly without relying on model luck.

## Fixture types

| Fixture | Purpose |
|---|---|
| Activation prompt | Skill should be selected/loaded |
| Non-activation prompt | Skill should not be selected |
| Script dry-run | Executable helper behaves deterministically |
| Golden output | Stable output shape for CLI scripts |
| Harness projection | Generated config matches fixture |
| End-to-end install | Skill appears in target harness location |
| Docs truth | Generated docs mention correct support tier |

## Evaluation metrics

- activation precision/recall where measurable;
- script pass/fail;
- config diff exact match;
- docs matrix consistency;
- install smoke success;
- rollback success.
