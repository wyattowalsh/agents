# Design

## Boundary

Discovery logic lives only under `skills/discover-skills/scripts/`. Skills must not import or reference `wagents` per `tests/test_skills_no_wagents.py`.

`inventory_scan.py` delegates to `skills/skill-router/scripts/skill_index.py` via subprocess. `invoke_surfaces.py` delegates to `skills/harness-master/scripts/discover_surfaces.py`.

## Artifact Layout

```
artifacts/<session_id>/
  checkpoint.json
  wave0/{inventory,mcp,plugins,surfaces,gap-report}.json
  wave1/W1-RA-*.json
  wave2/manifest.json + W2-*.json
  wave3/proposals.json
  merged/candidates.json
```

## Accounting

`coordinator.py verify` enforces `resolved_count == expected_count` before ideation. Scout artifacts use `scout-artifact` schema with `status: success|skipped|failed`.

## npx Hardening

`npx_skills.py` uses process groups, SIGTERM/SIGKILL on timeout, structured error JSON.

## Journal v2

Frontmatter `session_version: 2` plus `artifact_root` path. v1 journals remain loadable.