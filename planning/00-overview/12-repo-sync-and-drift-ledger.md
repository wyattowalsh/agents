# Repo Sync Inventory And Drift Ledger

## Purpose

The repo-sync inventory and drift ledger make harness synchronization auditable before any apply step mutates user-level configuration. They record which paths are repo-owned, generated, merged into live config, symlinked, or experimental, and they define the validation evidence required before support claims move beyond planning tiers.

## Inputs

- `config/sync-manifest.json` is the canonical list of managed repo and live harness paths.
- `planning/manifests/repo-sync-inventory.json` classifies each managed path by ownership, mode, location class, source tier, drift policy, validation evidence, and secret-handling posture.
- `planning/manifests/repo-drift-ledger.json` records the observed drift state and next action for every inventory path.
- `planning/manifests/harness-fixture-support.json` records fixture evidence requirements for every harness surface in `config/harness-surface-registry.json`.

## Inventory Rules

- `canonical` paths are source-of-truth repo files or directories.
- `generated` paths must be regenerated from canonical repo inputs rather than edited directly.
- `merged` paths are live user or application config surfaces and require redacted merge handling.
- `symlink` and `symlinked-entries` paths must be verified as links to repo-managed content before support claims.
- Home and application-support paths are represented by path metadata only; their values are not read into planning artifacts.

## Drift Ledger Rules

- Repo files can be `tracked-clean`, `tracked-dirty`, `untracked`, or `not-checked`.
- User and application-support paths are `external-live` unless an approved harness audit verifies them more precisely.
- Generated or merged surfaces with possible credentials are high-risk until redaction and rollback fixtures exist.
- Existing dirty worktree changes must be preserved; staging must use explicit file paths only.

## Secret Handling

- `not-secret-bearing` means the path is expected to contain only public repo metadata or instructions.
- `path-only` means planning artifacts may name the path but must not inspect or copy values.
- `redacted` means downstream merge tooling must redact values in output and logs.
- `unknown` means the surface needs a harness-specific audit before automated handling.

## Harness Coverage

The fixture support manifest covers Claude Desktop, Claude Code, ChatGPT, Codex, GitHub Copilot Web, GitHub Copilot CLI, OpenCode, Gemini CLI, Antigravity, Perplexity Desktop, Cherry Studio, Cursor Editor, Cursor Agent Web, Cursor Agent CLI, and the repo-present Crush surface.

No harness is promoted to `validated` by this foundation pass. Surfaces with repo evidence remain `repo-present-validation-required`; blind-spot surfaces remain `planned-research-backed` or `experimental` until first-party docs and executable fixtures prove behavior.

## Promotion Path

To promote a harness surface, a child lane must add executable fixture evidence for its advertised projection surfaces, rollback coverage, and validation commands. The parent support tier must not be raised until tests prove the fixture record and support registry agree.

## Validation Commands

Run these before marking foundation tasks complete:

```bash
uv run pytest tests/test_distribution_metadata.py
uv run ruff check tests/test_distribution_metadata.py
uv run wagents openspec validate
uv run wagents validate
uv run wagents readme --check
```
