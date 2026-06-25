---
title: Security Quarantine Register Capture W24
tags:
  - kb
  - raw
  - security
aliases:
  - Quarantine register 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave24-pass4-2026-06-25
---

# Security Quarantine Register Capture W24

Pointer to `planning/manifests/security-quarantine-register.json` on 2026-06-25.

## Role

Hard-quarantine blocklist enforced by `uv run wagents validate` for curated external skill sources and catalog rows. Complements `support-tier-registry.json` **quarantine** tier (security-lane approval required).

## Validation coupling

- `wagents validate` includes quarantine policy checks on authoring sources.
- Catalog SSOT: `docs/public/generated-registries/skills-catalog-index.json` (Bucket A).

## KB implication

Do not promote quarantined skill IDs into install-now catalog status without explicit security review evidence.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Manifest path | `AGENTS.md` §2.7; `planning/manifests/` | canonical repo |
| Risk page | `kb/wiki/topics/skill-catalog-risk-and-eval-coverage.md` | wiki synthesis |