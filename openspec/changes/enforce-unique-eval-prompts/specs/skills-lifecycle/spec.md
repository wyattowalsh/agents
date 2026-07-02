## ADDED Requirements

### Requirement: Canonical eval prompts are unique

Canonical skill eval manifests SHALL reject repeated prompt text within a single
manifest after trimming surrounding whitespace.

#### Scenario: Duplicate canonical prompt is rejected

- **GIVEN** `skills/<name>/evals/evals.json` contains two cases whose `prompt`
  values are equal after trimming surrounding whitespace
- **WHEN** `wagents eval validate` runs
- **THEN** validation SHALL fail
- **AND** the error SHALL identify the later eval and the earlier eval that used
  the same prompt.

#### Scenario: Distinct canonical prompts are accepted

- **GIVEN** `skills/<name>/evals/evals.json` contains non-empty and unique
  `prompt` values
- **WHEN** `wagents eval validate` runs
- **THEN** validation SHALL continue to validate the manifest using the existing
  `skill_name`, `prompt`, and `expected_output` rules.
