---
title: Config Transaction Registry Capture W03
tags:
  - kb
  - raw
  - sync
  - safety
aliases:
  - Config transaction registry capture 2026-06-25
kind: source-summary
status: active
updated: 2026-06-25
source_count: 1
journal_ref: kb-wave03-config-2026-06-25
---

# Config Transaction Registry Capture W03

Read-only snapshot of `config/config-transaction-registry.json` on 2026-06-25.

## Surface modes

| Mode | Meaning |
|------|---------|
| `canonical` | Repo-owned source file; edit through normal review |
| `generated` | Derived output; regenerate from canonical sources |
| `merged` | Live/global user config; preview, backup, redaction, explicit approval, apply, rollback |
| `symlink` | Pointer to canonical repo source; verify target |
| `symlinked-entries` | Directory with repo-managed symlinks; preserve unrelated user entries |

## Global config rules (merged surfaces)

1. Never mutate live global config during planning or dry-run.
2. Before apply: preview with secrets/private tokens redacted.
3. Before apply: backup snapshot outside generated repo outputs.
4. After apply: targeted validation or smoke check for touched harness.
5. Rollback restores pre-apply snapshot without touching unrelated user-owned entries.

## Redaction rules

- Never print secret values from `.env` or global app configs.
- Credential references render as env var names or deterministic fingerprints only.
- Redact auth tokens, cookies, API keys, OAuth refresh tokens, private keys, browser profile secrets.
- Treat desktop app configs as sensitive even when JSON.

## Fixture classes (test contract vocabulary)

`preview`, `idempotent-rerun`, `global-merge`, `rollback`, `redaction`, `generated-source-trace`, `no-fabricated-skill-claim`

## Implementation gap (cross-registry)

Registry policy is richer than current monolithic sync coverage. Partially implemented today:

| Control | Status |
|---------|--------|
| Dry/check (`apply=False`) | implemented |
| Config-drop refusal (`ConfigDropError`) | implemented |
| Merge preservation (MCP/hooks/config tables) | implemented |
| Symlink `.bak` backup | implemented (limited paths) |
| Full merged-home snapshot restore | not proven end-to-end |

See `kb/raw/captures/sync-rollback-capture-w01.md` for pytest rollback inventory (8 cases).

## Provenance

| Claim | Source | Type |
|-------|--------|------|
| Transaction modes and rules | `config/config-transaction-registry.json` | canonical repo path |
| Sync manifest surface typing | `config/sync-manifest.json` | canonical repo path |
| Adapter merge behavior | `wagents/platforms/*`, `scripts/sync_agent_stack.py` | canonical repo path |