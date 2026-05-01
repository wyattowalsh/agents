# Catalog Browser

## Objective

Provide a unified browser for skills, plugins, MCPs, and harness projections.

## Capability card fields

- id.
- type: skill/plugin/MCP/instruction/OpenAPI.
- title.
- description.
- source.
- support tier.
- compatible harnesses.
- install method.
- trust signals.
- risk tags.
- version/ref.
- validation status.
- docs link.
- action buttons: preview install, inspect, audit, enable, disable, rollback.

## Filtering

- by harness;
- by type;
- by risk;
- by install method;
- by source trust;
- by validation status;
- by skill-vs-MCP replacement potential.

## Acceptance criteria

- CLI and dashboard share the same catalog source.
- No capability can be installed without showing source/trust/risk metadata.
