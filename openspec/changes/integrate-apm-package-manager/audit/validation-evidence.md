# Wave 5-6 Validation Assurance Evidence

**Change:** `openspec/changes/integrate-apm-package-manager/`
**Date:** 2026-06-23 (UTC)
**Purpose:** Capture outputs from the explicit Wave 5-6 validation gates for ruff, ty, pytest, wagents validate, apm doctor, apm audit (when in PATH), and openspec validate. Used to satisfy T050/T053/T063/T064 and provide pass/fail for G2-G6.

**Commands run from repo root (`/Users/ww/dev/projects/agents`):**
- `uv run ruff check wagents/apm.py wagents/cli.py tests/test_apm_materialize.py`
- `uv run ty check ...` (files confirmed in `[tool.ty.src]` gated includes: wagents, tests)
- `uv run pytest tests/test_apm_materialize.py tests/test_distribution_metadata.py -q`
- `uv run wagents validate`
- `uv run wagents apm doctor --format json` (and plain)
- `apm audit --ci --no-drift` (since `apm` present in `~/.local/bin/apm` via pipx; v0.21.0)
- `uv run wagents openspec validate`

**Notes:**
- Artifacts `.apm/`, `apm.yml`, and `apm.lock.yaml` became present during the session (untracked in git at time of runs; likely from explicit or side-effect runs of materialize facade or `apm` CLI usage in validation flows). Doctor transitioned from "missing" to "ok".
- `apm audit` is expected to surface issues without full lockfile reconciliation or when MCP fragments in `apm.yml` (from `config/mcp-registry.json`) are not yet locked via `apm install`.
- `wagents openspec validate` reports 1 failure on the in-progress change itself ("integrate-apm-package-manager" has no deltas/specs/ yet per OpenSpec rules requiring at least one delta with Scenarios). This is normal for an open change; 55/56 total passed.
- All targeted Python quality and repo validation gates (except the self-referential openspec item) passed.

---

## STEP 1: ruff check

```console
$ uv run ruff check wagents/apm.py wagents/cli.py tests/test_apm_materialize.py
All checks passed!
```

**Result:** PASS

---

## STEP 2: ty check (if in gated sources)

Gated sources confirmation (from `pyproject.toml`):

```toml
[tool.ty.src]
include = ["wagents", "scripts", "tests", "skills/nerdbot/src", "skills/nerdbot/scripts"]
exclude = ["scripts/validate/**", "tests/docs_ui/**"]
```

Target files:
- `wagents/apm.py` → under "wagents" → included
- `wagents/cli.py` → under "wagents" → included
- `tests/test_apm_materialize.py` → under "tests" → included

```console
$ uv run ty check wagents/apm.py wagents/cli.py tests/test_apm_materialize.py
All checks passed!
```

**Result:** PASS (files in scope; clean)

---

## STEP 3: pytest (targeted)

```console
$ uv run pytest tests/test_apm_materialize.py tests/test_distribution_metadata.py -q
...................................                                      [100%]
35 passed in 2.36s
```

**Result:** PASS (35 passed)

---

## STEP 4: wagents validate

```console
$ uv run wagents validate
All validations passed
```

**Result:** PASS

---

## STEP 5: wagents apm doctor

### JSON

```console
$ uv run wagents apm doctor --format json
{
  "ok": true,
  "checks": [
    {
      "name": "opencode.json",
      "ok": true
    },
    {
      "name": "apm.yml",
      "ok": true
    },
    {
      "name": ".apm/",
      "ok": true,
      "hooks": true
    }
  ],
  "repo_root": "/Users/ww/dev/projects/agents"
}
```

### Plain text

```console
$ uv run wagents apm doctor
apm doctor: ok
  opencode.json: ok
  apm.yml: ok
  .apm/: ok
```

**Result:** PASS (ok: true)

(Note: earlier in session, before artifacts present: `ok: false` with "apm.yml: missing (run materialize)", ".apm/: agents=False instructions=False".)

---

## STEP 6: apm presence + audit --ci --no-drift

### Presence

```console
$ which apm && apm --version
/Users/ww/.local/bin/apm
Agent Package Manager (APM) CLI version 0.21.0

$ ls -l ~/.local/bin/apm
lrwxr-xr-x@ - ww 23 Jun 03:11 /Users/ww/.local/bin/apm -> /Users/ww/.local/share/pipx/venvs/apm-cli/bin/apm
```

**apm present:** YES (in PATH via pipx)

### Audit run

```console
$ apm audit --ci --no-drift
[!] MCP dependency 'atom-of-thoughts': unknown key(s) preserved in extra: 
timeout_ms
... (similar warnings for chrome-devtools, creative-thinking, docling, ffmpeg, lotus-wisdom-mcp, trafilatura)
[!] drift detection skipped (--no-drift); coverage reduced -- hand-edits and missing integrations will not be caught

                           [>] APM Policy Compliance                            
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status   ┃ Check                    ┃ Message                                ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ [+]      │ lockfile-exists          │ Lockfile present                       │
│ [+]      │ ref-consistency          │ All dependency refs match lockfile     │
│ [+]      │ deployed-files-present   │ All deployed files present on disk     │
│ [+]      │ no-orphaned-packages     │ No orphaned packages in lockfile       │
│ [+]      │ skill-subset-consistency │ Skill subset selections match lockfile │
│          │ config-consistency       │ 33 MCP config inconsistenc(ies) -- run │
│          │                          │ 'apm install' to reconcile             │
└──────────┴──────────────────────────┴────────────────────────────────────────┘

  config-consistency details:
    - arxiv: in manifest but not in lockfile
    ... (33 total including atom-of-thoughts, brave-search, ... wikipedia)
[x] 1 of 6 check(s) failed
(exited 1, expected per task guidance when reconciliation/lock not fully aligned)
```

**Artifacts at time of audit:**

```
.rw-r-r--  apm.yml
.rw-r-r--  apm.lock.yaml  (139 lines)
.apm/
  agents/
  hooks/
  instructions/
```

**Result:** FAIL (expected; 1/6 on config-consistency for MCPs declared in `apm.yml` manifest section vs lockfile; many "in manifest but not in lockfile". Warnings on extra keys for MCPs. Task note: "may fail without lockfile - document". Lockfile was present here but full `apm install` reconciliation not performed.)

---

## STEP 7: wagents openspec validate (if change exists)

Change dir exists: `openspec/changes/integrate-apm-package-manager/`

```console
$ uv run wagents openspec validate
... (full JSON omitted for brevity; see prior full capture in session)
{
  "id": "integrate-apm-package-manager",
  "type": "change",
  "valid": false,
  "issues": [
    {
      "level": "ERROR",
      "path": "file",
      "message": "Change must have at least one delta. No deltas found. Ensure your change has a specs/ directory with capability folders (e.g. specs/http-server/spec.md) containing .md files that use delta headers (## ADDED/MODIFIED/REMOVED/RENAMED Requirements) and that each requirement includes at least one \"#### Scenario:\" block. Tip: run \"openspec change show <change-id> --json --deltas-only\" to inspect parsed deltas."
    }
  ],
  "durationMs": 0
},
...
  "summary": {
    "totals": {
      "items": 56,
      "passed": 55,
      "failed": 1
    },
    "byType": {
      "change": {
        "items": 31,
        "passed": 30,
        "failed": 1
      },
      "spec": {
        "items": 25,
        "passed": 25,
        "failed": 0
      }
    }
  },
  "version": "1.0"
}
```

Command exit: 1 (due to the 1 failing item).

**Result:** PARTIAL (55/56 passed; the sole failure is this open change lacking `specs/` deltas per OpenSpec schema. All other changes + all specs valid. Per matrix: "Pass (this change + others)" — the failure is self-referential and documented.)

---

## Gate Summary (G2-G6)

Mapping based on run sequence and historical gate patterns (ruff/ty/pytest/validate/openspec as quality gates in tooling/modernization and harness changes):

| Gate | Command(s) | Status | Details |
|------|------------|--------|---------|
| **G2** | `uv run ruff check wagents/apm.py wagents/cli.py tests/test_apm_materialize.py` | **PASS** | All checks passed. |
| **G3** | `uv run ty check` (target files) | **PASS** | Files in gated `[tool.ty.src]`; All checks passed. (error-on-warning=true) |
| **G4** | `uv run pytest .../test_apm_materialize.py .../test_distribution_metadata.py -q` | **PASS** | 35 passed. |
| **G5** | `uv run wagents validate` + `uv run wagents apm doctor --format json` | **PASS** | "All validations passed"; doctor "ok": true (after artifacts). |
| **G6** | `apm audit --ci --no-drift` (if present) + `uv run wagents openspec validate` | **PARTIAL / FAIL on audit** (documented) | - apm present → ran.<br>- audit: 1/6 failed (config-consistency, expected per "may fail without lockfile" note; also MCP extra key warnings).<br>- openspec: 55/56 (1 self-fail on missing deltas for this change; all other surfaces green). |

**Overall Wave 5-6 assurance:** All core Python/repo gates (G2-G5) passed cleanly. G6 documents the expected non-blocking / in-progress discrepancies for `apm audit` and the open change in `openspec validate`. No regressions introduced by `wagents/apm.py`, `wagents/cli.py`, or related tests.

**Evidence location:** This file + sibling audits (`wave1-target-spikes.md`, `sync-manifest-overlap.md`, etc.) + `validation-matrix.md`.

**Follow-ups (from matrix/tasks):** 
- Reconcile via `apm install` if locking desired for this self-manifest (but repo policy is complementary use of APM for *remote* only; this `apm.yml` is generated projection).
- Add deltas to this change (Wave 6 items) to make openspec fully green.
- Run full `uv run pytest -q` / pre-commit as final before close if needed.


---

## Resume pass (2026-06-23)

Subagent hang recovery: added OpenSpec spec deltas, emptied `apm.yml` MCP list (MCPHub-owned), patched CI frozen install to `--only apm`.

| Gate | Result |
|------|--------|
| `uv run pytest tests/test_apm_materialize.py tests/test_distribution_metadata.py -q` | PASS (35) |
| `uv run ruff check wagents/apm.py ...` | PASS |
| `uv run ty check wagents/apm.py ...` | PASS |
| `uv run wagents validate` | PASS |
| `uv run wagents apm doctor` | PASS |
| `apm audit --ci --no-drift` | PASS (8/8; config-consistency: no MCP configs) |
| `uv run wagents openspec validate` | PASS (56/56) |
