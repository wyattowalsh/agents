## Architecture

`new-project` is a project initialization planner and orchestrator, not a monolithic generator. `SKILL.md` remains a compact dispatch and safety contract. Project setup detail lives in typed data, references, scripts, and templates.

## Core Concepts

| Concept    | Definition                                                                                                           |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| Preset     | Curated project setup bundle such as `minimal`, `python-api`, `docs-lite`, `docs-product`, `monorepo`, or `max-free` |
| Capability | Atomic setup feature such as `python.uv`, `docs.starlight`, `data.duckdb`, or `github.actions-ci`                    |
| Blueprint  | Read-only plan containing selected capabilities, files, commands, risks, approvals, and validation                   |
| Apply step | Approved mutation unit that can be performed after blueprint review                                                  |

## Data Model

Capabilities include stable IDs, categories, dependencies, conflicts, implied capabilities, risk level, external side-effect flags, command templates, artifacts, validation checks, handoff skills, and docs sources. Presets reference capability IDs and must validate against the capability graph.

## Safety Model

All mutating modes follow preflight, blueprint, approval, apply, post-step diff/check, and validation. Existing files are skipped by default. Cloud, deploy, release, Docker, package install, and external account mutations require explicit opt-in. Secret files are never read and real secrets are never requested or generated.

## Docs Model

Starlight is the lightweight docs default. The docs profiles are split into `docs-lite`, `docs-themed`, `docs-interactive`, and `docs-product`. Fumadocs is an advanced product/API docs option, not the generic default. Tailwind v4 and shadcn/ui are opt-in outside web/product profiles.

## Extensibility Model

Future preferences are added by editing catalog data first, then presets, references only as needed, and evals for new routing/safety behavior. `SKILL.md` should rarely change for a new stack preference.

## Reuse Of Existing Skills

The skill routes or hands off specialized work instead of replacing existing skills: docs maintenance to `docs-steward`, feature UI work to `frontend-designer`, agent creation to `agent-conventions`, MCP creation to `mcp-creator`, cloud implementation to Cloudflare/Wrangler/infrastructure skills, and schema design to database skills.
