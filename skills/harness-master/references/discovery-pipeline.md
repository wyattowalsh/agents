# Discovery Pipeline

Gap analysis, coordinator scouts, and harness-bounded research for systematic expansion. Load for **Discover** mode only.

## Evidence vs contracts

| Layer | Location | Role |
| ----- | -------- | ---- |
| Contracts | `data/discovery/` (taxonomy, schemas, fixtures) | Skill-shipped JSON shapes |
| Evidence | `config/*` registries, `skills/`, `mcp/`, live harness files | Read-only repo truth (no docs index) |

Do not depend on `docs/src/generated-*`; run scripts directly.

## Depth inference

| User signal | Depth | Waves |
| ----------- | ----- | ----- |
| what's missing / expand collection | full | W0 → W4 |
| find best X for harness Y | focused | W0 + W2 + report |
| evaluate URL/package | candidate | dossier + `candidate_score.py` |
| compare A vs B | compare | normalize + score + rank |
| gaps only | w0only | W0 only |
| proposals only | ideate | W3 (needs prior journal) |
| resume / list | journal | `journal-store.py` |

Optional classifier:

```bash
uv run python skills/harness-master/scripts/discovery/classify_intent.py --args "<user args>" --json
```

## W0 deterministic scans

From repo root — see `references/discovery/coordinator-contract.md`:

```bash
python skills/harness-master/scripts/discovery/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json
python skills/harness-master/scripts/discovery/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json
python skills/harness-master/scripts/discovery/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json
python skills/harness-master/scripts/discovery/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hooks.json
python skills/harness-master/scripts/discovery/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json
python skills/harness-master/scripts/discovery/gap_engine.py \
  --taxonomy skills/harness-master/data/discovery/discovery-taxonomy.json \
  --inventory artifacts/<sid>/wave0/inventory.json \
  --mcp artifacts/<sid>/wave0/mcp.json \
  --plugins artifacts/<sid>/wave0/plugins.json \
  --harness artifacts/<sid>/wave0/surfaces.json \
  --hooks artifacts/<sid>/wave0/hooks.json \
  -o artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/validate_session.py artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/parity_check.py
```

Journal root: `~/.agents/harness-master/discovery/` (legacy `~/.*/discover-skills/` readable on list/resume only).

## W1–W4 orchestration

- **W1:** repo auditors (optional when W0 trusted)
- **W2:** scouts (max 24) — registry, web, MCP, plugin, harness, hook (report-only), policy; use `source_probe.py` / `npx_skills.py` per manifest
- **W2b:** `candidate_score.py` for candidate/compare depth
- **W3:** ideator proposals
- **W4:** interactive report per `references/discovery/output-formats.md`

```bash
python skills/harness-master/scripts/discovery/coordinator.py plan --gap ... --wave 2 ...
python skills/harness-master/scripts/discovery/coordinator.py verify --manifest ... --artifacts ...
python skills/harness-master/scripts/discovery/merge_artifacts.py --artifacts ... -o .../merged/candidates.json
```

## Redirects

| Signal | Route |
| ------ | ----- |
| ad-hoc "find skill for X" | `find-skills` / `npx skills find` |
| create skill | `skill-creator` |
| open-ended non-harness research | `/research` |
| config fixes from findings | Audit dry-run + `apply approved` |

## Read-only boundary

Discover never edits files or installs without explicit user confirmation. Harness-bounded web research stays inside scout artifacts; do not promote into instructions (`/learn`).