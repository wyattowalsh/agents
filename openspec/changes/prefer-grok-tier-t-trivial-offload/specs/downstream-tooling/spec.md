## MODIFIED Requirements

### Requirement: Grok Delegate Requires Preflight And Ledger Accounting

`grok-delegate` SHALL require machine-readable preflight, default Tier-T use for eligible trivial leaves, and explicit session accounting before synthesis or dependent waves proceed.

#### Scenario: Tier-T eligible leaf is available

- **WHEN** a parent decomposes work and finds one bounded leaf task
- **AND** the leaf requires no more than three file reads or one file edit of no more than 80 LOC
- **AND** fast preflight reports `ok: true`
- **AND** bundled preflight reports `grok-auth-expiry` as `ok`
- **THEN** the parent SHALL default that leaf to `/grok-delegate trivial` using single-node native `grok -p`
- **AND** the parent SHALL retain synthesis and verification responsibility.

#### Scenario: Tier-T ineligible work is requested

- **WHEN** the candidate work is a multi-node graph, has overlapping writers, is broad implementation work, reads secrets, performs destructive actions, targets production, or includes `git push`
- **THEN** the parent SHALL NOT use Tier-T trivial offload
- **AND** it SHALL choose local execution, normal Grok waves, or another orchestration pattern that fits the task boundaries.

#### Scenario: Tier-T native dispatch fails

- **WHEN** the first native Tier-T `grok -p` dispatch fails in a parent work item
- **THEN** the parent SHALL record or report the Grok failure
- **AND** it SHALL stop using Tier-T for that parent work item
- **AND** it SHALL continue locally when the task can still proceed.
