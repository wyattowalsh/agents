# Security Quarantine Delta

## MODIFIED Requirements

### Requirement: Security quarantine

The security quarantine lane SHALL block default installation or promotion for auth-bridging, proxying, credential-sharing, offensive-security, and unresolved provenance-risk assets.

#### Scenario: Auth-bridging repo is discovered

- **GIVEN** an external repo reuses or proxies credentials
- **WHEN** intake classifies it
- **THEN** it is marked `quarantine` until explicit security review and exception approval.

#### Scenario: Quarantine register is validated

- **WHEN** repo validation reads `planning/manifests/security-quarantine-register.json`
- **THEN** each external repo record trigger SHALL match one of the declared `quarantine_triggers`
- **AND** each external repo record SHALL include a non-blank trigger
- **AND** invalid register JSON SHALL be reported as a validation error without a traceback
- **AND** hard-quarantined sources SHALL remain blocked from curated external catalog rows and legacy curated projections.
