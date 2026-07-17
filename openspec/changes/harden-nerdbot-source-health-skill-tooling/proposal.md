# Summary

Harden the current Nerdbot implementation, the `source-url-health` MCP, and the
repo-owned Skill Creator packaging/eval tooling after reconciling the July 2026
audit against the live dirty worktree.

# Problem

The focused tests and focused type checks are green, but they do not prove all
runtime and distribution contracts:

- `source-url-health` passes a `verify` keyword to `httpx.Client.request`, even
  though the supported HTTPX API configures verification on the client; its
  wheel also omits the sibling SSRF module and the client inherits proxy-related
  environment variables.
- Skill archives can follow symlinks, build a manifest before all vendored
  members are known, and write the final ZIP non-atomically.
- Nerdbot writes its replay journal and human activity log as independent
  appends, so an interrupted operation can leave their projections divergent.
- Nerdbot's aggregate eval manifest and per-case projection files are both
  counted by the CLI, doubling its reported case count.
- The dirty Nerdbot metadata lowers the skill version from the committed
  `1.0.0`, and its dry-run archive includes repo-local `AGENTS.md` guidance with
  package-invalid relative links.

Earlier hook diagnostics for source-health test doubles, docs generation, and
repo projection drift are not assumed open: the live focused Ty check, docs
generation check, and repo projection check currently pass and remain regression
gates.

# Proposed Change

- Make the source-health transport use supported client-level TLS/environment
  configuration, enforce URL/address/redirect/deadline policy at every hop, and
  ship a self-contained wheel.
- Make skill archive collection no-follow, regular-file-only, bounded,
  deterministic, manifest-complete, and atomically published.
- Introduce explicit canonical-eval/projection metadata so Nerdbot's logical
  cases are counted once while legacy skills remain unchanged.
- Make the operation journal the canonical append-only audit record and the
  activity log an idempotently repairable projection under an operation lock.
- Restore monotonic Nerdbot versioning and exclude repo-local instruction files
  from portable archives.
- Add adversarial tests first, then update source, bundled toolkit projections,
  docs, and generated surfaces only after source writers are quiescent.

# Non-Goals

- No live installs, `wagents skills sync --apply`, production URL probes,
  credentialed actions, commits, pushes, branch changes, or worktrees.
- No global rewrite of legacy eval layouts.
- No cryptographic journal chain, resolver subprocess, or compatibility alias
  unless a deterministic failing test proves the simpler contract insufficient.
- No hand edits to generated docs, catalogs, indexes, or lock files.

