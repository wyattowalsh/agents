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
updated: 2026-06-25
source_count: 4
---

# Hooks Evals Control Plane

## Scope

This page maps hooks and evals as repository control-plane surfaces. It does not claim live harness hook projection or eval execution passed during this KB batch.

## Summary

Hooks are runtime and projection controls: the registry names hook events and commands, runtime code enforces research-mode behavior, and sync code projects hooks into harness formats. Evals are regression controls: skill eval manifests and `wagents eval` commands validate skill behavior and coverage.

Use this page with [[validation-and-test-coverage]] when a workflow changes hook behavior, research write guards, skill eval manifests, or sync projection behavior. Static source coverage is strong, but live harness behavior still requires targeted command execution and tests.

**2026-06-25 Wave 05 runtime inventory:** `hooks/` holds 11 executables (10 shell helpers + `wagents-hook.py` with **16** policy handlers). Portable `config/hook-registry.json` defines **22** registry entries; `wagents hooks list` reports **40** hooks (16 `settings.json`, 22 `registry:*`, 2 `skill:*`). **31** listed commands invoke `wagents-hook.py`—research policies (`research-evidence-ledger`, `research-readonly-write-guard`, `research-dangerous-shell-guard`, `research-stop-verifier`, `research-prompt-triage-context`) appear 3× each across harness dialects; Codex/Cursor guards and truth gates fill the remainder. `hooks validate` returns `ok: true` with 0 errors; `KNOWN_HOOK_EVENTS` count is **21** per `test_hooks_cli.py`.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Hook registry, runtime hook code, sync projection, CLI parsing, tests, and selected eval manifests form an agent control plane. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Dedicated source note. |
| Hooks enforce runtime policy while evals provide regression and acceptance checks. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Synthesis of repo-local code and tests. |
| Live harness behavior is not proven by static source inspection. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Verification gap. |
| `wagents eval` exposes list/validate/coverage/adequacy; 56/56 skills with evals, 791 cases, adequacy strict 0 failing. | `kb/raw/captures/wagents-eval-cli-capture-w02.md` | raw capture | 2026-06-25 JSON captures. |
| `wagents hooks list` reports 40 hooks; `hooks validate` delegates to `validate_hooks.py`. | `kb/raw/captures/wagents-eval-cli-capture-w02.md` | raw capture | Distinct from `wagents validate` repo gate. |
| 16 `wagents-hook.py` policies; 22 registry entries; 31 hook.py invocations in list. | `kb/raw/captures/hooks-runtime-inventory-capture-w05.md` | raw capture | Wave 05 hooks runtime inventory. |
| 106-test hooks/eval pytest cluster; `test_wagents_hook.py` covers policy shapes. | `kb/raw/captures/hooks-tests-cluster-capture-w05.md` | raw capture | Wave 05 test cluster map. |

## Related

- [[validation-and-test-coverage]]
- [[wagents-cli-and-automation]]
- [[harness-and-platform-sync]]
- [[skill-catalog-risk-and-eval-coverage]]
