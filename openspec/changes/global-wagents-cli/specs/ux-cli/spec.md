# ux-cli Delta

## ADDED Requirements

### Requirement: Global wagents Discovers Repository Root At Runtime

The `wagents` CLI SHALL resolve the agents repository root at runtime for global installs (`uv tool install`) and editable checkouts, using `WAGENTS_REPO_ROOT`, `--repo-root`, cwd walk, and package-parent fallback.

#### Scenario: Global binary resolves repo assets

- **WHEN** `wagents` is invoked from outside a clone via a global install
- **THEN** it discovers the agents repository root before reading `skills/`, `config/`, or `scripts/`
- **AND** `wagents self doctor` reports the resolved root and install mode.

#### Scenario: Contributor uses editable checkout

- **WHEN** `uv run wagents` executes inside the repository
- **THEN** repo discovery SHALL prefer the checkout root without requiring `WAGENTS_REPO_ROOT`.
