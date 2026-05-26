# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Generated docs and instruction truth

The docs/instructions lane SHALL consolidate README, docs, support matrices, and AI instructions from registries and fragments after schema freeze. The canonical instruction source SHALL define safety, precedence, trust-boundary, git, and generated-surface ownership rules that downstream platform mirrors inherit through repo-managed generation rather than manual edits.

#### Scenario: Canonical instructions change

- **GIVEN** `instructions/global.md` changes shared cross-platform policy
- **WHEN** repo-managed instruction sync runs
- **THEN** generated Codex and Copilot instruction mirrors SHALL inherit the canonical policy
- **AND** stale local includes that do not resolve to tracked source files SHALL NOT remain in generated instruction output.

#### Scenario: Platform overlays narrow shared policy

- **GIVEN** a platform-specific instruction overlay adds runtime guidance
- **WHEN** the overlay concerns safety, secrets, approvals, destructive actions, or git operations
- **THEN** the overlay SHALL NOT weaken canonical safety guidance unless the active user explicitly requests that outcome.

#### Scenario: Secret-guard bypass guidance is documented

- **GIVEN** a platform-specific secret guard supports an environment-variable bypass
- **WHEN** instructions document legitimate bypass usage
- **THEN** the instructions SHALL scope the bypass to a specific command or short-lived shell
- **AND** the instructions SHALL NOT recommend adding the bypass to shell profiles, repo config, or committed files.
