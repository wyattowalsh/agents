# Gemini CLI Ecosystem Surface

## Sources

- Extensions: https://google-gemini.github.io/gemini-cli/docs/extensions/
- Getting started: https://google-gemini.github.io/gemini-cli/docs/extensions/getting-started-extensions.html
- MCP config: https://gemini-cli.xyz/docs/en/get-started/configuration

## Extension surfaces

- `.gemini/extensions/<name>/gemini-extension.json`.
- Extension-packaged prompts/context files.
- Extension-packaged MCP servers.
- Custom commands under extension `commands/`.
- Workspace config precedence over extensions.
- `excludeTools` to block specific tool/command usage.

## Planning implications

- Gemini extension adapter should generate `gemini-extension.json` from canonical registry.
- Skills may project as extension context, but no native Agent Skills support should be assumed unless verified.
- MCP server config must handle command/url/httpUrl precedence.
