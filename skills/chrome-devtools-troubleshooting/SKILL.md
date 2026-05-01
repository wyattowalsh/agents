---
name: chrome-devtools-troubleshooting
description: 'Use when auditing Chrome DevTools MCP setup failures: initialization, connection, page listing, navigation, missing tools, or wrong Chrome profile. NOT for application debugging after MCP is healthy or unrelated browser automation.'
license: Apache-2.0
compatibility: 'Requires access to the user MCP configuration surface and `npx chrome-devtools-mcp@latest --help` for package diagnostics.'
metadata:
  author: Google LLC
  version: 0.23.0
---

# Chrome DevTools MCP Troubleshooting

Act as a configuration and connection troubleshooter. Find the active MCP config, identify the exact failure mode, and change only the canonical config source for the affected harness.

## Dispatch

| $ARGUMENTS | Action |
| --- | --- |
| Empty | Ask for the failing harness and exact error |
| Server initialization failure | Inspect MCP config, package availability, Node version, and launch flags |
| `list_pages` or `new_page` failure | Triage connection mode, Chrome profile, and remote debugging state |
| Missing tools | Check client read-only mode, `--slim`, and extension-category flags |
| Wrong or empty profile | Check user-data-dir, browser URL, auto-connect, and harness sandboxing |
| Extension tools missing | Check extension-category support and whether Chrome is launched rather than attached |

## Step 1: Find Configuration

Search for harness-appropriate config surfaces before asking the user for content. Common files include `.mcp.json`, `mcp.json`, `.vscode/mcp.json`, `.claude/settings.json`, `.gemini/settings.json`, and harness-specific global MCP configs.

Look for:

- Incorrect package names or commands.
- Typos in flags.
- Missing required environment variables.
- Conflicting launch modes such as `--autoConnect` and `--browserUrl`.
- Generated config drift from this repo's canonical `config/mcp-registry.json`.

## Step 2: Triage Known Symptoms

### `Could not find DevToolsActivePort`

This usually points to auto-connect behavior. Confirm the intended Chrome is running, remote debugging is enabled where required, and the harness can access the Chrome process. Do not immediately switch to `--browserUrl` without evidence.

### Empty Profile Or No Pages

Check whether the MCP server launched a fresh profile instead of using the expected profile. Verify `--user-data-dir` spelling and path against the shared default documented in `AGENTS.md`.

### Missing Tools

Check whether the MCP client is in read-only or plan mode, whether `--slim` is enabled, and whether extension tools require extension-category flags.

### Extension Issues

Verify extension-category tools are enabled. Some Chrome versions cannot load extensions when attaching to an existing browser instance; launching Chrome through MCP may be required.

## Step 3: Diagnostics

Run bounded diagnostics only:

```bash
npx -y chrome-devtools-mcp@latest --help
```

If deeper logs are needed, use an explicit log file path and avoid printing huge logs directly.

## Step 4: Formulate Fix

Recommend the smallest config change and specify whether it belongs in a canonical repo source, generated project surface, global merged surface, or manual UI-only setting. Preserve repo-specific invariants documented in `AGENTS.md` and `instructions/opencode-global.md`.

## Reference File Index

| File | Content | Read When |
| --- | --- | --- |
| `references/provenance.md` | Upstream source, commit, license, and adaptation notes | Before modifying this skill or auditing provenance |

## Critical Rules

1. Read the active MCP configuration before suggesting fixes.
2. Modify canonical repo sources instead of generated surfaces when this repo owns the config.
3. Preserve the OpenCode local launcher override unless it is explicitly disabled or replaced.
4. Do not recommend `--browserUrl` or `--autoConnect` changes without matching the exact failure mode.
5. Use bounded diagnostics and avoid printing large logs directly.

## Canonical Vocabulary

| Term | Meaning |
| --- | --- |
| MCP owner | The plugin, extension, repo MCP config, or manual UI setting that owns one server for a harness |
| Generated surface | Config produced from repo canonical sources and not edited directly |
| Canonical source | Repo file that should be changed before generated configs |
| Launch mode | Chrome DevTools MCP connection style such as launched profile, browser URL, or auto-connect |

## Validation Contract

Before declaring skill changes complete, run `uv run wagents validate`, `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools-troubleshooting`, and `uv run wagents package chrome-devtools-troubleshooting --dry-run`.
