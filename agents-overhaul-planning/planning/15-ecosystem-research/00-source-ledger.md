# Source Index

Generated: `2026-05-01T07:19:13Z`

## Authoritative and ecosystem sources

### agentskills_spec
- Title: Agent Skills Specification
- URL: https://agentskills.io/specification
- Notes: Defines SKILL.md, frontmatter, scripts/references/assets, progressive disclosure, validation.

### antigravity_google_blog
- Title: Google Developers Blog: Antigravity
- URL: https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/
- Notes: Antigravity combines Editor View and Manager surface; agents operate across editor, terminal, browser and produce artifacts.

### awesome_agent_skills
- Title: skillmatic-ai/awesome-agent-skills
- URL: https://github.com/skillmatic-ai/awesome-agent-skills
- Notes: Curated resources for Agent Skills.

### awesome_copilot
- Title: Awesome GitHub Copilot skills
- URL: https://awesome-copilot.github.com/skills/
- Notes: Community-created catalog with hundreds of Copilot agent skills.

### awesome_mcp_abordage
- Title: abordage/awesome-mcp
- URL: https://github.com/abordage/awesome-mcp
- Notes: Automated, curated, ranked MCP list updated daily with GitHub activity metrics.

### cherry_mcp_auto
- Title: Cherry Studio automatic MCP install
- URL: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/auto-install
- Notes: Auto-install requires v1.1.18+ and is currently testing-phase.

### cherry_mcp_config
- Title: Cherry Studio MCP config
- URL: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/config
- Notes: Cherry MCP UI can configure stdio servers with command uvx and args.

### cherry_mcp_install
- Title: Cherry Studio MCP environment install
- URL: https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/install
- Notes: Cherry uses built-in uv and bun in ~/.cherrystudio/bin rather than system installs.

### claude_code_hooks
- Title: Claude Code hooks
- URL: https://code.claude.com/docs/en/hooks
- Notes: Documents hook event types and command/http/mcp_tool/prompt/agent hook behavior.

### claude_code_plugins
- Title: Claude Code plugins
- URL: https://code.claude.com/docs/en/plugins
- Notes: Plugins bundle commands, agents, hooks, skills, MCP servers, LSP servers, monitors.

### claude_code_skills
- Title: Claude Code skills
- URL: https://docs.claude.com/en/docs/claude-code/skills
- Notes: Defines personal/project/plugin skills, model invocation, allowed-tools, team sharing.

### codex_launch
- Title: OpenAI Codex launch
- URL: https://openai.com/index/introducing-codex/
- Notes: Codex runs tasks in cloud sandbox environments and can perform many tasks in parallel.

### crewai_skills
- Title: CrewAI Skills
- URL: https://docs.crewai.com/en/skills
- Notes: CrewAI publishes official skill pack on skills.sh and installs via npx skills add crewaiinc/skills.

### cursor_background
- Title: Cursor background agents
- URL: https://docs.cursor.com/en/background-agents
- Notes: Background agents run in isolated Ubuntu machines, use GitHub integration, environment.json, encrypted secrets, and auto-run commands.

### cursor_background_api
- Title: Cursor Background Agents API
- URL: https://docs.cursor.com/background-agent/api/overview
- Notes: Beta API for programmatically creating/managing background agents; up to 256 active agents per API key.

### cursor_cli
- Title: Cursor CLI docs
- URL: https://docs.cursor.com/en/cli
- Notes: Cursor CLI supports interactive and non-interactive terminal agents.

### cursor_cli_using
- Title: Cursor CLI usage
- URL: https://docs.cursor.com/en/cli/using
- Notes: CLI reads MCP config, rules, AGENTS.md and CLAUDE.md, supports --output-format json/text.

### cursor_mcp_cli
- Title: Cursor CLI MCP
- URL: https://docs.cursor.com/cli/mcp
- Notes: cursor-agent mcp list/list-tools/login/disable and shared editor/CLI config.

### gemini_extensions
- Title: Gemini CLI extensions
- URL: https://google-gemini.github.io/gemini-cli/docs/extensions/
- Notes: Gemini extensions package prompts, MCP servers, custom commands; workspace config takes precedence.

### gemini_extensions_getting_started
- Title: Gemini CLI extension getting started
- URL: https://google-gemini.github.io/gemini-cli/docs/extensions/getting-started-extensions.html
- Notes: gemini extensions new/install/update flows and gemini-extension.json structure.

### gemini_mcp_config
- Title: Gemini CLI MCP configuration
- URL: https://gemini-cli.xyz/docs/en/get-started/configuration
- Notes: mcpServers support command/url/httpUrl precedence and tool name conflict prefixing.

### github_copilot_agent_config
- Title: GitHub custom agents configuration reference
- URL: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- Notes: Documents YAML frontmatter, tool selection, MCP server config, secret syntax, public-preview caveats.

### github_copilot_custom_agents
- Title: GitHub Copilot custom agents docs
- URL: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-custom-agents
- Notes: Defines repo and org/enterprise custom agent profile locations and cross-surface usage.

### github_copilot_skills
- Title: GitHub Copilot agent skills docs
- URL: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-skills
- Notes: Defines project/personal skill locations, gh skill preview/install/update/publish, pinning, warning about unverified skills.

### google_gemini3_antigravity
- Title: Google Gemini 3 launch with Antigravity
- URL: https://blog.google/products-and-platforms/products/gemini/gemini-3/
- Notes: Gemini 3 announcement states Antigravity gives agents direct access to editor, terminal, browser and task-oriented operation.

### langfuse
- Title: Langfuse observability docs
- URL: https://langfuse.com/docs/observability/overview
- Notes: LLM tracing captures prompts, responses, token usage, latency, tools, retrieval steps; async SDK export.

### mcp_authorization
- Title: MCP authorization
- URL: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- Notes: HTTP authorization is optional but OAuth 2.1-based when supported; stdio should retrieve credentials from environment.

### mcp_directory
- Title: MCP.Directory awesome MCP servers
- URL: https://mcp.directory/awesome-mcp-servers
- Notes: Curated category directory for browser, DB, search, developer tools, cloud, security, productivity.

### mcp_registry
- Title: Official MCP Registry
- URL: https://modelcontextprotocol.io/registry/about
- Notes: Official registry preview; breaking changes/data resets possible; server.json metadata, namespace verification.

### mcp_scan
- Title: Invariant MCP-Scan
- URL: https://explorer.invariantlabs.ai/docs/mcp-scan/
- Notes: Scans MCP configs for prompt injection, tool poisoning, rug pulls, cross-origin escalation; quickstart uvx mcp-scan@latest.

### mcp_transports
- Title: MCP transports
- URL: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- Notes: MCP uses JSON-RPC over stdio and Streamable HTTP; clients should support stdio where possible; Streamable HTTP security warnings.

### openai_agents_sdk
- Title: OpenAI Agents SDK
- URL: https://platform.openai.com/docs/guides/agents-sdk/
- Notes: Agents SDK supports tools, handoffs, streaming, and tracing.

### openai_apps_sdk
- Title: OpenAI Apps SDK help
- URL: https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk
- Notes: Apps SDK is preview, built on MCP, enables ChatGPT app UI and logic.

### openai_docs_mcp
- Title: OpenAI Docs MCP
- URL: https://platform.openai.com/docs/docs-mcp
- Notes: Documents public OpenAI developer docs MCP server and Codex/Cursor/VS Code installation examples.

### openai_gpt_actions
- Title: OpenAI GPT Actions configuration
- URL: https://help.openai.com/en/articles/9442513-configuring-actions-in-gpts
- Notes: Actions use OpenAPI schema and auth modes none/API key/OAuth; GPTs use apps or actions but not both.

### opencode_skills
- Title: OpenCode skills
- URL: https://opencode.ai/docs/skills
- Notes: OpenCode discovers .opencode/skills, .claude/skills, .agents/skills, global config equivalents.

### openspec
- Title: OpenSpec official site
- URL: https://openspec.dev/
- Notes: OpenSpec organizes changes as proposal.md, design.md, tasks.md, specs/ deltas.

### otel_genai
- Title: OpenTelemetry GenAI semantic conventions
- URL: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Notes: GenAI semantic conventions are development status; include metrics/spans/events and MCP semconv links.

### perplexity_local_mcp
- Title: Perplexity local and remote MCPs
- URL: https://www.perplexity.ai/help-center/en/articles/11502712-local-and-remote-mcps-for-perplexity
- Notes: Local MCP available for macOS Mac App Store app; remote MCP coming soon; helper app required.

### perplexity_mcp_server
- Title: Perplexity MCP server
- URL: https://docs.perplexity.ai/guides/mcp-server
- Notes: Perplexity MCP server offers one-click Cursor/VS Code install and manual API-key setup.

### phoenix
- Title: Arize Phoenix docs
- URL: https://arize.com/docs/phoenix
- Notes: Phoenix provides tracing, evaluation, prompt engineering, datasets/experiments on OpenTelemetry/OpenInference.

### pulsemcp
- Title: PulseMCP server directory
- URL: https://www.pulsemcp.com/servers
- Notes: Large MCP server directory with filters/classifications and usage-signal estimates.

### skills_sh
- Title: skills.sh documentation
- URL: https://skills.sh/docs
- Notes: Documents npx skills add, leaderboard, telemetry, security caveats.
