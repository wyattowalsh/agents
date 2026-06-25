---
title: OpenCode Harness Policy
tags:
  - kb
  - opencode
  - harness
aliases:
  - OpenCode harness policy summary
kind: concept
status: active
updated: 2026-06-25
source_count: 3
---

# OpenCode Harness Policy

## Summary

OpenCode is the largest native platform adapter (~849 LOC). Repo policy keeps models in `opencode.json` (not agent frontmatter), npm plugins on `@latest`, and DCP/Ensemble in separate canonical config files. Runtime-specific agent keys live in `instructions/opencode-agents-overlay.md`.

## Key surfaces

| Surface | Role |
|---------|------|
| `opencode.json` | Repo-managed runtime plugins and model defaults |
| `config/opencode-dcp.jsonc` | Dynamic Context Pruning canonical source |
| `config/opencode-ensemble.json` | Team orchestration plugin config |
| `instructions/opencode-global.md` | Platform overlay |
| `wagents/platforms/opencode.py` | Merge/sync adapter |

## Constraints

- Strip transient provider blocks on sync (vercel/opencode-go/kimi-for-coding).
- Session poisoning recovery may require DB quarantine — see [[opencode-runtime-policy]].
- Chrome DevTools may use OpenCode-specific launcher override for sign-in flows.

## Provenance

| Claim | Source |
|-------|--------|
| Wave 18 capture | `kb/raw/captures/opencode-harness-policy-capture-w18.md` |
| Runtime detail | [[opencode-runtime-policy]] |
| Adapter evidence | `kb/raw/captures/opencode-platform-adapter-capture-w08.md` |

## Related

- [[harness-and-platform-sync]]
- [[canonical-generated-surfaces]]
- [[plugin-and-mcp-ownership]]