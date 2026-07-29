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
- Freeze the current derived graph of 65 runtime artifacts, 1,266 promoted
  selectors, and 7,596 selector-to-harness bindings (the current exact
  six-target set for each selector); change a count only when a new audited
  source artifact changes the authoritative manifests, and always recompute
  rather than copying a prior constant.
- Replace path/config/dry-run completion with semantic use, failure and denial
  paths, fresh-process discovery, rollback, reinstall, and final installed state.
- Treat `already_present` as discovery-only. Require a distinct,
  content-addressed five-phase receipt chain for every selector-to-harness
  binding, tied to the exact selector, harness, current input digest, and
  installed-content digest.
- Derive required capabilities from current portable catalog/sync metadata and
  compute untested capabilities as `required - proved`; never hardcode an empty
  untested set.
- Activate audited MCP and plugin surfaces through canary-first transactions.
- Reproduce every enabled plugin from its pinned upstream Git tree object, apply
  an explicit projection, and bind the approved marketplace, isolated install,
  and live cache to one immutable content digest.
- Accept rollback evidence only when an immutable `commit-pending` journal is
  followed by a post-CAS passed marker that binds the exact artifact set and
  receipt-store transaction.
- Add exact auth, platform, quarantine, attribution, and docs closure receipts.
- Require trusted harness-issued session/task provenance for live independent
  review when such an issuer exists. If none exists, keep source validation
  available but report live review closure as `BLOCKED-EXTERNAL`.
- Preserve RV-002 as source-closed: enabled registry state, generated/live
  presence and identity equality, and authenticated reachability/denial
  regressions remain proof gates rather than new implementation work.
- Block candidate behavioral receipt regeneration until ordinary CLI/plugin
  timeout paths pass the process-group cleanup contract.
- Preserve the dirty worktree with compare-and-swap preimages and one writer.

## Non-Goals

- No branch, worktree, stash, reset, clean, commit, or push.
- No secret values in tracked files or receipts.
- No unlawful, abusive, destructive, or production-side-effect fixture.
- No claim of full usability while any artifact, selector, binding, capability,
  credential, platform, review finding, or rollback proof remains unresolved.
- No claim of DSSE, SLSA, or in-toto compliance and no invented PKI merely to
  satisfy review-provenance fields.
