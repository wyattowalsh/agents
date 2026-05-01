# Harness Capability Matrix

| Harness | Support tier | Repo artifacts | Preferred lane | Secondary lane | Stability |
|---|---|---|---|---|---|
| Claude Code | `repo-present-validation-required` | .claude/, .claude-plugin/, CLAUDE.md, skills/, instructions/ | Agent Skills + Claude Code plugin | MCP for live systems | official-docs-backed |
| Claude Desktop | `planned-from-shared-artifacts` | mcp/, config/, skills/ | Agent Skills where surfaced by client; otherwise Desktop Extensions/MCP | local MCP Desktop Extensions | official-docs-backed-partial |
| ChatGPT | `planned-research-backed` | AGENTS.md, docs/, instructions/ | Custom GPT instructions + Actions/OpenAPI; Apps SDK where preview accepted | MCP via Apps SDK developer mode / app model | official-docs-backed-preview-for-apps |
| OpenAI Codex | `repo-present-validation-required` | AGENTS.md, .codex-plugin/, instructions/ | AGENTS.md + skill-compatible docs/scripts + optional MCP docs server | MCP for developer docs/live APIs | official-docs-backed-partial |
| GitHub Copilot Web | `planned-research-backed` | .github/, AGENTS.md, instructions/ | repository instructions + AGENTS.md + skills/custom agents where available | GitHub MCP / Actions / Apps integration | official-docs-backed |
| GitHub Copilot CLI | `repo-present-validation-required` | .agents/plugins, .github/, skills/ | Copilot CLI skills | MCP for live GitHub/stateful systems | official-docs-backed |
| OpenCode | `repo-present-validation-required` | .opencode/, .opencode-plugin/, opencode.json, opencode-setup/ | OpenCode skills + plugins + instructions | MCP for live systems | official-docs-backed |
| Gemini CLI | `repo-present-validation-required` | GEMINI.md, instructions/, skills/ | Gemini extensions + commands + context files; skill wrapper scripts where possible | MCP servers in gemini-extension.json/settings | official/open-source-docs-backed |
| Cursor Editor | `repo-present-validation-required` | .cursor/rules, AGENTS.md, mcp/, skills/ | rules + AGENTS.md + skill-compatible CLI/docs | MCP configured project/global/nested | official-docs-backed |
| Cursor Agent CLI/Web | `repo-present-validation-required` | .cursor/rules, AGENTS.md, mcp/ | non-interactive CLI + JSON/stream-json + rules/AGENTS.md | MCP with shared editor config | official-docs-backed |
| Antigravity | `repo-present-experimental-contracts-unverified` | .antigravity/rules | rules/instructions only until official stable extension docs are verified | none until authoritative MCP/skills/plugin contract confirmed | experimental/unverified |
| Perplexity Desktop | `repo-present-experimental-contracts-unverified` | .perplexity/skills | skill-like docs/instructions if client supports them; otherwise no generated config writes | Perplexity MCP server as service integration, not Desktop extension contract | partial/unverified-desktop |
| Cherry Studio | `repo-present-validation-required` | .cherry/presets | presets/assistants + MCP UI presets; skill-like prompts where possible | MCP through Cherry Studio UI/built-in uv/bun | official/community-docs-backed |
