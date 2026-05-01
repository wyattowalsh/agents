---
title: Canonical Generated Surfaces
tags:
  - kb
  - sync
  - generated
aliases:
  - Canonical surfaces
kind: concept
status: active
updated: 2026-05-01
source_count: 4
---

# Canonical Generated Surfaces

## Scope

This page explains how to reason about source-of-truth files versus derived or merged harness surfaces.

## Summary

The repo root is the bundle root. Source authority is concentrated in `AGENTS.md`, `instructions/global.md`, `skills/`, `agents/`, `config/`, `agent-bundle.json`, `openspec/`, and implementation code. Generated or projected surfaces include README/docs outputs, platform instruction mirrors, plugin manifests, and harness config projections.

`config/sync-manifest.json` is the current ledger for canonical, generated, merged, symlink, and symlinked-entry surfaces. A known tension remains around `opencode.json`: repo instructions describe it as a canonical repo source for project-level OpenCode config, while some sync/manifests classify it as generated. Treat that as an unresolved source-of-truth gap until reconciled.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The repo root is the bundle root and should not duplicate asset directories into plugin folders. | `kb/raw/sources/agents-md.md`; `kb/raw/sources/agent-bundle-and-sync.md` | raw source notes | Existing repo policy. |
| `sync-manifest.json` tracks surface roles. | `kb/raw/sources/config-registries-and-sync.md` | raw source note | Ledger for generated/merged/symlinked surfaces. |
| `opencode.json` has canonical/generated classification tension. | `kb/raw/sources/config-registries-and-sync.md`; `kb/raw/sources/opencode-policy-and-runtime-plugins.md` | raw source notes | Open gap. |

## Related

- [[harness-and-platform-sync]]
- [[docs-generation-and-site]]
- [[known-risks-and-open-gaps]]
