# security-quarantine Specification

## Purpose
Define quarantine requirements for untrusted, external, or security-sensitive agent assets before they can be promoted into supported repository workflows.
## Requirements
### Requirement: Security quarantine

The security quarantine lane SHALL block default installation or promotion for auth-bridging, proxying, credential-sharing, offensive-security, and unresolved provenance-risk assets.

#### Scenario: Auth-bridging repo is discovered

- **GIVEN** an external repo reuses or proxies credentials
- **WHEN** intake classifies it
- **THEN** it is marked `quarantine` until explicit security review and exception approval.
