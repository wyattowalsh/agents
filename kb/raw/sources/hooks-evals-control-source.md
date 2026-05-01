---
title: Hooks Evals Control Plane
tags:
  - kb
  - source
  - hooks
  - evals
aliases:
  - Hooks evals source
  - Control plane source
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# Hooks Evals Control Plane

## Source Record

| Field | Value |
|-------|-------|
| source_id | `hooks-evals-control-plane` |
| original_location | `config/hook-registry.json`; `hooks/wagents-hook.py`; `scripts/sync_agent_stack.py`; `wagents/cli.py`; `wagents/parsing.py`; `tests/test_hooks_cli.py`; `tests/test_wagents_hook.py`; `tests/test_sync_agent_stack.py`; `tests/test_eval_cli.py`; selected `skills/*/evals/evals.json` manifests |
| raw_path | `kb/raw/sources/hooks-evals-control-source.md` |
| capture_method | repo-local pointer summary from read-only research |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | repo-local source and tests; no secrets captured |
| intended_wiki_coverage | [[hooks-evals-control-plane]], [[validation-and-test-coverage]], [[wagents-cli-and-automation]], [[harness-and-platform-sync]] |

## Summary

Hooks and evals form a repo-local agent control plane. The portable hook registry describes hook IDs, events, matchers, commands, timeouts, harness support, and research-mode behavior. Runtime hook code enforces research-state behavior, read-only write denial, dangerous shell blocking, evidence-ledger capture, and stop verification.

Eval manifests are the parallel regression and acceptance surface for skills. `wagents eval list`, `validate`, and `coverage` scan skill eval manifests, validate shape, and report skill coverage. The current KB previously mentioned these surfaces in validation pages, but did not have a dedicated synthesis page for how hooks and evals work together.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| The portable hook registry defines hook events, commands, harness support, timeouts, and research-specific behavior. | `config/hook-registry.json` | canonical config | Registry source. |
| Research hook runtime code enforces read-only and dangerous-command policies during research workflows. | `hooks/wagents-hook.py`; `skills/research/SKILL.md`; `skills/research/scripts/verify.py` | canonical implementation | Runtime behavior requires command execution for live proof. |
| Hook projection is centralized through sync logic that maps hooks into harness-specific formats. | `scripts/sync_agent_stack.py`; `tests/test_sync_agent_stack.py` | implementation and tests | Supports harness sync claims. |
| `wagents hooks` and `wagents eval` are first-class CLI surfaces. | `wagents/cli.py`; `wagents/parsing.py` | implementation | Covers list/validate/coverage flows. |
| Hook and eval behavior has targeted pytest coverage. | `tests/test_hooks_cli.py`; `tests/test_wagents_hook.py`; `tests/test_eval_cli.py` | tests | Static evidence only; full suite not run in this batch. |
| Selected skills already use eval manifests for regression coverage. | `skills/skill-creator/evals/evals.json`; `skills/agent-runtime-governance/evals/evals.json` | skill eval manifests | Representative examples. |
