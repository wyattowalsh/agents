---
title: Known Risks Refresh Capture W28
tags:
  - kb
  - raw
  - risks
aliases:
  - Known risks refresh 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave28-pass5-2026-06-25
---

# Known Risks Refresh Capture W28

Open gaps reaffirmed on 2026-06-25 after passes 3–4 (not fixed in KB).

| Gap | Evidence |
|-----|----------|
| MCP docs badge 15 vs registry 33 | docs-artifact truth rules; mcp-registry w03 |
| agent-bundle agents/ wording vs 9 live files | agent-bundle-snapshot w23 |
| validate_codex_config.py not in CI | scripts-and-validation-tooling |
| 189 legacy eval JSON vs manifest semantics | skill-eval-files w05 |
| pnpm-version doctor warn | wagents-doctor-checks w27 |

## Provenance

Consolidation capture — points to prior wave evidence without new canonical edits.