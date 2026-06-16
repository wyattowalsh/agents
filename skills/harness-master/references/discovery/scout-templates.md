# Scout Templates

Spawn prompts for coordinator-manifest scouts (Wave 2). Load ONE role at a time when executing a manifest task.

**Output contract:** Write `scout-artifact` JSON to the manifest `outputs.artifact` path (not stdout). Shape in `data/schemas/scout-artifact.schema.json`.

---

## Registry Scout

**Role:** Search skills.sh via bounded CLI for one manifest query.

**Inputs:** `query` string from manifest task.

**Steps:**

1. Run `python skills/harness-master/scripts/discovery/npx_skills.py find "<query>" --timeout-sec 45 -o <artifact-path>`.
2. Map `candidates` from CLI output into scout-artifact `candidates` with `name`, `source`, `install_count`, `fills_gap`.
3. Set `status: success` when CLI exits 0; `failed` with `errors` on timeout or non-zero exit.
4. Deduplicate against gap report `existing_skills`; skip duplicates.

---

## Web Researcher

**Role:** Bounded web research for one high-priority domain.

**Inputs:** `domain_id`, `domain_name` from manifest.

**Steps:**

1. Load `references/research-integration.md` for tool boundaries.
2. Search registry-adjacent sources (GitHub SKILL.md paths, skills.sh, reputable blogs) for the domain.
3. Emit installable leads as `candidates` with `source`, `install_command`, `fills_gap`.
4. Mark non-installable leads in `errors` or `provenance.notes` — do not fabricate install commands.

---

## MCP Scout

**Role:** Summarize MCP coverage gaps from W0 scan.

**Steps:**

1. Read `artifacts/<sid>/wave0/mcp.json` (or re-run `mcp_scan.py`).
2. Cross-reference `config/mcp-registry.json` enabled servers.
3. Emit `candidates` only for actionable external MCP packages; record blind spots in `provenance`.

---

## Harness Scout

**Role:** Summarize harness/plugin surface gaps.

**Steps:**

1. Read `artifacts/<sid>/wave0/surfaces.json` from `invoke_surfaces.py`.
2. Flag harnesses missing expected skill/MCP projection.
3. Do not edit harness configs — report only.

---

## Hook Scout

**Role:** Summarize hook surface coverage from W0 hook_scan (report-only).

**Steps:**

1. Read `artifacts/<sid>/wave0/hooks.json` (produced by hook_scan.py + hook registries).
2. Report harness hook projection claims vs actual registry + surface inventory.
3. Record blind spots for harnesses that declare "hooks" in harness-surface-registry but lack first-class support.
4. **candidates** are always `[]` — this scout is report-only (parity and gap documentation); no external hook "skills" are installed via discovery.

---

## Plugin Scout

**Role:** Summarize native plugin/extension ownership vs repo MCP fallback.

**Steps:**

1. Read `artifacts/<sid>/wave0/plugins.json`.
2. Note plugin-owned surfaces that suppress duplicate MCP entries.
3. Record blind spots (UI-only connectors) in `provenance`.

---

## Policy Scout

**Role:** Read curated external skill policy (evidence only).

**Steps:**

1. Read `config/external-skills.md` and planning manifests under `planning/manifests/` when present.
2. Emit candidates matching documented `npx skills add` commands not yet in inventory.
3. Never auto-edit policy files.

---

## Ideator (Wave 3)

**Role:** Propose custom skills for gaps not filled by external candidates.

**Input:** Merged `merged/candidates.json` + gap report.

**Steps:** Follow proposal rules in `references/team-templates.md` § Ideator. Write proposals to `wave3/proposals.json` or journal via `journal-store.py save`.

**Legacy:** Full prose templates remain in `references/team-templates.md` when no manifest is available.