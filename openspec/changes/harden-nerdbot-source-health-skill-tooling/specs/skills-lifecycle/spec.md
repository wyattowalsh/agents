# Skill archive and eval integrity

## ADDED Requirements

### Requirement: Closed-world portable archive

Skill packaging SHALL include only validated regular files rooted in the skill,
apply explicit resource limits, reject ambiguous archive names, compute the
manifest from the final member set, and publish the ZIP atomically and
deterministically. Windows reparse/device-name ambiguity, manifest metadata, and
the generated manifest bytes SHALL be subject to the same closed-world checks.

#### Scenario: Link escapes the skill root

- **GIVEN** a symlink, hard link, or special file appears below a skill root
- **WHEN** packaging runs
- **THEN** packaging fails without reading external content or publishing a partial archive

#### Scenario: Toolkit destination is redirected

- **GIVEN** a selected bundled toolkit destination is a symlink, junction, or reparse point
- **WHEN** toolkit reconciliation runs
- **THEN** reconciliation fails during all-target preflight before any destination is changed

### Requirement: Canonical eval ownership

A canonical eval manifest MAY explicitly own per-case projection files. The
collector SHALL count its logical cases once, and validation SHALL prove exact
closed-world projection parity without changing undeclared legacy layouts.

#### Scenario: Nerdbot aggregate plus projections

- **GIVEN** Nerdbot declares all per-case projections in its canonical manifest
- **WHEN** eval inventory runs
- **THEN** the reported count equals canonical logical cases, not canonical plus projections
- **AND** any malformed, behavior-drifted, or schema-extended projection remains visible rather than being suppressed
