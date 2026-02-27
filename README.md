# agents

AI agent artifacts, configs, skills, tools, and more

## Install

```bash
npx skills add wyattowalsh/agents --all -g
```

## Skills

| Name | Description |
| ---- | ----------- |
| add-badges | Scan a codebase to detect languages, frameworks, CI/CD pipelines, package managers, and tools, then generate and insert shields.io badges into the README with correct icons, brand colors, and live data endpoints. Use when adding badges, updating badges, removing badges, improving README appearance, adding shields, adding CI status badges, or making a README look more professional. NOT for README content writing, documentation generation, or CI/CD setup. |
| agent-conventions | Agent definition conventions. Use when creating or modifying agents at any level (~/.claude/agents/, .claude/agents/, or project-local). Validate frontmatter, update README.md index. NOT for creating skills, MCP servers, or modifying CLAUDE.md. |
| email-whiz | Gmail inbox copilot via MCP. Triage, inbox zero with streak tracking, smart filters, auto-rules, analytics, newsletters, labels, search, senders, digest, cleanup, audit. Use when overwhelmed by email or building Gmail filters. NOT for: composing emails, calendar, Google Drive, non-Gmail. |
| frontend-designer | Build production-grade frontend interfaces with modern React, Tailwind CSS, and shadcn/ui. Five modes: scaffold projects, create components, configure themes and design tokens, refactor styles, and audit codebases. Encodes best practices for React 19 Server Components (framework-dependent), TailwindCSS v4 CSS-first config, shadcn/ui with Radix primitives, modern CSS (container queries, :has(), view transitions, scroll-driven animations), Monaspace typography, and Vite 6. Supersedes the frontend-design skill. Use when building, styling, theming, or improving any frontend project. NOT for backend APIs, database design, DevOps, testing frameworks, state management libraries, routing, or full SSR framework setup. |
| honest-review | Research-driven code review with confidence-scored, evidence-validated findings. Session review or full codebase audit via parallel teams. Use when reviewing changes, auditing codebases, verifying work quality. NOT for writing new code, explaining code, or benchmarking. |
| host-panel | Host simulated panel discussions and debates among AI-simulated domain experts. Supports roundtable, Oxford-style, and Socratic formats with heterogeneous expert personas, anti-groupthink mechanisms, and structured synthesis. Use when exploring complex topics from multiple expert perspectives, testing argument strength, academic brainstorming, or understanding trade-offs in decisions. NOT for one-on-one conversations, simple Q&A, or real-time debates. |
| javascript-conventions | JavaScript/Node.js tooling conventions. Use when working on JS/TS files, package.json, or Node.js projects. Enforce pnpm for package management. NOT for Python projects, backend-only work, or shell scripts. |
| learn | Capture corrections, insights, and patterns as reusable project knowledge. Routes learnings to the right instruction file. Applies kaizen: small improvements, error-proofing, standards work. Auto-invoked when a correction pattern is detected 3+ times. Also use manually when Claude makes a repeated mistake, discovers a non-obvious gotcha, or when you want to persist a workflow preference. |
| mcp-creator | Build production-ready MCP servers using FastMCP v3. Guides research, scaffolding, tool/resource/prompt implementation, testing, and deployment. Targets FastMCP 3.0.0rc2 with Providers, Transforms, middleware, OAuth, and composition. Use when creating MCP servers, integrating APIs via MCP, converting OpenAPI specs or FastAPI apps, or troubleshooting FastMCP issues. NOT for building REST APIs, CLI tools, or non-MCP integrations. |
| orchestrator | Build and deploy parallel execution via subagent waves, agent teams, and multi-wave pipelines. Use when the Decomposition Gate identifies 2+ independent actions or when spawning teams. NOT for single-action tasks or non-parallel work.
 |
| prompt-engineer | Comprehensive prompt and context engineering for any AI system. Four modes: (1) Craft new prompts from scratch, (2) Analyze existing prompts with diagnostic scoring and optional improvement, (3) Convert prompts between model families (Claude/GPT/Gemini/Llama), (4) Evaluate prompts with test suites and rubrics. Adapts all recommendations to model class (instruction-following vs reasoning). Validates findings against current documentation. Use for system prompts, agent prompts, RAG pipelines, tool definitions, or any LLM context design. NOT for running prompts, generating content, or building agents. |
| python-conventions | Python tooling conventions. Use when working on .py files, pyproject.toml, or Python projects. Enforce uv for package management, ty for type checking. NOT for JavaScript/TypeScript projects or shell scripts. |
| research | General-purpose deep research with multi-source synthesis and confidence-scored findings. Auto-classifies complexity from quick lookup to exhaustive investigation. Cross-validates across independent sources with anti-hallucination verification, contradiction detection, and bias auditing. Produces synthesis products with evidence chains and provenance. Resumable journal sessions. Use when investigating technical topics, academic questions, market analysis, competitive intelligence, architecture decisions, technology evaluation, fact-checking, literature review, or trend analysis. NOT for code review (use honest-review), strategic decisions (use wargame), multi-perspective debate (use host-panel), or simple factual Q&A answerable in one search. |
| skill-creator | Create, improve, and audit AI agent skills. Applies 14 proven structural patterns, scores quality with deterministic audit, manages full lifecycle. Use when building, refactoring, or reviewing skills. NOT for agents, MCP servers, or running existing skills. |
| wargame | Domain-agnostic strategic decision analysis and wargaming. Auto-classifies scenario complexity: simple decisions get structured analysis (pre-mortem, ACH, decision trees); complex or adversarial scenarios get full multi-turn interactive wargames with AI-controlled actors, Monte Carlo outcome exploration, and structured adjudication. Generates visual dashboards and saves markdown decision journals. Use for business strategy, crisis management, competitive analysis, geopolitical scenarios, personal decisions, or any consequential choice under uncertainty. NOT for simple pros/cons lists, non-strategic decisions, or academic debate. |

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
