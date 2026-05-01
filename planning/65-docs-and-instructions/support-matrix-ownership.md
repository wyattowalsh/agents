# Support Matrix Ownership

## Source Inputs

- `config/support-tier-registry.json` defines allowed tier vocabulary.
- `config/harness-surface-registry.json` defines harness IDs and surface splits.
- `planning/manifests/harness-fixture-support.json` records fixture status without promoting support tiers.
- Child lane manifests provide evidence for lane-specific support claims.

## Surface Split Requirement

Support matrices must distinguish:

- desktop app surfaces
- web/cloud surfaces
- CLI surfaces
- editor-integrated surfaces
- experimental or manually configured surfaces

Examples that must not be collapsed:

- Claude Code vs Claude Desktop
- ChatGPT vs Codex
- GitHub Copilot Web vs GitHub Copilot CLI
- Cursor Editor vs Cursor cloud/agent surfaces
- OpenCode CLI/TUI/plugin surfaces vs unrelated editor surfaces

## Ownership Rules

- C01 owns support-tier vocabulary and registry schema.
- C04 harness lanes own harness-specific evidence fragments.
- C08 owns generated support matrix assembly and wording.
- Unsupported, unverified, experimental, and quarantine states must be rendered explicitly rather than omitted.

## Promotion Rule

A docs support matrix may not show a higher tier than the backing registry entry. Fixture manifests can support evidence but cannot promote support tiers on their own.
