# agents

AI agent artifacts, configs, skills, tools, and more

## Install

```bash
npx skills add wyattowalsh/agents --all -g
```

## Skills

| Name | Description |
| ---- | ----------- |
| add-badges | Scan a codebase to detect languages, frameworks, CI/CD pipelines, package managers, and tools, then generate and insert shields.io badges into the README with correct icons, brand colors, and live data endpoints. Use when adding badges, updating badges, removing badges, improving README appearance, adding shields, adding CI status badges, or making a README look more professional. Supports shields.io, badgen.net, and forthebadge.com with all styles including for-the-badge. Handles badge grouping, ordering, style matching, custom badges, and incremental updates. |
| agent-conventions | Agent definition conventions. When creating or modifying agents at any level (~/.claude/agents/, .claude/agents/, or project-local), always update the corresponding README.md index with the new entry (table row + description section). |
| continuous-improvement | Instruction file maintenance protocol. Propose updates when a pattern is corrected 3+ times across 2+ sessions. Route: cross-project → global.md, language-specific → language skill, orchestration → orchestrator skill, project → AGENTS.md. Verify against actual practice, check for contradictions, get user approval. |
| honest-review | Research-driven code review at multiple abstraction levels with strengths acknowledgment, creative review lenses, AI code smell detection, and severity calibration by project type. Two modes: (1) Session review — review and verify changes using parallel reviewers that research-validate every assumption; (2) Full codebase audit — deep end-to-end evaluation using parallel teams of subagent-spawning reviewers. Use when reviewing changes, verifying work quality, auditing a codebase, validating correctness, checking assumptions, finding defects, reducing complexity. NOT for writing new code, explaining code, or benchmarking. |
| host-panel | Host simulated panel discussions and debates among AI-simulated domain experts. Supports roundtable, Oxford-style, and Socratic formats with heterogeneous expert personas, anti-groupthink mechanisms, and structured synthesis. Use when exploring complex topics from multiple expert perspectives, testing argument strength, academic brainstorming, or understanding trade-offs in decisions. |
| javascript-conventions | JavaScript/Node.js tooling conventions. Use pnpm for all package management (not npm or yarn, unless a project explicitly requires them). |
| mcp-creator | Build production-ready MCP servers using FastMCP v3. Guides the full lifecycle: research, scaffolding, tool/resource/prompt implementation, testing, and deployment. Targets FastMCP 3.0.0rc2 with Providers, Transforms, middleware, OAuth, composition, component versioning, background tasks, elicitation, sampling, and structured output. Prevents 34 common errors. Use when creating MCP servers, adding tools/resources/prompts, integrating APIs via MCP, converting OpenAPI specs or FastAPI apps, troubleshooting FastMCP issues, or learning FastMCP v3 patterns. Python-focused with uv toolchain. |
| orchestrator | Full orchestration guide for parallel execution, subagent waves, agent teams, and multi-wave pipelines. Invoke before complex multi-step work, when spawning teams, or when the Decomposition Gate identifies 2+ independent actions. Covers: best practices, patterns (A-F), anti-patterns, failure recovery, progress visibility. |
| prompt-engineer | Comprehensive prompt and context engineering for any AI system. Four modes: (1) Craft new prompts from scratch, (2) Analyze existing prompts with diagnostic scoring and optional improvement, (3) Convert prompts between model families (Claude/GPT/Gemini/Llama), (4) Evaluate prompts with test suites and rubrics. Adapts all recommendations to model class (instruction-following vs reasoning). Validates findings against current documentation. Use for system prompts, agent prompts, RAG pipelines, tool definitions, or any LLM context design. NOT for running prompts or generating content. |
| python-conventions | Python tooling conventions. Use uv for all operations (uv run, uv add — not pip). Use pyproject.toml with uv add (not uv pip). Use ty for type checking (not mypy). Preferred libraries: loguru, tenacity, tqdm, fastapi, typer, alembic, sqlmodel, gradio, numpy. |
| skill-creator | Create, improve, and audit AI agent skills. Applies 13 proven structural patterns, scores quality with deterministic audit, manages full lifecycle. Use when building, refactoring, or reviewing skills. NOT for agents, MCP servers, or running existing skills. |
| wargame | Domain-agnostic strategic decision analysis and wargaming. Auto-classifies scenario complexity: simple decisions get structured analysis (pre-mortem, ACH, decision trees); complex or adversarial scenarios get full multi-turn interactive wargames with AI-controlled actors, Monte Carlo outcome exploration, and structured adjudication. Generates visual dashboards and saves markdown decision journals. Use for business strategy, crisis management, competitive analysis, geopolitical scenarios, personal decisions, or any consequential choice under uncertainty. |

## Development

| Command | Description |
| ------- | ----------- |
| `wagents new skill <name>` | Create a new skill |
| `wagents new agent <name>` | Create a new agent |
| `wagents new mcp <name>` | Create a new MCP server |
| `wagents validate` | Validate all skills and agents |
| `wagents readme` | Regenerate this README |
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
