# Awesome List Harvest Model

## Objective

Systematically mine curated lists without polluting the repo with low-quality candidates.

## Candidate sources

- Awesome GitHub Copilot skills and agents.
- Awesome Agent Skills.
- Awesome MCP and MCP server lists.
- Awesome LLM, Awesome AI Agents, Awesome Agent Frameworks.
- Awesome LLM Security / prompt injection / AI appsec lists.
- Awesome OpenTelemetry / observability lists.
- Awesome Policy-as-Code / supply chain lists.
- DevTools AI / AI IDE lists.

## Extraction schema

```yaml
candidate:
  id: string
  source_list: url
  repo_url: url
  category: skill|mcp|plugin|framework|eval|observability|security|policy|ui
  maintainer: string|null
  license: string|null
  stars: int|null
  last_commit: date|null
  maturity: experimental|beta|stable|production-proven|unknown
  integration_path: skill|mcp|plugin|cli-wrapper|docs-only|reject
  security_notes: []
  overlap_with_existing_repo: []
  recommended_action: adopt|adapt|watch|reject|replace-mcp|docs-only
```

## Quality thresholds

- Direct repository URL required.
- License required before adoption.
- Recent activity preferred unless project is stable and low-change.
- Must be testable in CI or explicitly docs-only.
- Must have clear install path.
- Must not require broad secrets or filesystem access by default.

## Review principle

Awesome lists are curation accelerators, not trust authorities. Every candidate needs direct upstream review.
