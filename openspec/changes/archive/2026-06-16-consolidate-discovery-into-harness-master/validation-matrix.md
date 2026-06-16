# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| Harness-master portable check (discovery) | `uv run python skills/harness-master/scripts/discovery/check.py` | Exit 0; audit >= baseline (e.g. 92/100); evals pass; package dry-run ok | Exercises validate_session, parity_check (delegating), evals, etc. |
| Harness-master top-level check | `uv run python skills/harness-master/scripts/check.py` | Exit 0 | Harmonized with discovery/ sub-check. |
| Discovery unit tests | `uv run pytest tests/test_discovery_*.py -q --tb=line` | All pass (retargeted modules, new migration/delete guards) | gap_engine, coordinator, schemas, hook_scan, parity, no-wagents. |
| No-wagents boundary | `uv run pytest tests/test_skills_no_wagents.py -q -k "harness or discovery"` | Pass | Confirms no `wagents` imports under `skills/harness-master/scripts/discovery/`. |
| Repo discovery parity | `uv run python scripts/check_discovery_parity.py` | `{"ok": true, ...}` (repo_count matches expectations) | Primary parity guard; hook variant if separate. |
| Hook discovery parity | `uv run python scripts/check_hook_discovery_parity.py` | Exit 0 or ok json | Complements general parity (hook registry vs surfaces). |
| W0 pipeline (manual, new paths) | See coordinator-contract W0 block below (all scripts under `skills/harness-master/scripts/discovery/`) | `artifacts/<sid>/wave0/*.json` present + valid; `gap-report.json` passes `validate_session.py`; parity ok; journal written to `~/.agents/harness-master/discovery/<sid>/` | Full chain before wave-2. |
| W0 bash example | ```bash<br>python skills/harness-master/scripts/discovery/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json<br>python skills/harness-master/scripts/discovery/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json<br>python skills/harness-master/scripts/discovery/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json<br>python skills/harness-master/scripts/discovery/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json<br>python skills/harness-master/scripts/discovery/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hook-scan.json<br>python skills/harness-master/scripts/discovery/gap_engine.py \<br>  --taxonomy skills/harness-master/data/discovery/discovery-taxonomy.json \<br>  --inventory artifacts/<sid>/wave0/inventory.json \<br>  --mcp artifacts/<sid>/wave0/mcp.json \<br>  --plugins artifacts/<sid>/wave0/plugins.json \<br>  --harness artifacts/<sid>/wave0/surfaces.json \<br>  --hooks artifacts/<sid>/wave0/hook-scan.json \<br>  -o artifacts/<sid>/wave0/gap-report.json<br>python skills/harness-master/scripts/discovery/validate_session.py artifacts/<sid>/wave0/gap-report.json<br>python skills/harness-master/scripts/discovery/parity_check.py<br>``` | All exit 0; artifacts valid per schemas; gap-report includes hooks + other sections; journal v2 metadata present | Update contract doc too. |
| discover_surfaces (grok-build + peers) | `python skills/harness-master/scripts/discover_surfaces.py --repo-root . --harness grok-build --level both` (or via invoke) | JSON surfaces present; `kind: "hooks"` rows continue for supported harnesses; no regression | Grok harness hooks via registry projection. |
| Coordinator plan + verify (post-merge) | `python skills/harness-master/scripts/discovery/coordinator.py plan --gap artifacts/<sid>/wave0/gap-report.json --wave 2 ...` then stub scouts + `verify` | Manifest includes expected Wx-YY tasks (incl. harness-scout, hook-scout W2-HK-00); verify `ok: true` | Accounting + status success/skipped. |
| Inferred modes dispatch (harness-master) | Manual / eval: `/harness-master`, `/harness-master discover`, `/harness-master audit claude-code project`, `/harness-master research all skill`, natural language "what skills am I missing for codex?" etc. | Routes to appropriate intake/audit/research/discover/ideate flow; read-only for discover paths; no crash on legacy phrasing (notes redirect) | Update SKILL.md dispatch + tests/evals. |
| Journal path + resume | Run full discover that writes journal; then resume/list via harness-master | Journal dir created at `~/.agents/harness-master/discovery/<sid>/`; resume succeeds; legacy v1 fallback documented + works for old paths | v2 session_version + artifact_root. |
| OpenSpec validate | `uv run wagents openspec validate` (or `uv run python skills/openspec-workflow/scripts/openspec_cli.py validate`) | Pass for this change + all specs | 5 artifacts present; updated skills-lifecycle/spec.md delta + canonical; no discover-skills requirement text. |
| Full `wagents validate` | `uv run wagents validate` | Exit 0 | Packaging, skill manifests, hooks, docs, etc. |
| Docs / generated refresh | `uv run wagents docs generate` (or steward) + inspect | `docs/skills/harness-master.mdx` (or equiv) documents discovery pipeline + inferred modes; discover-skills page absent or redirected | KB indexes updated. |
| Packaging + dist | Build harness-master skill zip (via check or explicit) | `dist/harness-master-*.skill.zip` contains `scripts/discovery/`, `data/discovery/`, references/discovery/; no discover-skills zip produced | Size delta noted. |
| Hook scan schema + parity | Via validate_session or direct: produce hook-scan.json under new path; run hook parity | Accepts schema; parity ok (registry vs surfaces) | From prior add-hook work, still valid. |
| End-to-end with orchestrator (if applicable) | Dispatch via higher orchestrator using harness-master discover intent | Gap + scouts + artifacts produced under unified flow | Non-blocking for this change gate if out of scope. |

## W0 Full Example (from updated coordinator-contract, to be refreshed)

```bash
python skills/harness-master/scripts/discovery/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json
python skills/harness-master/scripts/discovery/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json
python skills/harness-master/scripts/discovery/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json
python skills/harness-master/scripts/discovery/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json
python skills/harness-master/scripts/discovery/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hook-scan.json
python skills/harness-master/scripts/discovery/gap_engine.py \
  --taxonomy skills/harness-master/data/discovery/discovery-taxonomy.json \
  --inventory artifacts/<sid>/wave0/inventory.json \
  --mcp artifacts/<sid>/wave0/mcp.json \
  --plugins artifacts/<sid>/wave0/plugins.json \
  --harness artifacts/<sid>/wave0/surfaces.json \
  --hooks artifacts/<sid>/wave0/hook-scan.json \
  -o artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/validate_session.py artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/parity_check.py
# then coordinator plan / wave execution / journal under ~/.agents/harness-master/discovery/<sid>/
```

## Blockers

- None for OpenSpec scaffolding. Migration execution may surface path drift in tests or journal fallback edge cases.

## Deferred Checks

- Full live journal migration of many historical v1 sessions (one-time user action).
- Parallel Wave 2+ with real (non-stub) scouts after merge (accounting already covered by prior work).
- Long-term removal of any legacy `discover-skills` mentions in user-facing external docs or blog posts (outside repo).
- Cross-skill install flows that may have referenced discover-skills in curated lists (post-delete `wagents skills list` verification).
- Performance / size impact on single harness-master skill zip (acceptable; discovery is core harness concern).
