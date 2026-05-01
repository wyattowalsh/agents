# experimental-harnesses Specification

## Purpose
Define experimental harness requirements and caveats for lower-confidence platforms such as Perplexity Desktop, Cherry Studio, and Crush.
## Requirements
### Requirement: Experimental harness caveats

The experimental harness lane SHALL mark unsupported or unverified surfaces without overstating support.

#### Scenario: Experimental path exists

- **GIVEN** a harness directory exists but lacks validation fixtures
- **WHEN** support tiers are generated
- **THEN** the harness is marked `experimental` or `repo-present-validation-required` rather than `validated`.
