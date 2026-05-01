# skill-registry-intake Specification

## Purpose
Define intake requirements for skill registry entries, including provenance, support tier, validation, and promotion evidence.
## Requirements
### Requirement: Skill registry intake safety

The skill registry intake lane SHALL evaluate official and community skill registries as discovery inputs and require trust metadata before promotion.

#### Scenario: Community registry is discovered

- **GIVEN** a community skill registry is listed in research
- **WHEN** intake classifies it
- **THEN** no skills are installed without source, license, security, and fixture review.
