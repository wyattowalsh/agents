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
| honest-review | Research-driven code review at multiple abstraction levels with strengths acknowledgment, creative review lenses, AI code smell detection, and severity calibration by project type. Two modes: (1) Session review — review and verify changes using parallel reviewers that research-validate every assumption; (2) Full codebase audit — deep end-to-end evaluation using parallel teams of subagent-spawning reviewers. Use when reviewing changes, verifying work quality, auditing a codebase, validating correctness, checking assumptions, finding defects, reducing complexity. NOT for writing new code, explaining code, or benchmarking. |
| host-panel | Host simulated panel discussions and debates among AI-simulated domain experts. Supports roundtable, Oxford-style, and Socratic formats with heterogeneous expert personas, anti-groupthink mechanisms, and structured synthesis. Use when exploring complex topics from multiple expert perspectives, testing argument strength, academic brainstorming, or understanding trade-offs in decisions. |
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
