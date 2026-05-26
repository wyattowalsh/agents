# Proposal

## Problem

The requested Golang skill bundle and OpenCode plugins are external, trust-bearing assets that affect global harness installs and repo-managed OpenCode runtime behavior. Applying them without a tracked change would make plugin ordering, provider options, and TUI-only configuration harder to audit later.

## Intent

Install the audited `samber/cc-skills-golang` bundle through the Skills CLI for all supported local tools, and configure the requested OpenCode plugins according to their upstream docs and this repo's OpenCode conventions.

## Scope

- Install all skills from `https://github.com/samber/cc-skills-golang` globally for the repo-approved local tool target set.
- Add runtime OpenCode plugins for NotebookLM, cited web search, insights, and Mermaid rendering.
- Keep `opencode-websearch-cited` last in the runtime plugin list and configure its required OpenAI model option.
- Install `opencodeBar` as a TUI-only plugin using a stable local checkout and live TUI config.
- Preserve unrelated dirty worktree changes and user-owned settings.

## Out Of Scope

- Promoting external skill contents into tracked `skills/` directories.
- Reading, printing, or storing NotebookLM cookies or other credentials.
- Running `curl | bash` installers.
- Reverting unrelated existing changes.
