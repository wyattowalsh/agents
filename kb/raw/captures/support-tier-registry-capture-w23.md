---
title: Support Tier Registry Capture W23
tags:
  - kb
  - raw
  - config
aliases:
  - Support tier registry 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave23-pass4-2026-06-25
---

# Support Tier Registry Capture W23

Read-only snapshot of `config/support-tier-registry.json` on 2026-06-25.

## Tier vocabulary (7)

| Tier ID | docs_label | promotion_allowed |
|---------|------------|-------------------|
| validated | Validated | true |
| repo-present-validation-required | Repo-present, validation required | false |
| planned-research-backed | Planned, research-backed | false |
| experimental | Experimental | false |
| unverified | Unverified | false |
| unsupported | Unsupported | false |
| quarantine | Quarantine | false |

## Rules (4)

1. Validated requires fixture evidence + rollback coverage.
2. Experimental/planned must not appear as supported in generated install commands.
3. Quarantine requires security-lane approval before promotion.
4. Generated docs must preserve exact tier vocabulary.

## Downstream consumers

- `planning/manifests/harness-fixture-support.json`
- `config/harness-surface-registry.json`
- `wagents/docs.py` harness-support page generation

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Tier table | `config/support-tier-registry.json` | canonical repo |