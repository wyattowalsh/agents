---
title: Wagents Self Doctor Capture W27
tags:
  - kb
  - raw
  - wagents
aliases:
  - Wagents self doctor 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave27-pass5-2026-06-25
---

# Wagents Self Doctor Capture W27

`wagents self` sub-app doctor surface on 2026-06-25.

## Bundle install path

From `agent-bundle.json`:

```bash
uv tool install wagents --from git+https://github.com/wyattowalsh/agents
wagents self doctor
```

## Distinction

| Command | Scope |
|---------|-------|
| `wagents doctor` | Repo toolchain + docs deps + local discovery |
| `wagents self doctor` | Installed wagents package / entrypoint health |
| `wagents grok doctor` | Grok Build config + env flags |
| `wagents openspec doctor` | OpenSpec package + telemetry posture |

## Env

`WAGENTS_REPO_ROOT` — optional when not running inside clone (per bundle adapters.wagents-cli).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Install doctor | `agent-bundle.json` | canonical repo |
| Typer nesting | `kb/raw/captures/wagents-typer-map-capture-w20.md` | raw capture |