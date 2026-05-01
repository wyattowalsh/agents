# Design

## Decision

Complete the registry-core lane as the shared schema and vocabulary layer for the platform overhaul. The lane freezes the support tiers and points downstream work at canonical schema files for harnesses, skills, MCP servers, plugins/extensions, docs artifacts, external repositories, and support-tier records.

## Rationale

Later waves need consistent names for support state, projection ownership, and validation evidence. Centralizing those contracts prevents each lane from inventing incompatible fields or silently promoting unsupported surfaces.

## Implementation Notes

- Registry schemas live under `config/schemas/` and are the canonical contract for structured planning manifests.
- `planning/20-harness-registry/01-harness-projection-contract.md` documents projection surfaces, support-tier meaning, fixture requirements, and blind-spot policy.
- The accepted support tiers are `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, and `quarantine`.

## Risks

- Schema names overlap with downstream implementation lanes, so this pass records ownership without applying generated projections.
- Blind-spot surfaces must remain unverified until first-party docs and executable fixtures prove behavior.
- Registry contracts can block later promotion work if downstream lanes do not keep their manifests aligned.
