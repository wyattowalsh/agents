---
title: Developer Commands Refresh Capture W29
tags:
  - kb
  - raw
  - commands
aliases:
  - Developer commands refresh 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave29-pass5-2026-06-25
---

# Developer Commands Refresh Capture W29

Additive command anchors added during passes 3–5 (2026-06-25).

```bash
uv run wagents doctor --format json
uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning
uv run python skills/nerdbot/scripts/kb_inventory.py --root kb
uv run wagents grok doctor --format json
uv run pytest tests/test_platform_adapters.py -q
```

## KB maintenance loop

1. Ingest capture → update source-map / coverage
2. Enrich wiki topic
3. `kb_lint.py --fail-on warning`
4. Activity log entry + commit (kb/ only)

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Doctor JSON | wave 27 capture | tool output |
| KB lint | `skills/nerdbot/scripts/kb_lint.py` | canonical repo |