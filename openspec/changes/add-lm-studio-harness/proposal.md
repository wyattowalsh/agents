# Change: Add First-Class LM Studio Harness

## Why

LM Studio is installed and used locally as an MCP host (Cursor-compatible
`mcp.json`) and as a local OpenAI-compatible model server. The repo already
projects `local_llm_providers.lmstudio` into Codex/OpenCode, but does not treat
LM Studio as a first-class managed harness for registry → home `mcp.json` sync,
managed preset projection, surface discovery, or fixture-backed support claims.

## What Changes

- Add platform adapter `wagents/platforms/lm_studio.py` with home path resolution
  (`~/.lmstudio-home-pointer` then `~/.lmstudio`) and Cursor-compatible MCP merge.
- Default MCPHub projection: **remote-stdio** via `scripts/mcphub/remote-stdio.sh`
  (avoids undocumented header env expansion; avoids writing resolved bearer secrets).
- Register `lm-studio` across harness-surface, mcp-registry clients/ownership,
  plugin-extension registry, sync-manifest, RTK tier E, image-input optimizer,
  harness-fixture-support, and harness-master classify/discover.
- Add MCPHub launch wrapper `scripts/mcphub/wrappers/lm-studio`.
- Project managed instruction/agent presets and an optional repo-owned skill
  mirror for separately installed compatible community plugins, defaulting to none.
- Document that hooks, a native Skills CLI adapter, and global skill mirroring are unsupported.
- Fixture-backed tests for path resolution, render, merge, and registry metadata.

## Non-Goals

- Native Skills CLI adapter, direct Skills CLI installs, or installation of a
  compatible community plugin into LM Studio.
- Hooks, Plannotator, or RTK shell integration.
- Making LM Studio the default model for OpenCode/Codex.
- Project-local `.lmstudio/mcp.json` SSOT (app-global only).
- Live home `--apply` without operator approval after fixtures pass.
- Deeplink generation as primary sync path.
