## ADDED Requirements

### Requirement: External repos remain discovery inputs

The external repo intake lane SHALL create source, license, security, provenance, and conformance-review tasks without installing or promoting external assets by default.

#### Scenario: External repo is marked adopt-candidate

- **GIVEN** an external repo has initial action `adopt-candidates`
- **WHEN** intake runs
- **THEN** it remains uninstalled until all promotion gates pass.
