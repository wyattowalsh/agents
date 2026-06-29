## MODIFIED Requirements

### Requirement: Grok Delegate Requires Preflight And Ledger Accounting

`grok-delegate` SHALL require machine-readable preflight and explicit session accounting before synthesis or dependent waves proceed.

#### Scenario: Grok delegation starts

- **WHEN** the parent prepares a Grok delegation wave
- **THEN** it SHALL run `bash skills/grok-delegate/scripts/preflight.sh` (bundled `doctor.py`; optional `--cwd <target>`)
- **AND** it SHALL stop or downshift the Grok lane when required checks fail, including `grok-auth-*` OAuth failures.

#### Scenario: OAuth auth is missing or policy fails

- **WHEN** bundled preflight reports `grok-auth-oauth` or `grok-auth-policy` as `fail`
- **THEN** the parent SHALL stop fleet dispatch
- **AND** it SHALL recommend `grok login` before retrying delegation.

#### Scenario: OAuth expiry check fails

- **WHEN** bundled preflight reports `grok-auth-expiry` as `fail` (expired, missing, or malformed `expires_at`)
- **THEN** the parent SHALL stop fleet dispatch and Tier-T offload
- **AND** it SHALL recommend `grok login` before retrying delegation.

#### Scenario: Tier-T trivial offload

- **WHEN** a parent considers offloading a bounded leaf task to Grok
- **THEN** it SHALL confirm fast preflight `ok` and `grok-auth-expiry` is `ok`
- **AND** it SHALL use single-node native `grok -p` via `/grok-delegate trivial`
- **AND** the parent SHALL retain synthesis responsibility.

#### Scenario: Delegated sessions complete

- **WHEN** a Grok delegation wave finishes
- **THEN** the parent SHALL record one terminal ledger row per delegated session before unblocking dependent work.

## ADDED Requirements

### Requirement: Grok Delegate Bundled Doctor Is Self-Contained

The `grok-delegate` skill bundled doctor SHALL operate without `wagents` or `uv run` dependencies.

#### Scenario: Preflight runs outside agents repo

- **WHEN** `bash skills/grok-delegate/scripts/preflight.sh` runs from a packaged skill tree
- **THEN** it SHALL invoke only `python3` and bundled `doctor.py`
- **AND** it SHALL emit machine-readable JSON with `ok`, `summary`, and `checks`.