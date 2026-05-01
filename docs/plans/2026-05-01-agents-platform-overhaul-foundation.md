# Agents Platform Overhaul Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the remaining non-commit foundation tasks for `agents-platform-overhaul` by adding repo-sync/drift manifests and fixture-backed harness support-tier evidence without overstating support.

**Architecture:** Keep OpenSpec as the control plane and add small machine-readable artifacts under `planning/manifests/` with schemas under `config/schemas/`. Treat `config/sync-manifest.json` and `config/harness-surface-registry.json` as inputs, then validate with focused schema tests before marking OpenSpec tasks complete.

**Tech Stack:** OpenSpec, JSON Schema draft 2020-12, Python `pytest`, `jsonschema`, `ruff`, `uv`, `wagents`.

---

## Current State

OpenSpec apply status for `agents-platform-overhaul` reports `25/28` tasks complete.

Remaining parent tasks:

- `Create non-Markdown repo-sync inventory and drift ledger.`
- `Add fixture-backed support tiers for each harness variant.`
- `Commit foundation changes.`

Child lane `agents-c00-repo-sync` currently has all tasks unchecked:

- `Inventory requested repo paths and classify each support/source tier.`
- `Produce planning/manifests/repo-sync-inventory.json.`
- `Produce planning/manifests/repo-drift-ledger.json.`
- `Update repo-sync narrative docs.`
- `Validate OpenSpec and registry fixtures.`

The commit task should remain unchecked until the user explicitly approves a selective commit because the worktree contains many unrelated pre-existing changes.

## Design Decisions

- Do not mark any harness `validated` unless it has concrete fixture evidence and rollback coverage.
- Add companion evidence manifests instead of inflating `config/harness-surface-registry.json` with large fixture detail.
- Keep support tiers unchanged: `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, `quarantine`.
- Treat repo-sync inventory as a ledger over `config/sync-manifest.json`, not as a replacement for it.
- Treat drift state as current observed planning state, not a live scan of user config values or secrets.
- Do not read secret-bearing config files directly; use path-level metadata from registries only.

## Artifacts To Add

Create these files:

- `planning/manifests/repo-sync-inventory.json`
- `planning/manifests/repo-drift-ledger.json`
- `planning/manifests/harness-fixture-support.json`
- `config/schemas/repo-sync-inventory.schema.json`
- `config/schemas/repo-drift-ledger.schema.json`
- `config/schemas/harness-fixture-support.schema.json`
- `planning/00-overview/12-repo-sync-and-drift-ledger.md`

Modify these files:

- `tests/test_distribution_metadata.py`
- `openspec/changes/agents-c00-repo-sync/tasks.md`
- `openspec/changes/agents-platform-overhaul/tasks.md`

Optionally modify after tests prove it is needed:

- `config/sync-manifest.json` only if the new schemas are treated as canonical sync-managed source.

Do not modify these files during this plan:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `docs/src/**` generated docs
- unrelated `nerdbot`, OpenCode plugin, or active integration files already dirty in the worktree

## Acceptance Criteria

- Every record in `config/sync-manifest.json["managed"]` is represented in `planning/manifests/repo-sync-inventory.json`.
- Every sync inventory record has path, mode, location class, source tier, owner change, drift policy, validation evidence, and secret handling classification.
- Every sync inventory path has a matching drift-ledger record.
- Every harness in `config/harness-surface-registry.json["harnesses"]` has a matching record in `planning/manifests/harness-fixture-support.json`.
- Harness fixture support records include fixture status, fixture class list, validation command list, rollback coverage status, and promotion blocker reason.
- No harness support tier is promoted beyond the current registry tier.
- New JSON artifacts validate against schemas.
- Focused tests pass before tasks are checked off.
- Parent OpenSpec progress reaches `27/28` with only commit remaining.

---

## Task 1: Add Failing Schema Coverage Tests

**Files:**

- Modify: `tests/test_distribution_metadata.py`

**Step 1: Add schema validation entries**

Extend `test_platform_overhaul_registries_validate_against_schemas()` with these pairs:

```python
(
    "planning/manifests/repo-sync-inventory.json",
    "config/schemas/repo-sync-inventory.schema.json",
),
(
    "planning/manifests/repo-drift-ledger.json",
    "config/schemas/repo-drift-ledger.schema.json",
),
(
    "planning/manifests/harness-fixture-support.json",
    "config/schemas/harness-fixture-support.schema.json",
),
```

**Step 2: Add sync inventory coverage test**

Add this test:

```python
def test_repo_sync_inventory_covers_sync_manifest_paths():
    sync_manifest = load_json("config/sync-manifest.json")
    inventory = load_json("planning/manifests/repo-sync-inventory.json")
    drift_ledger = load_json("planning/manifests/repo-drift-ledger.json")

    sync_paths = {record["path"] for record in sync_manifest["managed"]}
    inventory_paths = {record["path"] for record in inventory["records"]}
    drift_paths = {record["path"] for record in drift_ledger["records"]}

    assert sync_paths <= inventory_paths
    assert inventory_paths <= drift_paths

    for record in inventory["records"]:
        assert record["mode"] in {item["mode"] for item in sync_manifest["managed"] if item["path"] == record["path"]}
        assert record["owner_change"].startswith("agents-c")
        assert record["secret_handling"] in {"not-secret-bearing", "path-only", "redacted", "unknown"}
        assert record["drift_policy"] in {"canonical", "generated", "merged", "symlink", "symlinked-entries", "local-only"}
```

**Step 3: Add harness fixture evidence coverage test**

Add this test:

```python
def test_harness_fixture_support_covers_every_harness_without_tier_promotion():
    harness_registry = load_json("config/harness-surface-registry.json")
    fixture_support = load_json("planning/manifests/harness-fixture-support.json")

    harnesses = {record["id"]: record for record in harness_registry["harnesses"]}
    support = {record["harness_id"]: record for record in fixture_support["records"]}

    assert set(harnesses) == set(support)

    for harness_id, harness in harnesses.items():
        evidence = support[harness_id]
        assert evidence["current_support_tier"] == harness["support_tier"]
        assert evidence["owner_change"] == harness["owner_change"]
        assert evidence["fixture_status"] in {
            "fixture-backed",
            "fixture-plan-only",
            "docs-ledger-required",
            "blocked",
        }
        assert evidence["validation_commands"]
        assert evidence["rollback_coverage"] in {"present", "planned", "not-applicable", "blocked"}

        if harness["support_tier"] != "validated":
            assert evidence["promotion_blocker"]
```

**Step 4: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_distribution_metadata.py::test_platform_overhaul_registries_validate_against_schemas tests/test_distribution_metadata.py::test_repo_sync_inventory_covers_sync_manifest_paths tests/test_distribution_metadata.py::test_harness_fixture_support_covers_every_harness_without_tier_promotion -v
```

Expected result: fail because the three JSON artifacts and schemas do not exist yet.

---

## Task 2: Add Repo-Sync Inventory Schema

**Files:**

- Create: `config/schemas/repo-sync-inventory.schema.json`

**Step 1: Write minimal schema**

Schema shape:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RepoSyncInventory",
  "type": "object",
  "required": ["version", "source_ref", "records"],
  "properties": {
    "version": {"const": 1},
    "source_ref": {"const": "config/sync-manifest.json"},
    "records": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "path",
          "mode",
          "location_class",
          "source_tier",
          "owner_change",
          "drift_policy",
          "validation_evidence",
          "secret_handling"
        ],
        "properties": {
          "path": {"type": "string", "minLength": 1},
          "mode": {"enum": ["canonical", "generated", "merged", "symlink", "symlinked-entries"]},
          "location_class": {"enum": ["repo", "home", "application-support", "cache", "unknown"]},
          "source_tier": {"enum": ["canonical-source", "generated-output", "merged-live-config", "symlink-target", "local-runtime"]},
          "owner_change": {"type": "string", "pattern": "^agents-c[0-9]{2}-.+|agents-platform-overhaul$"},
          "drift_policy": {"enum": ["canonical", "generated", "merged", "symlink", "symlinked-entries", "local-only"]},
          "validation_evidence": {"type": "array", "items": {"type": "string", "minLength": 1}},
          "secret_handling": {"enum": ["not-secret-bearing", "path-only", "redacted", "unknown"]},
          "notes": {"type": "array", "items": {"type": "string", "minLength": 1}}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

**Step 2: Do not run full validation yet**

The paired manifest does not exist until Task 3.

---

## Task 3: Add Repo-Sync Inventory Manifest

**Files:**

- Create: `planning/manifests/repo-sync-inventory.json`

**Step 1: Build records from `config/sync-manifest.json`**

Use one record per `managed` entry.

Recommended classification rules:

- Paths under `/Users/ww/dev/projects/agents/` are `location_class: "repo"`.
- Paths under `/Users/ww/.config/`, `/Users/ww/.codex/`, `/Users/ww/.claude/`, `/Users/ww/.copilot/`, `/Users/ww/.gemini/`, or `/Users/ww/.aitk/` are `location_class: "home"`.
- Paths under `/Users/ww/Library/Application Support/` are `location_class: "application-support"`.
- `mode: "canonical"` maps to `source_tier: "canonical-source"` and `drift_policy: "canonical"`.
- `mode: "generated"` maps to `source_tier: "generated-output"` and `drift_policy: "generated"`.
- `mode: "merged"` maps to `source_tier: "merged-live-config"` and `drift_policy: "merged"`.
- `mode: "symlink"` maps to `source_tier: "symlink-target"` and `drift_policy: "symlink"`.
- `mode: "symlinked-entries"` maps to `source_tier: "symlink-target"` and `drift_policy: "symlinked-entries"`.

**Step 2: Assign owner changes**

Recommended owner mapping:

- `config/mcp-registry.json`, `mcp.json`, `.vscode/mcp.json`, global MCP configs: `agents-c03-mcp-audit` or harness lane when path is harness-specific.
- `config/hook-registry.json`, hooks paths, credential guard plugins: `agents-c06-config-safety`.
- `config/tooling-policy.json`, support tier, harness, docs, skill, plugin registries, schemas: `agents-c01-registry-core`.
- OpenCode paths and Gemini/Antigravity paths: `agents-c04-opencode-gemini-harness`.
- Claude paths: `agents-c04-claude-harness`.
- Codex paths: `agents-c04-openai-harness`.
- Copilot paths: `agents-c04-copilot-harness`.
- Cursor paths: `agents-c04-cursor-harness`.
- Cherry Studio, Crush, AITK paths: `agents-c04-experimental-harnesses`.
- OpenSpec paths: `agents-platform-overhaul` unless a specific child lane owns them.

**Step 3: Assign secret handling**

Recommended values:

- Repo canonical JSON/Markdown config paths: `not-secret-bearing`.
- Live app config paths likely to contain tokens, API keys, or server args: `path-only`.
- Generated config outputs that must redact values before logging: `redacted`.
- Unknown third-party global config paths: `unknown`.

**Step 4: Run focused validation**

Run:

```bash
uv run pytest tests/test_distribution_metadata.py::test_platform_overhaul_registries_validate_against_schemas tests/test_distribution_metadata.py::test_repo_sync_inventory_covers_sync_manifest_paths -v
```

Expected result: still fail until drift ledger exists.

---

## Task 4: Add Repo Drift Ledger Schema And Manifest

**Files:**

- Create: `config/schemas/repo-drift-ledger.schema.json`
- Create: `planning/manifests/repo-drift-ledger.json`

**Step 1: Write schema**

Required top-level fields:

- `version`
- `source_refs`
- `records`

Required record fields:

- `path`
- `expected_mode`
- `current_state`
- `drift_risk`
- `owner_change`
- `next_action`
- `validation_command`

Enums:

- `current_state`: `tracked-clean`, `tracked-dirty`, `untracked`, `generated-live`, `external-live`, `not-checked`
- `drift_risk`: `low`, `medium`, `high`

**Step 2: Create ledger records**

Use one record per `repo-sync-inventory.json` record.

Recommended conservative states:

- Repo files known dirty from `git-smart-status`: `tracked-dirty`.
- Repo canonical paths not observed dirty: `not-checked` unless explicitly known.
- Home/application-support paths: `external-live`.
- Generated paths: `generated-live`.
- Symlink entries: `generated-live` or `external-live` depending location.

Recommended `next_action` values:

- `preserve-user-changes`
- `validate-before-sync`
- `regenerate-from-canonical-source`
- `merge-with-redaction`
- `verify-symlink-target`
- `document-experimental-state`

**Step 3: Run focused validation**

Run:

```bash
uv run pytest tests/test_distribution_metadata.py::test_repo_sync_inventory_covers_sync_manifest_paths -v
```

Expected result: pass after inventory and drift ledger align.

---

## Task 5: Add Harness Fixture Support Schema

**Files:**

- Create: `config/schemas/harness-fixture-support.schema.json`

**Step 1: Write schema**

Required top-level fields:

- `version`
- `harness_registry_ref`
- `support_tiers_ref`
- `records`

Required record fields:

- `harness_id`
- `owner_change`
- `current_support_tier`
- `fixture_status`
- `fixture_classes`
- `validation_commands`
- `rollback_coverage`
- `promotion_blocker`

Enums:

- `fixture_status`: `fixture-backed`, `fixture-plan-only`, `docs-ledger-required`, `blocked`
- `rollback_coverage`: `present`, `planned`, `not-applicable`, `blocked`

**Step 2: Do not validate yet**

The manifest is added in Task 6.

---

## Task 6: Add Harness Fixture Support Manifest

**Files:**

- Create: `planning/manifests/harness-fixture-support.json`

**Step 1: Add one record per harness ID**

Required harness IDs from `config/harness-surface-registry.json`:

- `claude-code`
- `claude-desktop`
- `chatgpt`
- `codex`
- `github-copilot-web`
- `github-copilot-cli`
- `opencode`
- `gemini-cli`
- `antigravity`
- `cursor-editor`
- `cursor-agent-web`
- `cursor-agent-cli`
- `perplexity-desktop`
- `cherry-studio`
- `crush`

**Step 2: Preserve current tiers**

Every record must copy `current_support_tier` from the harness registry. Do not promote any record to `validated` in this plan.

**Step 3: Fixture status guidance**

Use these statuses:

- `fixture-plan-only` for repo-present surfaces with planned but not yet executable fixtures.
- `docs-ledger-required` for blind-spot surfaces requiring first-party docs before local fixture claims.
- `blocked` only if the surface is unsafe or impossible to validate without user credentials.

Recommended mapping:

- `claude-code`: `fixture-plan-only`
- `claude-desktop`: `fixture-plan-only`
- `chatgpt`: `docs-ledger-required`
- `codex`: `fixture-plan-only`
- `github-copilot-web`: `fixture-plan-only`
- `github-copilot-cli`: `fixture-plan-only`
- `opencode`: `fixture-plan-only`
- `gemini-cli`: `fixture-plan-only`
- `antigravity`: `docs-ledger-required`
- `cursor-editor`: `fixture-plan-only`
- `cursor-agent-web`: `docs-ledger-required`
- `cursor-agent-cli`: `docs-ledger-required`
- `perplexity-desktop`: `docs-ledger-required`
- `cherry-studio`: `fixture-plan-only`
- `crush`: `fixture-plan-only`

**Step 4: Fixture class guidance**

Use classes that match each harness registry `validation_requirements`, for example:

- `plugin-fixture`
- `skills-fixture`
- `mcp-fixture`
- `global-config-merge-fixture`
- `secret-redaction-fixture`
- `rollback-fixture`
- `docs-ledger-fixture`
- `model-neutral-policy-fixture`
- `credential-guard-fixture`
- `no-fabricated-installed-skill-inventory-fixture`

**Step 5: Promotion blocker guidance**

Every non-validated record must state the blocker plainly, for example:

- `Requires executable fixture artifacts and rollback verification before validated support claims.`
- `Requires first-party docs ledger and local config discovery before support claims.`
- `Requires proof that installed-skill inventory is discovered, not inferred from generated instructions.`

**Step 6: Run focused validation**

Run:

```bash
uv run pytest tests/test_distribution_metadata.py::test_harness_fixture_support_covers_every_harness_without_tier_promotion -v
```

Expected result: pass.

---

## Task 7: Add Repo-Sync Narrative Doc

**Files:**

- Create: `planning/00-overview/12-repo-sync-and-drift-ledger.md`

**Step 1: Document purpose**

Include sections:

- `Purpose`
- `Inputs`
- `Inventory Rules`
- `Drift Ledger Rules`
- `Secret Handling`
- `Promotion Path`
- `Validation Commands`

**Step 2: Keep docs concise**

Do not duplicate every JSON record in prose. Describe the classification rules and point to the manifests.

**Step 3: Run OpenSpec validation**

Run:

```bash
uv run wagents openspec validate
```

Expected result: pass.

---

## Task 8: Mark Child And Parent Tasks Complete

**Files:**

- Modify: `openspec/changes/agents-c00-repo-sync/tasks.md`
- Modify: `openspec/changes/agents-platform-overhaul/tasks.md`

**Step 1: Mark child tasks complete**

In `openspec/changes/agents-c00-repo-sync/tasks.md`, check off all five tasks after artifacts and validation exist.

**Step 2: Mark parent tasks complete**

In `openspec/changes/agents-platform-overhaul/tasks.md`, check off:

- `Create non-Markdown repo-sync inventory and drift ledger.`
- `Add fixture-backed support tiers for each harness variant.`

Leave this unchecked unless the user explicitly approves a selective commit:

- `Commit foundation changes.`

**Step 3: Run OpenSpec status**

Run:

```bash
uv run wagents openspec instructions apply --change agents-platform-overhaul --format json
```

Expected result: `27/28` tasks complete, one remaining commit task.

---

## Task 9: Full Validation

**Files:**

- No new edits unless validation exposes a real issue.

**Step 1: Run focused tests**

```bash
uv run pytest tests/test_distribution_metadata.py -v
```

Expected result: pass.

**Step 2: Run lint for touched test file**

```bash
uv run ruff check tests/test_distribution_metadata.py
```

Expected result: pass.

**Step 3: Run OpenSpec validation**

```bash
uv run wagents openspec validate
```

Expected result: pass.

**Step 4: Run asset validation**

```bash
uv run wagents validate
```

Expected result: pass.

**Step 5: Run README freshness check**

```bash
uv run wagents readme --check
```

Expected result: pass.

---

## Task 10: Optional Selective Commit

**Files:**

- Stage only files created or modified by this plan.

**Step 1: Review dirty worktree**

Run:

```bash
git status --short
```

Expected result: many unrelated dirty files may still be present. Do not stage them.

**Step 2: Stage only overhaul foundation files**

Stage only:

```bash
git add planning/manifests/repo-sync-inventory.json \
  planning/manifests/repo-drift-ledger.json \
  planning/manifests/harness-fixture-support.json \
  config/schemas/repo-sync-inventory.schema.json \
  config/schemas/repo-drift-ledger.schema.json \
  config/schemas/harness-fixture-support.schema.json \
  planning/00-overview/12-repo-sync-and-drift-ledger.md \
  tests/test_distribution_metadata.py \
  openspec/changes/agents-c00-repo-sync/tasks.md \
  openspec/changes/agents-platform-overhaul/tasks.md
```

If `config/sync-manifest.json` is modified to include new schemas, include it only after confirming the diff is limited to these registry entries.

**Step 3: Commit if approved**

Run:

```bash
git commit -m "feat: add agents platform sync ledgers"
```

**Step 4: Mark commit task complete only after commit succeeds**

After commit success, mark `Commit foundation changes.` complete and run:

```bash
uv run wagents openspec instructions apply --change agents-platform-overhaul --format json
```

Expected result: `28/28` tasks complete.

---

## Risks And Mitigations

- **Risk:** Accidentally overstating support by calling a planned fixture `validated`.
  **Mitigation:** Preserve current `support_tier` values and require promotion blockers for every non-validated harness.

- **Risk:** Reading secret-bearing live config while building the drift ledger.
  **Mitigation:** Use only path-level metadata from `config/sync-manifest.json`; classify live configs as `path-only`, `redacted`, or `unknown`.

- **Risk:** Staging unrelated dirty worktree files.
  **Mitigation:** Use explicit `git add` paths only, and only if the user approves a commit.

- **Risk:** Duplicating sync manifest logic in a stale ledger.
  **Mitigation:** Tests assert every sync manifest path is covered by inventory and drift ledger records.

- **Risk:** Generated docs drift.
  **Mitigation:** Avoid generated docs in this plan; run `uv run wagents readme --check` and leave docs generation to `docs-steward` after implementation if needed.

## Approval Questions

1. Should implementation stop at `27/28` tasks complete, leaving commit for later?
2. Should `config/sync-manifest.json` include the new schemas/manifests as canonical managed paths, or should they remain covered only by tests for now?
3. Should `harness-fixture-support.json` live in `planning/manifests/` as implementation evidence, or in `config/` as a canonical registry?
4. Should the repo-sync inventory enumerate all current `config/sync-manifest.json` paths exactly, or also include planned future harness surfaces that are not yet in sync manifest?
