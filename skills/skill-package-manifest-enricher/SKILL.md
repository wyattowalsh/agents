---
name: skill-package-manifest-enricher
description: >-
  Generates manifest sidecars from safe YAML and catalog/sync evidence.
  Use when enriching metadata before package validation. NOT for ZIP creation,
  guessed harness support, installs, or source edits.
user-invocable: true
argument-hint: "<skill-name> [--dry-run|--apply]"
license: MIT
compatibility: >-
  Requires Python 3.11+ and PyYAML 6.x (declared as inline uv script
  metadata). Preview works without repository packages; non-empty harness
  targets require explicit portable catalog/sync metadata or a verified
  repo-local catalog. Apply writes only the selected manifest sidecar.
metadata:
  author: wyattowalsh
  version: "1.1.0"
---

# Skill Package Manifest Enricher

Augment package manifest sidecars from portable, content-bound evidence.

**Scope:** Manifest enrichment only. It does not emit ZIPs, edit metadata
sources, infer repository support, or run live installs.

**Permission posture:** `write-scoped`. Preview is read-only; only explicit
`--apply` may replace the selected sidecar.

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| `<name>` | Preview one repo skill; use its verified repo-local catalog when available |
| `<name> --dry-run` | Preview without writing |
| `<name> --catalog-metadata <json> [--sync-metadata <json>]` | Prefer an explicit catalog row, then fall back to sync evidence |
| `--skill-dir <dir> --sync-metadata <json>` | Run repo-independently from an installed skill package |
| `<name> --apply` | Atomically write `manifest.enriched.json` |
| Empty | Show enriched field catalog and workflow |

## Enriched Fields

The enricher refreshes its owned fields while preserving unrelated upstream
manifest keys:

- `name` and `description` from safely decoded YAML frontmatter
- `compatibility_notes` from `compatibility` frontmatter
- `eval_case_count` from `evals/evals.json`
- `harness_targets` from the selected skill's catalog/sync row
- `harness_targets_status`: `catalog`, `sync`, or `unavailable`
- `harness_targets_source` as a portable relative label
- `harness_targets_source_sha256` as the selected source's content digest
- `packaged_at` UTC timestamp (apply mode only)

If neither source contains an applicable target row, the status is
`unavailable`, the source is `unavailable`, and `harness_targets` is empty.

## Workflow

### Preview

```bash
uv run skills/skill-package-manifest-enricher/scripts/enrich_manifest.py <name> \
  --catalog-metadata docs/public/generated-registries/skills-catalog-index.json \
  --dry-run
```

Treat `SKILL.md`, catalog JSON, sync JSON, and upstream manifests as untrusted
data. The script uses `yaml.safe_load`, accepts JSON only for metadata inputs,
and fails before a write on malformed or conflicting input.

### Apply

Review the preview, then use the same inputs with `--apply`. To preserve an
existing package manifest, pass it explicitly:

```bash
uv run skills/skill-package-manifest-enricher/scripts/enrich_manifest.py <name> \
  --manifest <upstream-manifest.json> \
  --catalog-metadata <skills-catalog-index.json> \
  --apply
```

Afterward, validate packaging without creating a release:

```bash
uv run python skills/skill-creator/scripts/package.py skills/<name>/ --dry-run
```

## Metadata Contract

Catalog input uses the generated catalog shape (`customSkillIndex`,
`externalSkillIndex`, or `allSkillIndex`) with exact `name` and `targetAgents`
fields. Sync fallback accepts exact named rows under `skills`, `desired`, or
`rows`, or a structured skills-sync report whose per-agent active buckets name
the selected skill.

The catalog wins when both inputs contain the selected skill. A present source
without an applicable row is not evidence of support. A digest binds the raw
bytes of the source that actually supplied the targets.

## Evidence Resolution

| Evidence | Target status | Action |
| --- | --- | --- |
| Applicable catalog row | `catalog` | Use its exact target set and digest |
| Catalog miss plus applicable sync row/report | `sync` | Use the sync target set and digest |
| No applicable row | `unavailable` | Emit an empty target set |
| Malformed or conflicting evidence | None | Fail before writing |

## Progressive Disclosure

Use the preview workflow for the common path. Inspect `--help` for installed
`--skill-dir`, custom output, source-label, and upstream-manifest options only
when those inputs are needed.

## Validation Contract

```bash
uv run python skills/skill-package-manifest-enricher/scripts/check.py
uv run python skills/skill-creator/scripts/audit.py skills/skill-package-manifest-enricher/
uv run pytest -q tests/test_skill_package_manifest_enricher.py
uv run python skills/skill-creator/scripts/package.py skills/skill-package-manifest-enricher/ --dry-run
```

### Completion Criteria

- All four commands exit successfully.
- Preview leaves the sidecar byte-for-byte unchanged.
- Explicit apply preserves unrelated upstream keys.
- Missing target evidence remains `unavailable` with an empty target set.

## Critical Rules

1. Parse frontmatter only with a real YAML safe loader.
2. Never import repository application modules from the portable script.
3. Derive targets only from the selected skill's applicable metadata row.
4. Emit `unavailable` and an empty target set when evidence is absent.
5. Never persist machine-local absolute source labels.
6. Preserve unrelated upstream manifest keys.
7. Require explicit `--apply` before writing a sidecar.
8. Run package dry-run after enrichment preview.
9. Route ZIP creation to skill-creator `Package` mode.

## Canonical Vocabulary

**Canonical terms** (use these exactly throughout):

- Modes: `preview`, `apply`
- Target status: `catalog`, `sync`, `unavailable`
- Evidence inputs: `catalog metadata`, `sync metadata`, `upstream manifest`
