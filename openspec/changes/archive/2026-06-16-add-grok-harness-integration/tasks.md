# Tasks — Hyperfine parallel execution graph

47 tasks across 9 waves. Format: `ID | Wave | Team | Depends | Files | Acceptance`

## Orchestration mode

- **Pattern E**: team lead dispatches waves; teammates own disjoint files.
- **Accounting rule**: N dispatched = N resolved; no silent skips.
- **Conflict rule**: one writer per file per wave; `sync_agent_stack.py` owned only by T4.

## Team roster

| Team | Teammate | Exclusive write paths |
|------|----------|----------------------|
| T0 | t0-contract | `openspec/changes/add-grok-harness-integration/**` |
| T1 | t1-policy | `config/grok-config.toml`, `config/grok-env.sh`, `config/tooling-policy.json`, `config/sync-manifest.json`, `instructions/grok-global.md` |
| T2 | t2-registry | `agent-bundle.json`, `config/harness-surface-registry.json`, `config/mcp-registry.json` |
| T3 | t3-adapter | `wagents/platforms/grok.py`, `wagents/platforms/__init__.py` |
| T4 | t4-monolith | `scripts/sync_agent_stack.py` |
| T5 | t5-cli | `wagents/cli.py` |
| T6 | t6-inventory | `wagents/installed_inventory.py` |
| T8 | t8-tests | `tests/test_grok_platform.py`, grok tests in sync/cli/inventory modules |
| T9 | t9-docs | `AGENTS.md`, `docs/src/content/docs/cli.mdx`, `skills/harness-master/SKILL.md`, `wagents/site_model.py` |
| T10 | t10-gate | read-only validation only |

---

## Wave 0 — Contract (3 parallel)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-001 | T0 | — | Scaffold change + validation-matrix.md | `wagents openspec validate` passes |
| GROK-002 | T0 | — | Audit live `~/.grok/config.toml` + `grok --version` | Schema table in design.md |
| GROK-003 | T0 | — | Finalize `GROK_OWNED_*` + managed markers | Matches design.md ownership model |

**Gate G0:** Lead approves GROK-003.

---

## Wave 1 — Policy & registry (7 parallel)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-010 | T1 | GROK-003 | `config/grok-config.toml` sanitized template | No `/Users/` paths; tomllib loads |
| GROK-011 | T1 | GROK-003 | `model_defaults.grok` in tooling-policy.json | Adapter can consume keys |
| GROK-012 | T1 | GROK-002 | `instructions/grok-global.md` | Imports global.md; documents depth=1, env, restart |
| GROK-013 | T1 | GROK-012 | `config/grok-env.sh` | GROK_WEB_FETCH etc. documented |
| GROK-014 | T1 | GROK-010 | sync-manifest entries for new sources | Paths/modes correct |
| GROK-015 | T2 | GROK-001 | `grok-build` in harness-surface-registry | Surfaces: instructions, skills, agents, mcp, plugins |
| GROK-016 | T2 | GROK-001 | `grok` in agent-bundle supportedAgents + stub | Install note for claude alias |

**Gate G1:** `tomllib.load(open('config/grok-config.toml'))` succeeds.

---

## Wave 2 — Adapter (T3 sequential chain)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-020 | T3 | GROK-010,011 | Lift `render_grok_mcp_block` + markers into grok.py | Importable from adapter |
| GROK-021 | T3 | GROK-020 | `render_grok_base_config(policy)` | Matches template + policy |
| GROK-022 | T3 | GROK-021 | `render_preserved_grok_config(current)` | User tables survive |
| GROK-023 | T3 | GROK-022 | `render_config(..., repo_only=)` | Repo MCP-only vs home full |
| GROK-024 | T3 | GROK-023 | `sync_repo` | Writes config/grok-config.toml + .grok/config.toml |
| GROK-025 | T3 | GROK-023 | `sync_home` | Merges ~/.grok/config.toml |
| GROK-026 | T3 | GROK-025 | `is_available()` override | Detects grok binary or config |
| GROK-027 | T3 | GROK-025 | `assert_no_grok_config_drops` | Raises on owned-table loss |

**Gate G2:** `pytest tests/test_grok_platform.py` green.

---

## Wave 3 — Monolith (T4 sequential)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-030 | T4 | GROK-024,025 | Replace `merge_grok_config` with `sync_platform_*("grok")` | No duplicate MCP render |
| GROK-031 | T4 | GROK-030 | Add `--platforms` argparse | Home grok-only skips opencode |
| GROK-032 | T4 | GROK-030 | Remove/thin moved functions; fix test imports | sync tests import adapter |
| GROK-033 | T4 | GROK-030 | `sync_grok_agents` → ~/.grok/agents symlinks | Copilot pattern |

**Gate G3:** `sync_agent_stack.py --check --targets repo --platforms grok` exit 0.

---

## Wave 4 — CLI & inventory (5 parallel across T5+T6)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-040 | T5 | GROK-016 | `install()` maps grok via `skills_cli_agent_id()` | argv uses claude-code |
| GROK-041 | T5 | GROK-040 | Post-install `mirror_grok_skills_from_claude()` | Echo mirror count |
| GROK-042 | T5 | GROK-013 | `wagents grok doctor` subcommand | Reports config, env, MCP, skills |
| GROK-043 | T6 | GROK-041 | Scan repo `.grok/skills` when present | Inventory test passes |
| GROK-044 | T6 | GROK-043 | Dedupe grok+claude duplicate skill rows | One row per skill name |

**Gate G4:** `pytest tests/test_cli_integration.py -k grok` green.

---

## Wave 5 — MCP decision (blocked on lead)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-050 | T2 | GROK-030 | **Decision:** group-only vs chrome-devtools server for grok | Recorded in design; default keep group-only |
| GROK-051 | T2 | GROK-050 | Apply mcp-registry projection if approved | MCP tests updated |

**Gate G5:** Lead sign-off on GROK-050.

---

## Wave 6 — Tests (7 parallel)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-060 | T8 | GROK-027 | Create `tests/test_grok_platform.py` | render + preserve + availability |
| GROK-061 | T8 | GROK-027 | `test_grok_merge_preserves_user_sections` | Custom [user] table fixture |
| GROK-062 | T8 | GROK-040 | `test_install_grok_uses_claude_adapter_and_mirrors` | cli integration |
| GROK-063 | T8 | GROK-031 | `test_sync_platforms_grok_only_skips_opencode` | Platform filter |
| GROK-064 | T8 | GROK-042 | `test_grok_doctor_reports_missing_env` | Doctor warnings |
| GROK-065 | T8 | GROK-033 | `test_sync_grok_agents_creates_symlinks` | Temp home fixture |
| GROK-066 | T8 | GROK-010 | `test_grok_config_copy_matches_sanitized_template` | Repo file stable |

**Gate G6:** Full pytest harness subset green.

---

## Wave 7 — Docs (5 tasks, 4 parallel then generate)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-070 | T9 | G6 | Update AGENTS.md Grok section | grok-global, grok-config, doctor |
| GROK-071 | T9 | G6 | Update docs/cli.mdx | install alias, sync, doctor |
| GROK-072 | T9 | G6 | Update harness-master SKILL.md | Adapter + env |
| GROK-074 | T9 | G6 | site_model DistributionPath if gap | Site data includes grok |
| GROK-073 | T9 | GROK-070..072,074 | `wagents readme` + `wagents docs generate` | Generated consistent |

**Gate G7:** `wagents readme --check` + `wagents docs build`.

---

## Wave 8 — Ship gates (8 parallel checks)

| ID | Team | Depends | Task | Acceptance |
|----|------|---------|------|------------|
| GROK-080 | T10 | G7 | `uv run pytest` | 0 failures |
| GROK-081 | T10 | G7 | `uv run wagents validate` | 0 failures |
| GROK-082 | T10 | G7 | `ruff check wagents/ scripts/sync_agent_stack.py` | clean |
| GROK-083 | T10 | G7 | `uv run ty check` | clean |
| GROK-084 | T10 | G7 | `sync --check --targets repo` | no drift |
| GROK-085 | T10 | GROK-031 | `sync --apply --platforms grok --targets home` | user approval; no opencode |
| GROK-086 | T10 | GROK-085 | `~/.grok/bin/grok inspect` smoke | MCP + skills visible |
| GROK-087 | T10 | G7 | `wagents openspec validate` + archive | change complete |

**Gate G8 (ship):** All GROK-080..087 pass.

---

## Dependency DAG (critical path)

```
GROK-003 → GROK-010 → GROK-020 → GROK-021 → GROK-022 → GROK-023 → GROK-025 → GROK-027
  → GROK-030 → GROK-031 → GROK-060 → GROK-073 → GROK-080 → GROK-085 → GROK-087
```

**Max parallel width:** Wave 1 (7), Wave 6 (7), Wave 8 (8).

## Lead dispatch script

1. Wave 0: spawn GROK-001,002,003 in parallel.
2. Gate G0 → Wave 1: T1 (010-014) + T2 (015-016) parallel.
3. Wave 2: single T3 sequential 020→027.
4. Gate G2 → Wave 3: single T4 sequential 030→033.
5. Wave 4: T5 (040-042) || T6 (043-044).
6. Wave 5: lead decides GROK-050.
7. Wave 6: spawn 060-066 as six parallel test authors.
8. Gate G6 → Wave 7: 070,071,072,074 parallel → 073 sequential.
9. Wave 8: parallel validation; GROK-085 needs user OK.

## Coarse rollup todos

- [x] openspec-change (GROK-001..003, 087)
- [x] grok-policy-template (GROK-010..014)
- [x] grok-adapter (GROK-020..027, 060-061, 066)
- [x] monolith-platforms (GROK-030..033, 031, 063)
- [x] skills-install-fix (GROK-040..041, 062, 043-044)
- [x] agents-mcp-registry (GROK-015..017, 033, 050-051, 065)
- [x] env-and-docs (GROK-012..013, 042, 064, 070-074)
- [x] tests-validation (GROK-060..066, 080-086)

---

## Phase 2 — Hardening (GROK-088..111) — COMPLETE

| Area | Status |
|------|--------|
| Blend-owned merge (`ui`, `features`, etc.) | Done |
| Marker-less MCP strip | Done |
| Repo `.grok/skills` inventory (project scope) | Done |
| Doctor marker/env warnings | Done |
| Tests GROK-061,063-066,100-111 | Done |
| Docs cli.mdx + harness-master | Done |
| OpenSpec spec/design deltas | Done |
| Archive GROK-087 | Home apply done; archive pending |

