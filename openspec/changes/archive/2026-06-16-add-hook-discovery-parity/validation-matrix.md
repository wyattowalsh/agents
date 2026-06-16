# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| Skill portable check | `uv run python skills/discover-skills/scripts/check.py` | Exit 0 | Includes validate, evals, package dry-run, audit. |
| Discovery unit tests | `uv run pytest tests/test_discovery_*.py -q --tb=line` | All pass (incl. new hook scan / gap hooks / coordinator HK scout tests) | Schemas, gap engine, no-wagents boundary, coordinator roles. |
| W0 pipeline (manual) | See coordinator-contract W0 block below; include `hook_scan.py` | `artifacts/<sid>/wave0/hook-scan.json` present + valid; `gap-report.json` contains `hooks` key and passes `validate_gap_report`; `validate_session` ok | Full chain before wave-2. |
| W0 bash example | ```bash<br>python skills/discover-skills/scripts/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hook-scan.json<br>python skills/discover-skills/scripts/gap_engine.py \<br>  --taxonomy skills/discover-skills/data/discovery-taxonomy.json \<br>  --inventory artifacts/<sid>/wave0/inventory.json \<br>  --mcp artifacts/<sid>/wave0/mcp.json \<br>  --plugins artifacts/<sid>/wave0/plugins.json \<br>  --harness artifacts/<sid>/wave0/surfaces.json \<br>  --hooks artifacts/<sid>/wave0/hook-scan.json \<br>  -o artifacts/<sid>/wave0/gap-report.json<br>python skills/discover-skills/scripts/validate_session.py artifacts/<sid>/wave0/gap-report.json<br>python skills/discover-skills/scripts/parity_check.py<br>``` | All exit 0; hook-scan validated by schema; gap-report includes hooks section | Update contract doc too. |
| discover_surfaces for Grok Build | `python skills/harness-master/scripts/discover_surfaces.py --repo-root . --harness grok-build --level both` (or via invoke) | JSON with surfaces (hooks kinds for supported harnesses continue to appear; no regression) | Grok harness still lacks native hooks projection today per registry caveats. |
| Parity check (discovery) | `uv run python scripts/check_discovery_parity.py` | `{"ok": true, ...}` (extended to cover hook counts/surfaces if implemented in guard) | See tasks for HK parity items. |
| OpenSpec validate | `uv run python skills/openspec-workflow/scripts/openspec_cli.py validate` (or `uv run wagents openspec validate`) | Pass for this change + all specs | All 5 artifacts + updated skills-lifecycle/spec.md present. |
| Coordinator plan + verify (with hooks) | `python skills/discover-skills/scripts/coordinator.py plan --gap ... --wave 2 ...` then verify after stub scout artifact for HK-00 | Manifest includes W2-HK-00 with role "hook-scout"; verify `ok: true` when artifact present with valid scout-artifact + status success/skipped | Hook-scout report-only (candidates:[]). |
| No wagents import boundary | `uv run pytest tests/test_skills_no_wagents.py -q -k discover` | Pass | hook_scan.py, _hook_collect (if added), etc. must not import wagents.* |
| Hook scan schema | `python -c 'from skills.discover_skills.scripts.schemas import validate_hook_scan, write_json, load_json; ...'` (or via validate_session) | Accepts produced hook-scan.json; errors only on bad shape | `data/schemas/hook-scan.schema.json` required. |

## W0 Full Example (from coordinator-contract, to be updated)

```bash
python skills/discover-skills/scripts/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json
python skills/discover-skills/scripts/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json
python skills/discover-skills/scripts/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json
python skills/discover-skills/scripts/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json
python skills/discover-skills/scripts/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hook-scan.json
python skills/discover-skills/scripts/gap_engine.py \
  --taxonomy skills/discover-skills/data/discovery-taxonomy.json \
  --inventory artifacts/<sid>/wave0/inventory.json \
  --mcp artifacts/<sid>/wave0/mcp.json \
  --plugins artifacts/<sid>/wave0/plugins.json \
  --harness artifacts/<sid>/wave0/surfaces.json \
  --hooks artifacts/<sid>/wave0/hook-scan.json \
  -o artifacts/<sid>/wave0/gap-report.json
python skills/discover-skills/scripts/validate_session.py artifacts/<sid>/wave0/gap-report.json
python skills/discover-skills/scripts/parity_check.py
```

## Blockers

- None identified for OpenSpec creation step. Actual impl waves (per HK-00x plan) may surface file ownership conflicts or schema drift.

## Deferred Checks

- Full parallel Wave 2 execution with real hook-scout prompt (report-only stub sufficient for accounting).
- Live Grok Build / other harness surface drift after extraction of hook surfaces (use grok-build command above + compare before/after).
- End-to-end with journal v2 + artifact_root including hook-scan.json.
- wagents hooks validate cross-check against hook_scan output (semantic parity, not required for discover gate).
