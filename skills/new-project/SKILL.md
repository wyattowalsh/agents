---
name: new-project
description: >-
  Initialize projects with safe, preference-driven scaffolds, docs, AI
  instructions, quality gates, GitHub setup, and design baselines. Use when
  starting a repo or non-destructively adding conventions. NOT for product
  features, agents, MCP servers, cloud provisioning, or destructive migrations.
argument-hint: "<plan|init|bootstrap|audit|repair|prefs|preset|docs|ai|github|doctor> [name|path]"
model: opus
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# New Project

Plan and safely bootstrap modern software projects from typed presets and capability preferences.

## Dispatch

| `$ARGUMENTS`                                | Action                                                                        |
| ------------------------------------------- | ----------------------------------------------------------------------------- |
| Empty                                       | Gallery: show modes, presets, preference categories, examples; do not edit    |
| `prefs`, `prefs list`, `catalog`            | Preferences: list capability categories and defaults                          |
| `prefs validate`                            | Preferences: validate capability and preset catalogs                          |
| `prefs add <id>`                            | Preferences: explain the safe preference addition workflow                    |
| `preset list`                               | Presets: show curated presets and tradeoffs                                   |
| `plan <name-or-path>`                       | Plan: read-only blueprint for a new or existing target                        |
| `init <name>`, `new <name>`                 | Init: new target setup after preflight, blueprint, and approval               |
| `bootstrap <path>`, `init-existing <path>`  | Bootstrap Existing: non-destructive missing-file setup                        |
| `audit <path>`                              | Audit: read-only scaffold and convention health report                        |
| `repair <path>`                             | Repair: approved additive repair based on audit findings                      |
| `doctor <path>`                             | Doctor: validate toolchain/config health without changing files               |
| `docs <path>`                               | Docs: classify docs-lite, docs-themed, docs-interactive, or docs-product      |
| `docs-lite <path>`, `starlight <path>`      | Docs Lite: Astro Starlight static docs profile                                |
| `docs-themed <path>`                        | Docs Themed: Starlight plus CSS/Tailwind brand layer                          |
| `docs-interactive <path>`                   | Docs Interactive: Starlight plus React islands                                |
| `docs-product <path>`, `fumadocs <path>`    | Docs Product: Next.js plus Fumadocs advanced docs profile                     |
| `ai <path>`, `agents <path>`                | AI Instructions: AGENTS, nested AGENTS, Claude Code, OpenCode, Codex planning |
| `github <path>`                             | GitHub: CI, templates, release workflow planning                              |
| `python <name>`, `uv <name>`                | Init/Plan: Python-focused preset                                              |
| `node <name>`, `web <name>`, `next <name>`  | Init/Plan: Node/web preset                                                    |
| `data <name>`                               | Init/Plan: Supabase, SQLite, DuckDB, notebooks preset                         |
| `aws <name>`, `agentcore <name>`            | Plan: Bedrock/AgentCore planning; provider mutation is opt-in                 |
| `monorepo <name>`, `nx <name>`              | Init/Plan: monorepo preset                                                    |
| `full <name>`, `max-free <name>`            | Plan: comprehensive blueprint; apply module-by-module only                    |
| Natural language new repo/bootstrap request | Auto-classify, then ask only high-impact missing questions                    |
| Product feature request                     | Refuse or redirect to implementation skills                                   |
| Agent or MCP server request                 | Refuse or redirect to `agent-conventions` or `mcp-creator`                    |
| Destructive or force request                | Stop, explain risk, require file-by-file approval                             |

## Operating Flow

1. Classify the request as new project, existing repo bootstrap, audit, repair, preferences, docs, AI instructions, GitHub, cloud/data, or refusal.
2. Read `references/intake-and-routing.md` for ambiguous or natural-language requests.
3. Run read-only preflight before any mutating mode.
4. Resolve presets and capabilities from `data/`, not from ad hoc prose.
5. Produce a blueprint with files, commands, skipped existing files, risks, approvals, and validation.
6. Apply only after explicit approval, one module at a time.
7. Run validation and summarize created, skipped, and deferred work.

## Pattern Implementation

### Classification-Gating

Classify every request before acting: new project, existing bootstrap, audit, repair, preferences, docs, AI instructions, GitHub, cloud/data, or refusal. Ambiguous requests stay read-only until the missing choice is resolved.

### Progressive-Disclosure

Keep `SKILL.md` as the routing contract. Load references for domain detail, data files for preferences, scripts for deterministic checks, and templates only for report rendering.

### Scaling-Strategy

Add future stacks as capabilities and presets first. Change the dispatch table only when a new top-level mode is needed.

## Canonical Vocabulary

Use these canonical terms exactly.

| Term                 | Meaning                                                                             |
| -------------------- | ----------------------------------------------------------------------------------- |
| Preset               | Curated setup bundle, such as `minimal`, `python-api`, `docs-lite`, or `monorepo`   |
| Capability           | Atomic setup feature, such as `python.uv`, `docs.starlight`, or `github.actions-ci` |
| Blueprint            | Read-only project setup plan with files, commands, risks, approvals, and checks     |
| Apply step           | One approved mutation unit from a blueprint                                         |
| External side effect | Cloud, deploy, release, DNS, account, or provider mutation                          |

## Reference File Index

| File                                         | Purpose                                                   | Read When                |
| -------------------------------------------- | --------------------------------------------------------- | ------------------------ |
| `references/workflow.md`                     | End-to-end safe setup flow                                | Mutating modes           |
| `references/capability-model.md`             | Capability schema and conflict semantics                  | Preference/catalog work  |
| `references/presets.md`                      | Presets and tradeoffs                                     | Preset selection         |
| `references/preference-catalog.md`           | Human-readable preference list                            | `prefs`, planning        |
| `references/adding-preferences.md`           | Future preference extension workflow                      | `prefs add`, maintenance |
| `references/intake-and-routing.md`           | Classification and ambiguity handling                     | Natural language inputs  |
| `references/scaffold-profiles.md`            | Artifact matrices by preset                               | Blueprinting             |
| `references/python-uv.md`                    | uv, uvx, pyproject, Python packages                       | Python profiles          |
| `references/node-pnpm-npm.md`                | pnpm, npm/npx, TypeScript, Next, Astro, Nx, Changesets    | Node profiles            |
| `references/docs-starlight-react.md`         | Starlight docs-lite/themed/interactive guidance           | Docs light modes         |
| `references/docs-fumadocs.md`                | Fumadocs docs-product guidance                            | Docs product mode        |
| `references/design-system.md`                | DESIGN.md and anti-slop design guidance                   | Web/docs/design profiles |
| `references/data-platforms.md`               | Supabase, SQLite, DuckDB, Kaggle, Colab                   | Data/notebook profiles   |
| `references/ai-apps.md`                      | Pydantic AI, LangGraph, Vercel AI SDK, Bedrock, AgentCore | AI app profiles          |
| `references/github-ci-release.md`            | Actions, releases, least-privilege CI                     | GitHub mode              |
| `references/cloud-deploy-dns.md`             | Vercel, Cloudflare DNS, AWS deploy gates                  | Cloud modes              |
| `references/precommit-quality-gates.md`      | pre-commit and CI mirroring                               | Quality gates            |
| `references/conventional-commits-release.md` | Conventional Commits, Changesets, releases                | Release profile          |
| `references/ai-agent-instructions.md`        | AGENTS, nested AGENTS, Claude Code, OpenCode, Codex       | AI instruction mode      |
| `references/openspec-governance.md`          | OpenSpec setup and generated artifact policy              | OpenSpec profile         |
| `references/security-supply-chain.md`        | Secrets, package generators, Docker, CI, supply chain     | Risky modes              |
| `references/validation-and-repair.md`        | Audit, doctor, repair workflow                            | Audit/repair/doctor      |
| `references/artifact-templates.md`           | Skeletons and template guidance                           | Artifact generation      |

## Script Index

| Script                        | Purpose                                                              |
| ----------------------------- | -------------------------------------------------------------------- |
| `scripts/preferences.py`      | List, validate, resolve, merge, and explain preferences              |
| `scripts/preflight.py`        | Read-only project detection and risk flags                           |
| `scripts/blueprint.py`        | Build a JSON blueprint from request, preset, and capabilities        |
| `scripts/validate_catalog.py` | Validate schemas, dependencies, conflicts, templates, and references |
| `scripts/validate_plan.py`    | Validate blueprint safety before apply                               |
| `scripts/version_check.py`    | Query package/version facts for selected packages                    |
| `scripts/doctor.py`           | Verify existing scaffold health without mutations                    |
| `scripts/render_report.py`    | Render report data for HTML templates                                |

Scripts use `argparse`, JSON stdout, diagnostics on stderr, and `--help`. They must not read secret files.

## Safety Gates

1. Preflight first for scaffold, bootstrap, repair, docs, AI, GitHub, cloud, or apply modes.
2. Blueprint before mutation or package install.
3. Skip existing files by default; overwrite requires file-by-file approval.
4. Preserve detected package managers unless migration is approved.
5. Never ask users to paste secrets into chat, and never read secret files.
6. Generate `.env.example` or `.env.template`, not real credentials.
7. Cloud, deploy, release, DNS, Docker, and account mutations require explicit provider-specific approval.
8. GitHub Actions default to `permissions: contents: read`; add only narrow permissions.
9. Docker Compose templates must avoid privileged mode, host networking, Docker socket mounts, broad host mounts, root services, and public DB binds by default.
10. Generated AI instructions must not bypass approvals, disable credential guards, auto-deploy, or ignore higher-priority instructions.

## Critical Rules

1. Use the capability catalog for stack selection; do not hardcode preferences only in prose.
2. Distinguish `uvx` one-off tools from `uv run` project commands.
3. Prefer `pnpm` for new Node projects, but preserve detected npm/yarn/bun unless migration is approved.
4. Prefer Starlight for lightweight docs; use Fumadocs only when product/API/docs-heavy requirements justify it.
5. Make Tailwind v4 and shadcn/ui opt-in outside web/product profiles; add only needed shadcn components.
6. Never claim `latest` without live registry or official-doc evidence gathered during the run.
7. Do not create agents or MCP servers; redirect those requests.
8. Do not create branches, worktrees, commits, pushes, releases, or PRs unless explicitly requested.
9. Mirror local quality gates in GitHub Actions or document why CI was deferred.
10. Include mobile-first responsive UI requirements in web/docs/design profiles.
11. Update evals when dispatch modes, presets, capabilities, or safety gates change.
12. Keep this body under 500 lines; move details to references.

## Validation Contract

Before declaring changes to this skill complete, run:

```bash
python skills/new-project/scripts/check.py
uv run pytest tests/test_new_project.py
uv run python skills/new-project/scripts/preflight.py --path . --format json
```

After changing skill definitions, public descriptions, references, or eval behavior, invoke `docs-steward` if available.
