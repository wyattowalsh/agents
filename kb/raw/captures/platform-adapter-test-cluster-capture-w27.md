---
title: Platform Adapter Test Cluster Capture W27
tags:
  - kb
  - raw
  - tests
aliases:
  - Platform adapter tests 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave27-pass5-2026-06-25
---

# Platform Adapter Test Cluster Capture W27

Validation commands recurring in harness fixture records on 2026-06-25.

## Common pytest invocations

```bash
uv run pytest tests/test_platform_adapters.py -q
uv run pytest tests/test_harness_rollback_fixtures.py -q
uv run pytest tests/test_distribution_metadata.py -q
uv run wagents validate
```

## Harnesses citing adapter tests

From `harness-fixture-support.json`: claude-code, codex, grok-build, opencode (executable fixture class) among others.

## Adapter LOC baseline (w08)

Nine adapters ~3004 LOC; native: grok, opencode, codex; thin/delegator surfaces for others.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Validation commands | `planning/manifests/harness-fixture-support.json` | canonical repo |
| Adapter fleet | `kb/raw/captures/platform-adapters-fleet-capture-w08.md` | raw capture |