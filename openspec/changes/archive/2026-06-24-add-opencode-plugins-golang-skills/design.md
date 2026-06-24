# Design

Use the smallest integration points already supported by each upstream project.

Runtime OpenCode plugins are added to `opencode.json` with `@latest` to preserve this repo's managed plugin convention. `opencode-websearch-cited` is placed last because its README explicitly warns that plugin ordering can affect auth flows.

The cited web search plugin requires `provider.<provider>.options.websearch_cited.model`; the existing OpenAI provider is the narrowest correct location because this repo already uses OpenAI as the primary OpenCode provider.

`opencodeBar` is not added to runtime `opencode.json` because upstream docs and OpenCode docs both distinguish TUI config from runtime config. It is installed from a local source checkout and registered in live `tui.json` with an absolute `file://` path.

NotebookLM authentication is left to the plugin's documented Chrome/CDP flow. No credential files are inspected or committed.
