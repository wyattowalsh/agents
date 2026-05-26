# Capability Model

Capabilities are atomic project setup features. Stable dotted IDs, such as `python.uv` or `docs.starlight`, allow future preferences to be added without changing `SKILL.md`.

## Required Semantics

| Field                   | Meaning                                                               |
| ----------------------- | --------------------------------------------------------------------- |
| `requires`              | Capability IDs that must be selected first                            |
| `conflicts`             | Capability IDs that cannot share the same target without a resolution |
| `implies`               | Capability IDs that should be added automatically                     |
| `risk_level`            | `low`, `medium`, or `high`                                            |
| `external_side_effects` | True for cloud, account, deploy, DNS, release, or publish mutation    |
| `mutates_files`         | True when the capability creates or edits project files               |
| `runs_install`          | True when package managers or generators run                          |

## Resolution

`scripts/catalog_utils.py` resolves requested capabilities into a closed graph by adding every non-excluded `requires` and `implies` dependency. `--without` exclusions are hard stops: if a requested or transitive capability is excluded, the blueprint is invalid instead of silently dropping that dependency.

## Conflict Handling

When conflicts appear, stop and ask a targeted question. Do not silently choose between docs frameworks, package managers, database primaries, deployment platforms, or release strategies.
