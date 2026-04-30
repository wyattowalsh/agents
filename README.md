<div align="center">
  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/docs/src/assets/brand/logo.webp" alt="Agents Logo" width="100" height="100">
  <h1>agents</h1>
  <p><b>Portable AI agent skills, MCP config, and shared instructions</b></p>
  <p>
    <a href="https://github.com/wyattowalsh/agents/actions/workflows/ci.yml"><img src="https://github.com/wyattowalsh/agents/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <a href="https://github.com/wyattowalsh/agents/blob/main/LICENSE"><img src="https://img.shields.io/github/license/wyattowalsh/agents?style=flat-square&color=5D6D7E" alt="License"></a>
    <a href="https://github.com/wyattowalsh/agents/releases"><img src="https://img.shields.io/github/v/release/wyattowalsh/agents?style=flat-square&color=2E86C1" alt="Release"></a>
    <a href="https://agents.w4w.dev/skills/"><img src="https://img.shields.io/badge/skills-48-0f766e?style=flat-square" alt="Skills"></a>
    <a href="https://agents.w4w.dev"><img src="https://img.shields.io/badge/docs-agents.w4w.dev-00b4d8?style=flat-square&logo=read-the-docs&logoColor=white" alt="Docs"></a>
  </p>
  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/docs/public/social-card.png" alt="Agents social preview" width="640">
</div>

---

## 🚀 Quick Start

Install all skills globally into your favorite agents:

```bash
npx skills add github:wyattowalsh/agents --all -y -g --agent antigravity --agent claude-code --agent codex --agent crush --agent cursor --agent gemini-cli --agent github-copilot --agent opencode
```

## 📦 Distribution

This repo is packaged as one cross-agent bundle with native plugin adapters and a skills CLI fallback:

| Target | Path | Update behavior |
| ------ | ---- | --------------- |
| Claude Code | `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` | Git-hosted plugin updates resolve from the latest commit because the plugin version is intentionally unpinned |
| Codex | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` | Codex can load the Git-backed plugin bundle and bundled skills from the repository root |
| Other agents | `npx skills add github:wyattowalsh/agents ...` | `wagents update` refreshes recorded sources, and `wagents skills sync` additively reconciles repo + curated external skills across harnesses |

## ✨ Why use this repository?

| 📦 **Portable** | 🧩 **Composable** | 🌐 **Open Source** |
| :--- | :--- | :--- |
| Use skills across Claude Code, Cursor, Copilot, and more. | Combine simple skills into complex, multi-agent workflows. | Extensible, readable, and community-driven. |

## 🧰 Skills

Reusable actions and knowledge bases for AI agents.

| Name | Description |
| ---- | ----------- |
| add-badges | Detect stack and generate shields.io README badges with icons, colors, live endpoints. Use when adding or updating badges. NOT for README writing, docs, or CI/CD setup. |
| agent-conventions | Agent definition conventions. Validate frontmatter, update indexes. Use when creating or modifying agents. NOT for skills, MCP servers, or CLAUDE.md. |
| agent-runtime-governance | Audit runtime controls for tool permissions, approvals, memory, telemetry, evals, rollout, and containment. Use when reviewing tool-bearing agent systems. NOT for security scans, prompt-only work, or static code review. |
| api-designer | Contract-first API design for REST, GraphQL, gRPC. Design, spec, review, version, compat, sdk. Use for API architecture and OpenAPI specs. NOT for MCP servers (mcp-creator) or frontend API calls. |
| changelog-writer | Generate changelogs, release notes, and migration guides from git history. Parse conventional commits. Use for releases. NOT for git ops (git-workflow) or doc sites (docs-steward). |
| data-pipeline-architect | Analyzes and designs batch and streaming data pipelines with contracts, lineage, reliability, and cost controls. Use for ingestion and transformation systems. NOT for ad-hoc analysis or schema design. |
| data-wizard | Analyze data and guide ML: EDA, model selection, feature engineering, stats, visualization, MLOps. Use for data work. NOT for ETL, database design (database-architect), or frontend viz code. |
| database-architect | Design schemas, plan migrations, and optimize queries. Six modes from modeling to evolution. Use for database architecture. NOT for DBA ops, backups, or deployment (devops-engineer). |
| devops-engineer | Design, optimize, and debug CI/CD pipelines. GitHub Actions and GitLab CI patterns. Use for pipeline work. NOT for infrastructure provisioning (infrastructure-coder) or app code. |
| discover-skills | Discover AI agent skills via gap analysis, registry search, and ideation. Use when expanding your collection systematically. NOT for creating skills (skill-creator) or ad-hoc search (find-skills). |
| docling-graph | Use when designing/reviewing Docling Graph knowledge-graph workflows: templates, contracts, CLI/API configs, inspect reports, exports, traces. NOT for generic Docling parsing, vector-only RAG, graph DB admin, or ontology-only work. |
| docs-steward | Maintain docs across Starlight, Docusaurus, MkDocs. Sync, health checks, migrations, ADRs, runbooks, README, and AGENTS.md. Use when docs change. NOT for backend code, skill definition edits (skill-creator), or MCP servers (mcp-creator). |
| draw-thing | Local AI image generation via Draw Things CLI. txt2img, img2img, upscale, inpaint, ControlNet, LoRA, batch. Use when you need local image work on macOS. NOT for UI implementation (frontend-designer). |
| email-whiz | Gmail copilot via MCP. Triage, inbox-zero, filters, analytics, labels, cleanup. Use when managing email or automating Gmail. NOT for composing emails, calendar, or non-Gmail. |
| event-driven-architect | Design event-driven systems: contracts, topics, consumers, retries, idempotency, and sagas. Use for asynchronous workflows. NOT for CRUD APIs or ETL pipelines. |
| external-skill-auditor | Audit third-party Agent Skills before install or repo promotion. Use when evaluating external skill sources, hooks, scripts, provenance, credentials, network behavior, or destructive commands. NOT for creating skills, code review, or appsec scans. |
| files-buddy | Safe filesystem organization, deduplication, renaming, and cleanup with cloud drive support. Delegates to best-in-class CLI tools. Use for file management. NOT for shell scripts (shell-scripter). |
| frontend-designer | Build and audit React, Tailwind, shadcn/ui interfaces. Scaffold, create components/pages, theme, refactor, verify rendered UI. Use when building UI. NOT for backend, tests, state, routing, or DevOps. |
| git-workflow | Git operations: conventional commits, PR descriptions, branch strategy, conflict resolution, code archaeology, bisect. Use for git workflow tasks. NOT for code review, CI/CD, or changelogs. |
| harness-master | Audit harness configs and apply fixes. Use when tuning Claude Code, Codex, Cursor, Gemini CLI, Antigravity, Copilot, or OpenCode. NOT for agents (agent-conventions) or MCP servers (mcp-creator). |
| honest-review | Review code with confidence-scored evidence. Session, scoped, PR, or full audit; optional approved fix pass. Use when reviewing changes or quality. NOT for feature work or benchmarking. |
| host-panel | Facilitate research-grounded panels in roundtable, Oxford, and Socratic formats. Use when exploring contested topics from multiple angles. NOT for Q&A, code review, or real human opinion simulation. |
| i18n-localization | Plan and review localization changes across app, docs, and web surfaces. Use for string extraction, locale routing, plural/date/number formatting, RTL, pseudo-locale QA, message catalogs, and translation readiness. NOT for generic copy editing, frontend visual design, SEO, or JavaScript conventions. |
| incident-response-engineer | Operational incident response for triage, containment, communications, recovery, and postmortems. Use when coordinating outages or service degradation. NOT for code review or proactive security scanning. |
| infrastructure-coder | Infrastructure-as-Code: Terraform, Kubernetes, Docker. Generate, review, cost-compare, security-scan. Use for IaC work. NOT for CI/CD (devops-engineer), application code, or actual pricing. |
| javascript-conventions | Configure and validate JS/TS tooling conventions. Enforce pnpm, TypeScript, ESLint, and Prettier defaults. Use when working on JS/TS files or package.json. NOT for Python, backend-only, or shell scripts. |
| learn | Capture corrections and patterns as reusable knowledge. Routes to the right instruction file. Use when patterns repeat 3+ times or to save insights. NOT for one-time fixes or code review. |
| mcp-creator | Build MCP servers with FastMCP v3. Research, scaffold, implement, test, deploy. Use when creating MCP servers or integrating APIs via MCP. NOT for REST APIs, CLI tools, or non-MCP integrations. |
| namer | Name anything: projects, products, companies, packages. Generates creative names across linguistic archetypes, checks handle/username availability across platforms, checks domain availability with pricing, and ranks options with scored rationales. Use when naming projects, products, startups, packages, or brands. NOT for domain management (infrastructure-coder) or branding strategy beyond naming (host-panel). |
| nerdbot | Create, repair, query, audit, and migrate Obsidian-native knowledge bases with layered raw/wiki structure, provenance, indexes, logs, and safe vault overhauls. Use for git-friendly KBs and persistent llm-wiki-style vaults. NOT for docs sites or generic notes. |
| observability-advisor | Design and review logs, metrics, traces, SLOs, and alerting for reliable systems. Use for telemetry strategy and coverage gaps. NOT for live incident command or vendor-specific setup. |
| orchestrator | Review and orchestrate parallel execution via subagent waves, teams, and pipelines. Use when 2+ independent actions need coordination. NOT for single-action tasks. |
| performance-profiler | Performance analysis: complexity estimation, profiler output parsing, caching design, regression risk. Use for optimization guidance. NOT for running profilers, load tests, or monitoring. |
| prompt-engineer | Prompt engineering. Craft, analyze, harden, convert, design tool prompts, and build PromptOps/eval plans. Use for system, agent, tool, RAG prompts. NOT for running prompts or building agents. |
| python-conventions | Enforce Python tooling conventions for uv, ty, Ruff, pytest, and pyproject.toml. Use when working on .py files or Python project config. NOT for JS/TS, shell scripts, CI design, profiling, or test architecture. |
| reasoning-router | Classify problems and route to optimal thinking MCP (11 available). Monitor confidence, re-route on stall. Use for complex reasoning. NOT for simple questions (answer directly) or code review (honest-review). |
| release-pipeline-architect | Release workflow architecture for versioning, artifact promotion, rollout safety, and rollback design. Use for release pipelines. NOT for generic CI tuning or infrastructure. |
| research | Deep multi-source research with confidence scoring. Auto-classifies complexity. Use for technical investigation, fact-checking. NOT for code review or simple Q&A. |
| schema-evolution-planner | Plan zero-downtime schema changes across code, data backfills, and cutovers. Use for expand-contract database changes. NOT for fresh schema design or DBA ops. |
| security-scanner | Proactive security assessment with SAST, secrets detection, dependency scanning, and compliance checks. Use for pre-deployment audit. NOT for code review (honest-review) or pen testing. |
| shell-conventions | Apply and review shell tooling conventions. Enforce portable bash and sh practices, quoting, env usage, and Make or just patterns. Use when editing shell files. NOT for Python or CI/CD. |
| shell-scripter | Shell script generation, review, and dialect conversion. Makefile and justfile generation. ShellCheck rules. Use for shell work. NOT for Python (python-conventions) or CI/CD (devops-engineer). |
| simplify | Simplify working code without changing behavior. Analyze, apply, or explain clarity fixes. Use when recent code feels complex. NOT for review (honest-review) or debt scans (tech-debt-analyzer). |
| skill-creator | Create, improve, and audit AI agent skills. 14 structural patterns, deterministic scoring. Use when building or reviewing skills. NOT for agents, MCP servers, or running skills. |
| skill-router | Route tasks to local skills. Use when choosing skills, recovering omitted skills after context warnings, or preparing a small skill context packet. NOT for install, authoring, or audit workflows. |
| tech-debt-analyzer | Systematic tech debt inventory with complexity analysis, dead code detection, and remediation planning. Track debt over time. NOT for code review (honest-review) or refactoring. |
| test-architect | Test strategy, coverage analysis, edge case identification, flaky test diagnosis. Use when designing test suites. NOT for running tests (devops-engineer), TDD, or code review (honest-review). |
| wargame | Strategic decision analysis and wargaming. Auto-classifies complexity for analysis or simulation. Use for decisions under uncertainty. NOT for simple pros/cons or code review. |

## 🤖 Agents

System prompts and context definitions for AI agents.

| Name | Description |
| ---- | ----------- |
| code-reviewer | Review changes for correctness, risk, and maintainability without editing code. |
| docs-writer | Update or create technical documentation grounded in the current codebase. |
| orchestrator | Coordinate multi-step work by decomposing, delegating, and synthesizing results. |
| performance-profiler | Investigate performance bottlenecks and recommend the highest-leverage fixes. |
| planner | Create a codebase-grounded implementation plan before coding. |
| release-manager | Prepare release notes, versioning, and ship-readiness checks with cautious permissions. |
| researcher | Investigate a technical question deeply and return a concise evidence-backed summary. |
| security-auditor | Audit code and configuration for security risks without making changes. |

## 🛠️ Development

| Command | Description |
| ------- | ----------- |
| `wagents new skill <name>` | Create a new skill |
| `wagents new agent <name>` | Create a new agent |
| `wagents new mcp <name>` | Create a new MCP server |
| `wagents doctor` | Check local environment and toolchain health |
| `wagents validate` | Validate all skills and agents |
| `wagents skills sync --dry-run` | Preview additive cross-harness skill sync from the normalized inventory |
| `wagents skills search <query>` | Search local repo, installed, and plugin skills on demand |
| `wagents skills context <query>` | Build a compact context packet for matching skills |
| `make typecheck` | Run ty across `wagents/` and `scripts/` |
| `wagents readme` | Regenerate this README |
| `wagents package <name>` | Package a skill into portable ZIP |
| `wagents package --all` | Package all skills |
| `wagents install` | Install all skills to all agents |
| `wagents install -a <agent>` | Install all skills to specific agent |
| `wagents install <name>` | Install specific skill to all agents |
| `wagents install <name> -a <agent>` | Install specific skill to specific agents |
| `wagents update` | Refresh installed skills from their recorded sources |
| `wagents docs init` | One-time setup: install docs dependencies |
| `wagents docs generate` | Generate MDX content pages from assets |
| `wagents docs generate --include-installed` | Include installed skills discovered from the normalized harness inventory in generated docs |
| `wagents docs dev` | Generate + launch dev server |
| `wagents docs build` | Generate + production build |
| `wagents docs preview` | Generate + build + preview server |
| `wagents docs clean` | Remove generated content pages |

Third-party skill collections can be installed directly with `npx skills add <source> --skill <name> -y -g --agent <agent>`. Repeat `--skill` and `--agent` to target a curated subset.

## 🤝 Supported Agents

- [Antigravity](https://antigravity.google/)
- [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- [Codex](https://github.com/openai/codex)
- [Crush](https://github.com/crush-ai/crush)
- [Cursor](https://cursor.sh/)
- [Gemini CLI](https://github.com/google/gemini-cli)
- [GitHub Copilot](https://github.com/features/copilot)
- [OpenCode](https://github.com/anomalyco/opencode) — native AGENTS.md support with repo-level config
And other [agentskills.io](https://agentskills.io)-compatible agents.

## 📚 Documentation

Explore the full catalog, installation guides, and generated reference pages at [agents.w4w.dev](https://agents.w4w.dev).

## 📜 License

[MIT](LICENSE)
