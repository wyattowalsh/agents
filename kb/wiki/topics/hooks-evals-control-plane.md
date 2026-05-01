---
title: Hooks Evals Control Plane
tags:
  - kb
  - hooks
  - evals
aliases:
  - Hooks and evals
  - Agent control plane
kind: concept
status: active
updated: 2026-05-01
source_count: 1
---

# Hooks Evals Control Plane

## Scope

This page maps hooks and evals as repository control-plane surfaces. It does not claim live harness hook projection or eval execution passed during this KB batch.

## Summary

Hooks are runtime and projection controls: the registry names hook events and commands, runtime code enforces research-mode behavior, and sync code projects hooks into harness formats. Evals are regression controls: skill eval manifests and `wagents eval` commands validate skill behavior and coverage.

Use this page with [[validation-and-test-coverage]] when a workflow changes hook behavior, research write guards, skill eval manifests, or sync projection behavior. Static source coverage is strong, but live harness behavior still requires targeted command execution and tests.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Hook registry, runtime hook code, sync projection, CLI parsing, tests, and selected eval manifests form an agent control plane. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Dedicated source note. |
| Hooks enforce runtime policy while evals provide regression and acceptance checks. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Synthesis of repo-local code and tests. |
| Live harness behavior is not proven by static source inspection. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Verification gap. |

## Related

- [[validation-and-test-coverage]]
- [[wagents-cli-and-automation]]
- [[harness-and-platform-sync]]
- [[skill-catalog-risk-and-eval-coverage]]
