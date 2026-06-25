---
title: OpenCode Harness Policy Capture W18
tags:
  - kb
  - raw
  - opencode
aliases:
  - OpenCode policy 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave18-pass2-stop-2026-06-25
---

# OpenCode Harness Policy Capture W18

Metadata capture from `opencode.json` and `instructions/opencode-global.md` on 2026-06-25. Complements [[opencode-runtime-policy]].

## Repo-managed defaults

| Area | Policy |
|------|--------|
| Root model | `openai/gpt-5.5` |
| Small model | `openai/gpt-4-mini` class per repo sync |
| Plugins | npm specs pinned to `@latest` dist-tag |
| DCP | `config/opencode-dcp.jsonc` canonical |
| Ensemble | `config/opencode-ensemble.json` |

## Adapter

`wagents/platforms/opencode.py` (~849 LOC) — largest native adapter; merges JSON + satellite configs.

## Pass 2 stop note

Final pass-2 diminishing-returns capture (1 net-new). Waves 17–18 consecutive `<3` closes second gap sweep.

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Config keys | `opencode.json` | canonical repo |
| Runtime overlay | `instructions/opencode-global.md` | canonical repo |
| Prior adapter | `kb/raw/captures/opencode-platform-adapter-capture-w08.md` | raw capture |