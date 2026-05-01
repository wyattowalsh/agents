---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Skills Ecosystem Plan

## Objective

Make Agent Skills the default reusable capability artifact.

## External sources to curate

- agentskills.io specification
- skills.sh and `npx skills`
- GitHub Awesome Copilot skills
- OpenAI skills
- Trail of Bits skills
- Supabase, HashiCorp, inference.sh, PactFlow, and other domain skill packs

## Curation fields

```yaml
id: string
source_url: string
source_family: agentskills|skills_sh|github|vendor|internal
license: string
maintainer: string
trust_tier: internal|official|verified_maintainer|community|unknown
support_tier: first_class|validated|curated_review|experimental|watchlist|unsupported
preferred_install: npx skills|copy|manual
cli_robustness:
  has_json_output: bool
  has_help: bool
  idempotent: bool
  deterministic: bool
security:
  executes_code: bool
  needs_network: bool
  needs_secrets: bool
```

## OpenSpec-related internal skills

- `openspec-planner`
- `openspec-design-reviewer`
- `openspec-task-graph-builder`
- `openspec-archivist`
- `spec-delta-reviewer`
