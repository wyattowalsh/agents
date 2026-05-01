# ChatGPT and Codex Ecosystem Surface

## Sources

- Apps SDK: https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk
- Developer mode/MCP apps: https://help.openai.com/articles/12584461
- GPT Actions: https://help.openai.com/en/articles/9442513-configuring-actions-in-gpts
- GPT Action auth: https://platform.openai.com/docs/actions/authentication
- Docs MCP: https://platform.openai.com/docs/docs-mcp
- Codex launch: https://openai.com/index/introducing-codex/
- Agents SDK: https://platform.openai.com/docs/guides/agents-sdk/

## Extension surfaces

- Custom GPT Actions via OpenAPI schema and auth.
- Apps SDK preview built on MCP with UI and backend logic.
- Codex cloud sandbox tasks and CLI/IDE MCP config.
- AGENTS.md as repository instruction surface.
- OpenAI Docs MCP as a high-value docs lookup MCP.
- Agents SDK for app-level agent orchestration, tracing, tools, handoffs.

## Planning implications

- ChatGPT Apps SDK is preview; registry tier should be `experimental` or `planned-research-backed` until repo owns an app.
- GPT Actions are API/plugin-like, not Agent Skills; use OpenAPI adapter.
- Codex should inherit `AGENTS.md` and OpenSpec status docs.
- Add OpenAI Docs MCP as optional docs lookup MCP, not general API actor.
