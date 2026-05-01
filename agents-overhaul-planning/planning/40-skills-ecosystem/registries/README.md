---
status: planning
owner: skill-registry-team
last_updated: 2026-05-01
---

# Skill Registry Design

## Objective

Create a canonical skill registry that can render install guidance, support badges, OpenSpec references, and harness projections.

## Registry fields

```yaml
id: string
name: string
source_type: internal|external|vendor|community
source_url: string
license: string
support_tier: first_class|validated|curated_review|experimental|watchlist
trust_tier: official|vendor|curated|community|unknown
install_surface: npx-skills|copy|git-submodule|manual
preferred_harnesses: []
unsupported_harnesses: []
requires_mcp: false
requires_network: false
requires_secrets: false
version: string
checksum: string
openspec_requirements: []
ci_fixtures: []
security_notes: string
```

## Rules

- Internal skills must be validated before docs generation.
- External skills enter `curated_review` before `validated`.
- Any skill that shells out must document commands, inputs, outputs, and exit-code behavior.
- Skill docs must include a “why not MCP?” or “requires MCP companion” note when relevant.
