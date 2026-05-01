---
title: Skill Authoring And Validation
tags:
  - kb
  - skills
  - validation
aliases:
  - Skill authoring
  - Skill validation
kind: concept
status: active
updated: 2026-05-01
source_count: 11
---

# Skill Authoring And Validation

## Skill Shape

Repository skills use YAML frontmatter followed by a Markdown body. The minimum required fields are `name` and `description`. Skill names are kebab-case, limited by repo rules, and must match the directory name under `skills/`.

Optional frontmatter supports license, compatibility, allowed tools, metadata, argument hints, model/context options, user invocation controls, and hooks. The repo also distinguishes auto-invoked convention skills from user-invocable workflow skills.

## Lifecycle Commands

| Need | Command |
|------|---------|
| Create a skill | `uv run wagents new skill <name>` |
| Validate all assets | `uv run wagents validate` |
| Audit skill quality | `uv run python skills/skill-creator/scripts/audit.py --all --format table` |
| Package all skills dry-run | `uv run wagents package --all --dry-run` |
| Regenerate README | `uv run wagents readme` |
| Generate docs | `uv run wagents docs generate` |
| Sync installed skills dry-run | `uv run wagents skills sync --dry-run` |

## Documentation Implications

Skill descriptions feed README and generated docs surfaces. When skill definitions change, validate assets and refresh generated docs/readme checks according to the affected surface.

## Validation Boundaries

`uv run wagents validate` checks the asset definition contract, but packaging and docs checks catch stricter portability and generated-surface issues. Use [[validation-and-test-coverage]] before treating a validation pass as release readiness, and use `uv run wagents package <name> --dry-run` or `uv run wagents package --all --dry-run` for package-specific checks.

Skill eval coverage should also be read against skill risk. Use [[skill-catalog-risk-and-eval-coverage]] when deciding whether a skill's evals are adequate for browser, network, credential, destructive, or external-system workflows.

## Related Pages

- [[agent-asset-model]]
- [[developer-commands]]
- [[wagents-cli-and-automation]]
- [[validation-and-test-coverage]]
- [[agent-frontmatter-dialects]]
- [[openspec-workflow]]
- [[harness-and-platform-sync]]
- [[skill-catalog-risk-and-eval-coverage]]

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| Skill frontmatter requires `name` and `description`. | `kb/raw/sources/agents-md.md` | raw source note | Derived from `AGENTS.md`. |
| `wagents validate` validates all skills and agents. | `kb/raw/sources/pyproject-and-makefile.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Derived from Makefile and README. |
| README and docs pages are generated public surfaces. | `kb/raw/sources/openspec-config.md` | raw source note | Derived from OpenSpec config. |
| The repo currently lists 55 skills. | `kb/raw/sources/readme.md`; `kb/raw/sources/code-surface-inventory.md` | raw source notes | README badge/table plus inventory. |
| Validation and packaging have different enforcement scopes. | `kb/raw/sources/asset-validation-coverage.md`; `kb/raw/sources/tests-and-validation.md` | raw source notes | Important release-readiness distinction. |
| `wagents` exposes validation, docs, packaging, install/sync, OpenSpec, hooks, and eval command families. | `kb/raw/sources/wagents-internals.md` | raw source note | CLI implementation source. |
| Upstream agent-skill docs are contextual and do not supersede repo-local frontmatter requirements. | `kb/raw/sources/external-agent-skill-docs.md` | external source note | External context only. |
| Eval presence should be interpreted relative to skill risk. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | Risk-adjusted coverage model. |
