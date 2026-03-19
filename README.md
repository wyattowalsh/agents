# agents

AI agent artifacts, configs, skills, tools, and more

## Install

```bash
npx skills add wyattowalsh/agents --all -g
```

## Skills

| Name | Description |
| ---- | ----------- |
| add-badges | Detect stack and generate shields.io README badges with icons, colors, live endpoints. Use when adding or updating badges. NOT for README writing, docs, or CI/CD setup. |
| agent-conventions | Agent definition conventions. Validate frontmatter, update indexes. Use when creating or modifying agents. NOT for skills, MCP servers, or CLAUDE.md. |
| api-designer | Contract-first API design for REST, GraphQL, gRPC. Design, spec, review, version, compat, sdk. Use for API architecture and OpenAPI specs. NOT for MCP servers (mcp-creator) or frontend API calls. |
| changelog-writer | Generate changelogs, release notes, and migration guides from git history. Parse conventional commits. Use for releases. NOT for git ops (git-workflow) or doc sites (docs-steward). |
| data-wizard | Analyze data and guide ML: EDA, model selection, feature engineering, stats, visualization, MLOps. Use for data work. NOT for ETL, database design (database-architect), or frontend viz code. |
| database-architect | Design schemas, plan migrations, and optimize queries. Six modes from modeling to evolution. Use for database architecture. NOT for DBA ops, backups, or deployment (devops-engineer). |
| devops-engineer | Design, optimize, and debug CI/CD pipelines. GitHub Actions and GitLab CI patterns. Use for pipeline work. NOT for infrastructure provisioning (infrastructure-coder) or app code. |
| docs-steward | Maintain docs across Starlight, Docusaurus, MkDocs. Sync, health checks, migrations, ADRs, runbooks. Use when docs change. NOT for backend code, skills (skill-creator), or MCP servers (mcp-creator). |
| email-whiz | Gmail copilot via MCP. Triage, inbox-zero, filters, analytics, labels, cleanup. Use when managing email or automating Gmail. NOT for composing emails, calendar, or non-Gmail. |
| frontend-designer | Build frontends with React, Tailwind, shadcn/ui. Scaffold, create, theme, refactor, audit. Use when building or improving UI. NOT for backend, DevOps, testing, or state management. |
| git-workflow | Git operations: conventional commits, PR descriptions, branch strategy, conflict resolution, code archaeology, bisect. Use for git workflow tasks. NOT for code review, CI/CD, or changelogs. |
| honest-review | Confidence-scored code review with evidence validation. Session or full codebase audit. Use when reviewing changes or auditing quality. NOT for writing code or benchmarking. |
| host-panel | Simulated expert panel discussions. Roundtable, Oxford-style, Socratic formats. Use when exploring topics from multiple perspectives. NOT for Q&A, code review, or one-on-one conversations. |
| infrastructure-coder | Infrastructure-as-Code: Terraform, Kubernetes, Docker. Generate, review, cost-compare, security-scan. Use for IaC work. NOT for CI/CD (devops-engineer), application code, or actual pricing. |
| javascript-conventions | JS/TS tooling conventions. Enforce pnpm. Use when working on JS/TS files or package.json. NOT for Python, backend-only, or shell scripts. |
| learn | Capture corrections and patterns as reusable knowledge. Routes to the right instruction file. Use when patterns repeat 3+ times or to save insights. NOT for one-time fixes or code review. |
| mcp-creator | Build MCP servers with FastMCP v3. Research, scaffold, implement, test, deploy. Use when creating MCP servers or integrating APIs via MCP. NOT for REST APIs, CLI tools, or non-MCP integrations. |
| namer | Name anything: projects, products, companies, packages. Generates creative names across linguistic archetypes, checks handle/username availability across platforms, checks domain availability with pricing, and ranks options with scored rationales. Use when naming projects, products, startups, packages, or brands. NOT for domain management (infrastructure-coder) or branding strategy beyond naming (host-panel). |
| orchestrator | Parallel execution via subagent waves, teams, and pipelines. Use when 2+ independent actions need coordination. NOT for single-action tasks. |
| performance-profiler | Performance analysis: complexity estimation, profiler output parsing, caching design, regression risk. Use for optimization guidance. NOT for running profilers, load tests, or monitoring. |
| prompt-engineer | Prompt engineering for any AI system. Craft, analyze, convert between models, evaluate with rubrics. Use for system prompts, agent prompts, tool defs. NOT for running prompts or building agents. |
| python-conventions | Python tooling conventions. Enforce uv, ty. Use when working on .py files or pyproject.toml. NOT for JS/TS or shell scripts. |
| reasoning-router | Classify problems and route to optimal thinking MCP (11 available). Monitor confidence, re-route on stall. Use for complex reasoning. NOT for simple questions (answer directly) or code review (honest-review). |
| research | Deep multi-source research with confidence scoring. Auto-classifies complexity. Use for technical investigation, fact-checking. NOT for code review or simple Q&A. |
| security-scanner | Proactive security assessment with SAST, secrets detection, dependency scanning, and compliance checks. Use for pre-deployment audit. NOT for code review (honest-review) or pen testing. |
| shell-scripter | Shell script generation, review, and dialect conversion. Makefile and justfile generation. ShellCheck rules. Use for shell work. NOT for Python (python-conventions) or CI/CD (devops-engineer). |
| skill-creator | Create, improve, and audit AI agent skills. 14 structural patterns, deterministic scoring. Use when building or reviewing skills. NOT for agents, MCP servers, or running skills. |
| tech-debt-analyzer | Systematic tech debt inventory with complexity analysis, dead code detection, and remediation planning. Track debt over time. NOT for code review (honest-review) or refactoring. |
| test-architect | Test strategy, coverage analysis, edge case identification, flaky test diagnosis. Use when designing test suites. NOT for running tests (devops-engineer), TDD, or code review (honest-review). |
| wargame | Strategic decision analysis and wargaming. Auto-classifies complexity for analysis or simulation. Use for decisions under uncertainty. NOT for simple pros/cons or code review. |

## Development

| Command | Description |
| ------- | ----------- |
| `wagents new skill <name>` | Create a new skill |
| `wagents new agent <name>` | Create a new agent |
| `wagents new mcp <name>` | Create a new MCP server |
| `wagents validate` | Validate all skills and agents |
| `wagents readme` | Regenerate this README |
| `wagents package <name>` | Package a skill into portable ZIP |
| `wagents package --all` | Package all skills |
| `wagents install` | Install all skills to all agents |
| `wagents install -a <agent>` | Install all skills to specific agent |
| `wagents install <name>` | Install specific skill to all agents |
| `wagents docs init` | One-time setup: install docs dependencies |
| `wagents docs generate` | Generate MDX content pages from assets |
| `wagents docs dev` | Generate + launch dev server |
| `wagents docs build` | Generate + production build |
| `wagents docs preview` | Generate + build + preview server |
| `wagents docs clean` | Remove generated content pages |

## Supported Agents

Claude Code, Codex, Gemini CLI, and other agentskills.io-compatible agents.

## License

[MIT](LICENSE)
