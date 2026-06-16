# Proposal

## Problem

`discover-skills` orchestrates gap analysis and registry scouting via prose templates and LLM-produced JSON. Gap taxonomy lives in hand-edited markdown, scout outputs are not schema-validated, npx calls lack timeout handling, and MCP/plugin/harness dimensions are absent from the gap report. Resume state depends on journal regex blocks without artifact directory contracts.

## Intent

Refactor `discover-skills` into a portable discovery platform with stdlib Python scripts, machine-readable contracts, coordinator manifests for massively parallel scout waves, and filesystem artifact handoffs—without adding discovery logic to `wagents/`.

## Scope

- Add `data/discovery-taxonomy.json`, `data/agent-targets.json`, and JSON schema contracts.
- Add scripts: `gap_engine`, `inventory_scan`, `mcp_scan`, `plugin_scan`, `invoke_surfaces`, `npx_skills`, `coordinator`, `merge_artifacts`, `validate_session`, `render_gap_reference`, `schemas`.
- Extend journal sessions with artifact paths and checkpoint metadata.
- Update SKILL.md and references for W0 deterministic scans + coordinator manifests.
- Add tests and evals for gap engine, coordinator accounting, and npx timeout behavior.

## Out Of Scope

- `wagents discover` CLI module or embedding search.
- Auto-editing `config/external-skills.md`.
- Merging `skill-router` into `discover-skills`.

## Affected Surfaces

- `skills/discover-skills/**`
- `tests/test_discovery_*.py`
- Generated `references/gap-analysis.md` via `render_gap_reference.py`