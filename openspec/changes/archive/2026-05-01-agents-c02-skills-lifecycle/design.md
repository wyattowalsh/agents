# Design

## Decision

Complete the skills lifecycle lane as a planning and governance contract. The lane records inventory fields, execution risk classes, CLI conformance, provenance lock requirements, adoption gates, and validation fixtures without changing skill implementations.

## Rationale

The repo already contains local skills and external candidates, but promotion requires deterministic evidence. Keeping this pass in planning artifacts avoids conflicting with unrelated dirty skill files and preserves the parent rule that external sources stay discovery-only until reviewed.

## Implementation Notes

- `planning/40-skills-ecosystem/00-skills-lifecycle-control-plane.md` is the source contract for this pass.
- External repositories assigned to skills lifecycle remain candidates, not installs.
- Future code work may add schemas, lockfiles, and tests after the control-plane fields are accepted.

## Risks

- Skill implementation files are currently dirty from unrelated work, so this lane intentionally avoids editing `skills/`.
- Registry policy JSON ownership is shared with registry lanes and is not modified here.
