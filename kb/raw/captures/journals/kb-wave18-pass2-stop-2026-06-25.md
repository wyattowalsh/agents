---
title: "Research journal — KB wave 18"
tags:
  - kb
  - raw
  - journal
  - provenance
aliases:
  - "KB wave 18 journal"
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave18-pass2-stop-2026-06-25
original_location: "~/.grok/research/kb-wave18-pass2-stop-2026-06-25.md"
---

# Research journal — KB wave 18

- **Goal:** `goals/kb-research-ingest/goal.md`
- **Wave:** 18 | Theme: pass 2 stop OpenCode harness policy topic
- **Captured:** 2026-06-25
- **Commit message:** `feat(kb): wave 18 — pass 2 stop OpenCode harness policy topic`

## G0 brief

New [[opencode-harness-policy]] topic; **pass 2 stop** — waves 17–18 consecutive `<3` net-new.

## Ownership map

| Role | Artifact | Path |
|------|----------|------|
| worker | `opencode-harness-policy-capture-w18` | `kb/raw/captures/opencode-harness-policy-capture-w18.md` |

## Ingest queue

- `raw`: added 1 capture (`opencode-harness-policy-capture-w18`).

## Capture evidence (excerpts)

### `opencode-harness-policy-capture-w18`

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


## Key findings

Derived from command-backed captures above; canonical repo files remain authoritative.

## Metrics

**net-new raw sources: 1**; pages enriched: 2; lint: pass (exit 0).

## Gate status

- G1 research: complete (read-only repo paths / external pointers)
- G2 ingest: captures written under `kb/raw/`
- G3 enrich: wiki/index updates per wave manifest
- G4 audit: `uv run python skills/nerdbot/scripts/kb_lint.py --root kb --fail-on warning` exit 0 before wave commit
