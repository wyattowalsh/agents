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
| docs-steward | Automatically maintain, enhance, and improve the repository documentation site. Auto-triggers when skills, agents, or MCP servers change. Syncs generated pages, enhances content quality, performs health checks, and suggests site improvements. Can modify the generation pipeline itself when it identifies gaps. |
| honest-review | Research-driven code review at multiple abstraction levels with strengths acknowledgment, creative review lenses, AI code smell detection, and severity calibration by project type. Two modes: (1) Session review — review and verify changes using parallel reviewers that research-validate every assumption; (2) Full codebase audit — deep end-to-end evaluation using parallel teams of subagent-spawning reviewers. Use when reviewing changes, verifying work quality, auditing a codebase, validating correctness, checking assumptions, finding defects, reducing complexity. NOT for writing new code, explaining code, or benchmarking. |
| host-panel | Host simulated panel discussions and debates among AI-simulated domain experts. Supports roundtable, Oxford-style, and Socratic formats with heterogeneous expert personas, anti-groupthink mechanisms, and structured synthesis. Use when exploring complex topics from multiple expert perspectives, testing argument strength, academic brainstorming, or understanding trade-offs in decisions. |
| mcp-creator | Build production-ready MCP servers using FastMCP v3. Guides through the full lifecycle: research and planning, project scaffolding, tool/resource/prompt implementation, testing, and deployment. Targets FastMCP 3.0.0rc2 with Provider/Transform architecture, middleware, OAuth, server composition, and component versioning. Includes error-prevention patterns that eliminate common failures. Use when creating new MCP servers, adding tools/resources/prompts to existing servers, integrating external APIs via MCP, troubleshooting FastMCP issues, or learning FastMCP v3 patterns. Python-focused with uv toolchain. |
| prompt-engineer | Comprehensive prompt and context engineering for any AI system. Five modes: (1) Craft new prompts from scratch, (2) Optimize existing prompts with diagnostic scoring, (3) Audit prompts for anti-patterns and security issues, (4) Convert prompts between model families (Claude/GPT/Gemini/Llama), (5) Evaluate prompts with test suites and rubrics. Adapts all recommendations to model class (instruction-following vs reasoning). Validates findings against current documentation. Use for system prompts, agent prompts, RAG pipelines, tool definitions, or any LLM context design. NOT for running prompts or generating content. |
| skill-creator | Create, improve, and audit AI agent skills for this repository. Scaffolds via wagents CLI, applies 13 proven structural patterns from the repo's best skills, scores quality with a deterministic audit script, and manages the full lifecycle through validation and documentation. Modes: create new skills, improve existing skills, audit quality scores, render comparative dashboards. Use when building new skills, refactoring skill instructions, reviewing skill quality, or learning skill-writing patterns. NOT for running skills, creating agents, or building MCP servers. |
| wargame | Domain-agnostic strategic decision analysis and wargaming. Auto-classifies scenario complexity: simple decisions get structured analysis (pre-mortem, ACH, decision trees); complex or adversarial scenarios get full multi-turn interactive wargames with AI-controlled actors, Monte Carlo outcome exploration, and structured adjudication. Generates visual dashboards and saves markdown decision journals. Use for business strategy, crisis management, competitive analysis, geopolitical scenarios, personal decisions, or any consequential choice under uncertainty. |

## Development

| Command | Description |
| ------- | ----------- |
| `wagents new skill <name>` | Create a new skill |
| `wagents new agent <name>` | Create a new agent |
| `wagents new mcp <name>` | Create a new MCP server |
| `wagents validate` | Validate all skills and agents |
| `wagents readme` | Regenerate this README |

## Supported Agents

Claude Code, Codex, Gemini CLI, and other agentskills.io-compatible agents.

## License

[MIT](LICENSE)
