# CI / Evals / Observability Delta

## MODIFIED Requirements

### Requirement: Conformance gates

The CI/evals/observability lane SHALL define validation gates for registries,
skills, MCP smoke fixtures, adapter fixtures, docs truth, AI instructions,
OpenSpec changes, package artifacts, and release-readiness cleanup evidence.

#### Scenario: Public-release readiness loop

- **GIVEN** a maintainer requests public-release readiness
- **WHEN** local gates, generated docs, package checks, sync previews, and
  public-surface scans run
- **THEN** every gate exits zero
- **AND** stderr and parsed command output contain no unclassified warnings,
  failures, invalid items, deprecations, skips, public local paths, or secret
  markers
- **AND** validation-created caches, build outputs, and ignored files are
  cleaned or classified before the next full run
- **AND** release readiness is not claimed until two consecutive full matrix
  passes are clean after cleanup.
