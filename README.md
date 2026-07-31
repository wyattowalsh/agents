<div align="center">
  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/docs/src/assets/brand/logo.webp" alt="Agents Logo" width="100" height="100">
  <h1>agents</h1>
  <p><b>Portable AI agent skills, MCP config, and shared instructions</b></p>
  <p>
    <a href="https://github.com/wyattowalsh/agents/actions/workflows/CI"><img src="https://github.com/wyattowalsh/agents/actions/workflows/CI/badge.svg" alt="CI"></a>
    <a href="https://github.com/wyattowalsh/agents/blob/main/LICENSE"><img src="https://img.shields.io/github/license/wyattowalsh/agents?style=flat-square&color=5D6D7E" alt="License"></a>
    <a href="https://github.com/wyattowalsh/agents/releases"><img src="https://img.shields.io/github/v/release/wyattowalsh/agents?style=flat-square&color=2E86C1" alt="Release"></a>
    <a href="https://agents.w4w.dev/skills/catalog/"><img src="https://img.shields.io/badge/skills-67-0f766e?style=flat-square" alt="Skills"></a>
    <a href="https://agents.w4w.dev"><img src="https://img.shields.io/badge/docs-agents.w4w.dev-00b4d8?style=flat-square&logo=read-the-docs&logoColor=white" alt="Docs"></a>
  </p>
  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/docs/public/social-card.png" alt="Agents social preview" width="640">
</div>

---

## 🚀 Quick Start

New here? Start with [START-HERE.md](START-HERE.md) for a 30-minute onboarding path.

Install all skills globally into your favorite agents:

```bash
npx skills add github:wyattowalsh/agents --all -y -g --agent claude-code --agent codex --agent crush --agent cursor --agent opencode
```

For non-trivial repository changes, check the OpenSpec workflow state:

```bash
uv run wagents openspec doctor
```

## 📦 Distribution

This repo is packaged as one cross-agent bundle with native plugin adapters and a skills CLI fallback:

| Target | Path | Update behavior |
| ------ | ---- | --------------- |
| Claude Code | `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` | Git-hosted plugin updates resolve from the latest commit because the plugin version is intentionally unpinned |
| Codex | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` | Codex can load the Git-backed plugin bundle and bundled skills from the repository root |
| OpenCode | `opencode.json` + `.opencode/` | Repo-managed npm runtime plugin specs use `@latest`; OCX-managed components stay copied under `.opencode/` with `.ocx/` receipts; restart OpenCode or refresh `~/.cache/opencode/packages/` when Bun's plugin cache is stale |
| Other agents | `npx skills add github:wyattowalsh/agents ...` | `wagents update` refreshes recorded sources, and `wagents skills sync` additively reconciles repo + curated external skills across harnesses |
| OpenSpec | `openspec/` + `uv run wagents openspec ...` | Spec/change workflow with JSON wrappers and local downstream AI tool artifact generation |

## 🤝 Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) before changing skills, agents, MCP config, docs generators, external skill metadata, distribution files, or validation behavior.

Use source-of-truth files first, regenerate derived docs and indexes with `wagents`, and run `uv run wagents openspec validate` for non-trivial public formats, downstream tooling, docs generation, validation behavior, sync behavior, or multi-surface distribution work.

Security-sensitive reports and secret-handling rules are documented in [SECURITY.md](SECURITY.md).

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
| cross-agent-install-smoke | Phase 1 dry-run JSON smoke and phase 2 temp-HOME install smoke for skills sync. Use when validating cross-harness install parity. NOT for live --apply installs. |
| data-pipeline-architect | Analyzes and designs batch and streaming data pipelines with contracts, lineage, reliability, and cost controls. Use for ingestion and transformation systems. NOT for ad-hoc analysis or schema design. |
| data-wizard | Analyze data and guide ML: EDA, model selection, feature engineering, stats, visualization, MLOps. Use for data work. NOT for ETL, database design (database-architect), or frontend viz code. |
| database-architect | Design schemas, plan migrations, and optimize queries. Six modes from modeling to evolution. Use for database architecture. NOT for DBA ops, backups, or deployment (devops-engineer). |
| design | Design, build, refactor, and audit user-facing interfaces. Use for UI/UX, accessibility, motion, design systems, AI interfaces, badges/status indicators, and rendered proof. NOT for backend APIs, tests, DevOps, routing, architecture diagrams, or non-UI docs. |
| devops-engineer | Design, optimize, and debug CI/CD pipelines. GitHub Actions and GitLab CI patterns. Use for pipeline work. NOT for infrastructure provisioning (infrastructure-coder) or app code. |
| docling-graph | Use when designing/reviewing Docling Graph knowledge-graph workflows: templates, contracts, CLI/API configs, inspect reports, exports, traces. NOT for generic Docling parsing, vector-only RAG, graph DB admin, or ontology-only work. |
| docs-steward | Maintain docs across Starlight, Docusaurus, MkDocs. Sync, health checks, migrations, ADRs, runbooks, README, and AGENTS.md. Use when docs change. NOT for backend code, skill definition edits (skill-creator), or MCP servers (mcp-creator). |
| draw-thing | Generate local AI images and short media with Draw Things CLI on macOS. Use when you need local txt2img, img2img, model setup, imports, prompt refinement, or rig-aware best-model selection. NOT for UI implementation (design), ad copy iteration (ad-creative), or broad vendor/tool research (research). |
| email-whiz | Gmail copilot via MCP. Triage, inbox-zero, filters, analytics, labels, cleanup. Use when managing email or automating Gmail. NOT for composing emails, calendar, or non-Gmail. |
| event-driven-architect | Design event-driven systems: contracts, topics, consumers, retries, idempotency, and sagas. Use for asynchronous workflows. NOT for CRUD APIs or ETL pipelines. |
| ffmpeg | Probe, trim, transcode, concat, and extract local A/V with ffmpeg/ffprobe. Use when converting or inspecting media files. NOT for AI image generation (draw-thing) or UI design (design). |
| files-buddy | Use when safely auditing, organizing, deduplicating, renaming, archiving, offloading, or reclaiming storage on macOS file systems and cloud-drive folders. NOT for shell script generation, CI/CD, databases, or non-macOS platform cleanup. |
| git-workflow | Git operations: conventional commits, PR descriptions, branch strategy, conflict resolution, code archaeology, bisect. Use for git workflow tasks. NOT for code review, CI/CD, or changelogs. |
| grok-delegate | Use when delegating to native Grok CLI for default Tier-T trivial leaves or wave/tune nodes from parent harnesses. NOT for harness sync or wrappers. |
| harness-master | Audit harness configs, discover gaps, usage signals, apply approved fixes. Use when tuning Claude, Codex, Copilot, Cursor, Gemini, Grok, OpenCode, Cherry, or LM Studio. NOT agents, MCP, or app telemetry. |
| host-panel | Facilitate research-grounded panels in roundtable, Oxford, and Socratic formats. Use when exploring contested topics from multiple angles. NOT for Q&A, code review, or real human opinion simulation. |
| i18n-localization | Plan and review localization changes across app, docs, and web surfaces. Use for string extraction, locale routing, plural/date/number formatting, RTL, pseudo-locale QA, message catalogs, and translation readiness. NOT for generic copy editing, frontend visual design, SEO, or JavaScript conventions. |
| incident-response-engineer | Operational incident response for triage, containment, communications, recovery, and postmortems. Use when coordinating outages or service degradation. NOT for code review or proactive security scanning. |
| infrastructure-coder | Infrastructure-as-Code: Terraform, Kubernetes, Docker. Generate, review, cost-compare, security-scan. Use for IaC work. NOT for CI/CD (devops-engineer), application code, or actual pricing. |
| javascript-conventions | Configure and validate JS/TS tooling conventions. Enforce pnpm, TypeScript, ESLint, and Prettier defaults. Use when working on JS/TS files or package.json. NOT for Python, backend-only, or shell scripts. |
| justfile | Create, edit, migrate, check, and inspect just/justfile runners. Use when changing justfiles, migrating Makefile/npm scripts to just, linting house-style justfiles, or discovering via just --list/--show/--dump. NOT for shell scripts (shell-scripter), shell conventions (shell-conventions), CI YAML (devops-engineer), Make mtime builds, Compose, or mise. |
| learn | Capture corrections and patterns as reusable knowledge. Routes to the right instruction file. Use when patterns repeat 3+ times or to save insights. NOT for one-time fixes or code review. |
| mcp-creator | Build MCP servers with FastMCP v3. Research, scaffold, implement, test, deploy. Use when creating MCP servers or integrating APIs via MCP. NOT for REST APIs, CLI tools, or non-MCP integrations. |
| mcphub-operator | Operate MCPHub groups, endpoints, compression, and CLI from repo registry. Use for hub preflight, group picking, tunnel vs local exposure. NOT harness sync. |
| namer | Name anything: projects, products, companies, packages. Generates creative names across linguistic archetypes, checks handle/username availability across platforms, checks domain availability with pricing, and ranks options with scored rationales. Use when naming projects, products, startups, packages, or brands. NOT for domain management (infrastructure-coder) or branding strategy beyond naming (host-panel). |
| nerdbot | Use when creating, repairing, querying, auditing, or migrating Obsidian-native git KBs with raw/wiki layers. NOT for docs sites or generic notes. |
| new-project | Initialize projects with safe, preference-driven scaffolds, docs, AI instructions, quality gates, GitHub setup, and design baselines. Use when starting a repo or non-destructively adding conventions. NOT for product features, agents, MCP servers, cloud provisioning, or destructive migrations. |
| observability-advisor | Design and review logs, metrics, traces, SLOs, and alerting for reliable systems. Use for telemetry strategy and coverage gaps. NOT for live incident command or vendor-specific setup. |
| opencode-ensemble | Use when coordinating OpenCode Ensemble teams, delegating independent coding work, reviewing teammate output, or running staged parallel waves. NOT for single-agent tasks, nested team-of-teams, or teammate subagents using team tools. |
| openspec-workflow | Use when planning, applying, validating, or archiving OpenSpec changes in this repo, or when downstream AI tools need OpenSpec JSON status/instructions. NOT for generic code review, unrelated docs edits, or replacing generated upstream openspec-* skills. |
| orchestrator | Review and orchestrate parallel execution via subagent waves, teams, and pipelines. Use when 2+ independent actions need coordination. NOT for single-action tasks. |
| pentest | Authorized pentest planning with mandatory ROE scope gate. Synthesizes phase checklists and findings. NOT for static audit (security-scanner), CTF labs (ctf-*), or C2/webshell tooling. |
| performance-profiler | Performance analysis: complexity estimation, profiler output parsing, caching design, regression risk. Use for optimization guidance. NOT for running profilers, load tests, or monitoring. |
| prompt-engineer | Prompt engineering. Craft, analyze, harden, convert, design tool prompts, and build PromptOps/eval plans. Use for system, agent, tool, RAG prompts. NOT for running prompts or building agents. |
| python-conventions | Enforce Python tooling conventions for uv, ty, Ruff, pytest, and pyproject.toml. Use when working on .py files or Python project config. NOT for JS/TS, shell scripts, CI design, profiling, or test architecture. |
| reasoning-router | Classify problems and route to optimal thinking MCP (11 available). Monitor confidence, re-route on stall. Use for complex reasoning. NOT for simple questions (answer directly) or code review (review). |
| release-pipeline-architect | Release workflow architecture for versioning, artifact promotion, rollout safety, and rollback design. Use for release pipelines. NOT for generic CI tuning or infrastructure. |
| research | Deep multi-source research with reviewable plans, source-support auditing, and confidence scoring. Use for technical, academic, market, fact-checking investigation. NOT for code review or simple Q&A. |
| review | Use for session, scoped, PR, range, full audit, simplification, and source/provenance reviews with evidence-first findings. NOT for feature implementation or benchmarking. |
| schema-evolution-planner | Plan zero-downtime schema changes across code, data backfills, and cutovers. Use for expand-contract database changes. NOT for fresh schema design or DBA ops. |
| security-scanner | Proactive security assessment with SAST, secrets detection, dependency scanning, and compliance checks. Use for pre-deployment audit. NOT for code review (review) or pen testing. |
| shell-conventions | Apply and review shell tooling conventions. Enforce portable bash and sh practices, quoting, env usage, and Make or just patterns. Use when editing shell files. NOT for Python or CI/CD. |
| shell-scripter | Shell script generation, review, and dialect conversion. Makefile and justfile generation. ShellCheck rules. Use for shell work. NOT for Python (python-conventions) or CI/CD (devops-engineer). |
| skill-bundle-curator | Summarize bundle components from agent-bundle.json and repo skill/agent counts. Use when packaging or auditing distributable bundles. NOT for live plugin installs. |
| skill-compat-matrix | Report portable vs runtime-specific skill fields across supported harnesses. Use when auditing cross-agent compatibility. NOT for live installs or packaging. |
| skill-creator | Create, improve, and audit AI agent skills. 14 structural patterns, deterministic scoring. Use when building or reviewing skills. NOT for agents, MCP servers, or running skills. |
| skill-eval-scaffolder | Scaffold evals/evals.json manifests for repo skills with baseline cases. Use when adding behavioral eval coverage. NOT for live LLM eval execution. |
| skill-install-dry-run-planner | Plan cross-harness skills sync dry-run steps before any live install. Use when reconciling harness skill inventory. NOT for --apply or npx installs. |
| skill-lifecycle-manager | Report skill lifecycle stage from frontmatter, eval coverage, and validators. Use when promoting, deprecating, or auditing repo skills. NOT for live installs. |
| skill-package-manifest-enricher | Generates manifest sidecars from safe YAML and catalog/sync evidence. Use when enriching metadata before package validation. NOT for ZIP creation, guessed harness support, installs, or source edits. |
| skill-quality-dashboard | Aggregate generated maintainer reports into a skill-quality summary. Use when reviewing docs, link, and eval health. NOT for editing report sources. |
| skill-router | Route tasks to local skills. Use when choosing skills, recovering omitted skills after context warnings, or preparing a small skill context packet. NOT for install, authoring, or audit workflows. |
| skill-tag-taxonomist | Infer and audit skill tags from names, descriptions, and catalog authoring rows. Use when organizing catalog taxonomies. NOT for live catalog index edits. |
| skill-token-budget-linter | Lint skill descriptions, body length, and reference bulk against token budgets. Use when tightening standing-context cost. NOT for DCP tuning or RTK hooks. |
| skill-trace-debugger | Inspect eval manifests and portable validators for trace-friendly skill signals. Use when debugging skill invocation gaps. NOT for live LLM trace capture. |
| tech-debt-analyzer | Systematic tech debt inventory with complexity analysis, dead code detection, and remediation planning. Track debt over time. NOT for code review (review) or refactoring. |
| test-architect | Test strategy, coverage analysis, edge case identification, flaky test diagnosis. Use when designing test suites. NOT for running tests (devops-engineer), TDD, or code review (review). |
| things-manager | Use when reviewing/managing Things 3 via SupaThings MCP: tasks, projects, headings, tags, deadlines, triage, capture, cleanup, and GTD. NOT for calendars, Gmail, database edits, MCP setup, or secrets. |
| trafilatura | Extract clean article text and metadata from URLs or HTML with trafilatura CLI. Use for single-page extraction, piped/local HTML, bounded discovery. NOT for research synthesis (research), PDFs (docling), raw fetch (fetch), video (yt-dlp). |
| wargame | Strategic decision analysis and wargaming. Auto-classifies complexity for analysis or simulation. Use for decisions under uncertainty. NOT for simple pros/cons or code review. |
| yt-dlp | Probe, transcript, and download video/audio with yt-dlp CLI on supported hosts. Use when you need metadata, captions, or local media. Transcript-first (probe, transcript, download). NOT for static HTML (Fetch MCP), research, or ffmpeg transforms. |

## 🤖 Agents

System prompts and context definitions for AI agents.

| Name | Description |
| ---- | ----------- |
| agent-change-recorder | Record agent definition changes with validation evidence for maintainer audit trails. |
| agent-eval-runner | Run structural eval gates for skills and agents; report adequacy without live LLM runs. |
| agent-permission-simulator | Scaffold for simulating agent permission decisions against sample tool calls (planned). |
| agent-registry-publisher | Scaffold for publishing agent catalog registry artifacts (planned). |
| agent-transpiler | Scaffold for transpiling portable agent frontmatter across harness projections (planned). |
| bridge-consistency-checker | Verify instruction bridge and discovery parity across harness sync projections. |
| code-reviewer | Review changes for correctness, risk, and maintainability without editing code. |
| docs-writer | Update or create technical documentation grounded in the current codebase. |
| mcp-capability-mapper | Map MCP server tools to harness registry entries and maintainer docs surfaces. |
| mcp-template-maintainer | Maintain FastMCP v3 MCP scaffolds in mcp/; align templates with repo conventions. |
| orchestrator | Coordinate multi-step work by decomposing, delegating, and synthesizing results. |
| performance-profiler | Investigate performance bottlenecks and recommend the highest-leverage fixes. |
| permission-policy-auditor | Audit agent permissionMode, tool allowlists, and OpenCode permission overlays for least privilege. |
| planner | Create a codebase-grounded implementation plan before coding. |
| prompt-optimizer | Scaffold for prompt/token optimization reviews on agent and skill bodies (planned). |
| release-manager | Prepare release notes, versioning, and ship-readiness checks with cautious permissions. |
| researcher | Investigate a technical question deeply and return a concise evidence-backed summary. |
| security-auditor | Audit code and configuration for security risks without making changes. |
| skill-author | Read-only advisor for skill authoring, audits, and eval planning. Does not edit skill files. |
| triage-lead | Classify incoming work by severity, harness surface, and ownership; route to specialist agents. |

## 🔌 MCP Servers

First-party MCP servers authored in this repository (see `AGENTS.md` §2). Curated external servers are configured in `config/mcp-registry.json` and exposed via MCPHub.

| Name | Description |
| ---- | ----------- |
| mcp-agent-catalog | Read-only MCP server exposing the repo agent catalog (agents/, agent -> skill/mcp cross-reference edges) |
| mcp-changelog-digest | Stub MCP server for changelog digest summaries |
| mcp-ci-artifacts | Read-only MCP server for docs/public/generated-reports CI JSON and artifact registry metadata |
| mcp-docs-graph | Read-only MCP server exposing docs/public/generated-reports/docs-graph-snapshot.json |
| mcp-docs-index | Read-only MCP server exposing generated docs reports (docs/public/generated-reports/*.json) and content page metadata |
| mcp-eval-results | Read-only MCP server exposing wagents eval list/coverage/adequacy/validate results |
| mcp-mcphub | MCPHub control-plane metadata MCP server |
| mcp-oauth-reference | Read-only OAuth MCP configuration reference shape for maintainers |
| mcp-registry-publisher | Stub MCP server for future registry publishing workflows |
| mcp-release-provenance | Read-only MCP server for release and provenance manifests and workflows |
| mcp-repo-readonly | Read-only MCP server exposing an allowlisted subset of repo files (skills/, agents/, mcp/, docs/, config/, openspec/, ...) |
| mcp-sandbox-profiles | Stub MCP server for sandbox profile reference data |
| mcp-skill-catalog | Read-only MCP server exposing the repo skill catalog (skills/, docs/public/generated-registries/skills-catalog-index.json) |
| mcp-source-url-health | Read-only MCP server that checks the reachability of skill/agent/mcp source URLs over HTTP |
| mcp-template-smoke | Read-only MCP server for dry-run MCP scaffold and layout validation |
| mcp-workflow-status | Read-only MCP server summarizing .github/workflows YAML files |

## 🛠️ Development

| Command | Description |
| ------- | ----------- |
| `wagents new skill <name>` | Create a new skill |
| `wagents new agent <name>` | Create a new agent |
| `wagents new mcp <name>` | Create a new MCP server |
| `wagents doctor` | Check local environment and toolchain health |
| `wagents validate` | Validate all skills and agents |
| `wagents openspec doctor` | Diagnose OpenSpec tooling, project state, and downstream tool mapping |
| `wagents openspec validate` | Validate OpenSpec specs and changes with JSON-backed output |
| `wagents skills sync --dry-run` | Preview additive cross-harness skill sync from the normalized inventory |
| `wagents skills search <query>` | Search local repo, installed, and plugin skills on demand |
| `wagents skills context <query>` | Build a compact context packet for matching skills |
| `just typecheck` | Run ty across `wagents/` and `scripts/` |
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
- [Grok Build](https://x.ai/)
- [OpenCode](https://github.com/anomalyco/opencode) — native AGENTS.md support with repo-level config
- [Cherry Studio](https://www.cherry-ai.com/) — MCP-only via MCPHub registry
And other [agentskills.io](https://agentskills.io)-compatible agents.

## 📚 Documentation

Explore the full catalog, installation guides, and generated reference pages at [agents.w4w.dev](https://agents.w4w.dev).

## 📜 License

[MIT](LICENSE)
