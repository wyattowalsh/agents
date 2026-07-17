# Tasks: add-lm-studio-harness

## W0 OpenSpec

- [x] Proposal / design / tasks scaffold

## W2 Implementation

- [x] Platform adapter + register + sync_home wire
- [x] Registries (harness-surface, mcp, plugin, sync-manifest)
- [x] harness-master classify + discover + SKILL + authoring
- [x] MCPHub wrapper
- [x] rtk + image-input + fixture-support

## W3 Tests

- [x] `tests/test_lm_studio_platform.py`
- [x] distribution metadata expectations
- [x] classify_intent aliases / all-order

## W4 Docs

- [x] AGENTS.md Supported Agents row
- [x] wagents/cli.py Supported Agents bullet
- [x] platforms/lm-studio/README.md

## W5 Gates

- [x] pytest slice green (`tests/test_lm_studio_platform.py`, `tests/test_distribution_metadata.py`, `tests/test_discovery_classify_intent.py`)
- [x] sync --check for lm-studio (proposes update under pointer home)
- [x] discover_surfaces smoke

## V3 full surfaces

- [x] `instructions/lm-studio-global.md`
- [x] presets (instructions + agents) + skills mirror in adapter
- [x] projection_surfaces: mcp, instructions, skills, agents
- [x] docs/README/AGENTS updated (not MCP-only)

## V5 harden / close (RV-S-*)

- [x] RV-S-001: no absolute path in instruction preset body
- [x] RV-S-002: skill mirror modes none|allowlist|all; default none
- [x] RV-S-003: structural preset key asserts in unit tests
- [x] RV-S-004: remove dead `lms` wrapper branch
- [x] RV-S-005: `is_relative_to` for skill ownership checks
- [x] RV-S-006: stage map only (no corpus noise; commit gated)
- [x] RV-S-007: OpenSpec skill requirement rewritten for default none
- [x] RV-S-008: mode=none purges prior managed skill symlinks
- [x] RV-S-009: residual v5 checklist (this section)
- [x] RV-S-010: tests mode matrix + purge + home surface expectations
- [ ] RV-S-011: verify legacy-shaped presets in the current LM Studio schema/UI
  before promoting beyond `repo-present-validation-required`
