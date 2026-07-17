# Change: Activate The July 2026 Candidate Corpus Runtime

## Why

The historical intake change accounts for 293 raw entries and 289 normalized
targets, but its completion model accepts disabled MCP servers, disabled plugins,
path/config presence, dry-run harness inventory, and non-install reference rows.
Those conditions do not satisfy the operator's request that every relevant
skill, agent, instruction, CLI, library, MCP server, plugin, hook, and service be
installed, configured, and usable across applicable local harnesses.

## What Changes

- Reopen every source, selector, runtime artifact, and harness binding under a
  fail-closed executable receipt model.
- Discover at least the 64 known runtime artifacts and 1,306 selector floor;
  increase either count when exact source inspection finds more assets.
- Replace path/config/dry-run completion with semantic use, failure and denial
  paths, fresh-process discovery, rollback, reinstall, and final installed state.
- Activate audited MCP and plugin surfaces through canary-first transactions.
- Add exact auth, platform, quarantine, attribution, and docs closure receipts.
- Preserve the dirty worktree with compare-and-swap preimages and one writer.

## Non-Goals

- No branch, worktree, stash, reset, clean, commit, or push.
- No secret values in tracked files or receipts.
- No unlawful, abusive, destructive, or production-side-effect fixture.
- No claim of full usability while any artifact, selector, binding, capability,
  credential, platform, review finding, or rollback proof remains unresolved.
