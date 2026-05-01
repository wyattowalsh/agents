---
name: chrome-devtools-cli
description: 'Use when auditing, writing, or running bounded shell commands that drive Chrome DevTools through the `chrome-devtools` CLI. NOT for MCP tool-call workflows, broad browser QA, unattended package installation, or replacing harness MCP configuration.'
license: Apache-2.0
compatibility: 'Requires the `chrome-devtools` binary from chrome-devtools-mcp 0.23.0 or compatible version and Node.js 20.19.0, 22.12.0, or newer.'
metadata:
  author: Google LLC
  version: 0.23.0
---

# Chrome DevTools CLI

Use the `chrome-devtools` CLI for terminal-driven browser automation when the user explicitly needs shell commands or scripts. Prefer MCP tools directly when the current harness already exposes Chrome DevTools MCP tools.

## Dispatch

| $ARGUMENTS | Action |
| --- | --- |
| Empty | Ask what page or CLI task should be automated |
| CLI examples | Provide bounded `chrome-devtools <tool>` commands with expected outputs |
| Shell script request | Write a script that calls `chrome-devtools` commands and handles failures |
| First-time setup | Surface installation guidance from `references/installation.md`; do not install automatically |
| Large output | Use CLI output files or JSON parsing instead of printing huge snapshots or traces |
| Service lifecycle | Use `start`, `status`, and `stop` only when diagnosing the CLI service itself |

## Guardrails

- Do not run `npm i -g` or mutate global package state unless the user explicitly asks.
- Run `chrome-devtools <tool> --help` before using unfamiliar flags.
- Use `--output-format=json` when a script needs stable parsing.
- Do not read raw trace, screenshot, or heap snapshot artifacts into the context.
- Quote file paths and URLs in shell commands.

## Command Shape

```sh
chrome-devtools <tool> [arguments] [flags]
```

## Common Commands

```bash
chrome-devtools list_pages
chrome-devtools new_page "https://example.com"
chrome-devtools navigate_page --url "https://example.com"
chrome-devtools take_snapshot
chrome-devtools click "uid"
chrome-devtools fill "uid" "text"
chrome-devtools press_key "Enter"
chrome-devtools list_console_messages --types error
chrome-devtools list_network_requests --pageSize 50 --pageIdx 0
chrome-devtools lighthouse_audit --mode "navigation" --device "desktop"
chrome-devtools performance_start_trace true true --filePath "trace.json.gz"
chrome-devtools take_screenshot --fullPage true --filePath "page.png"
```

## Workflow

1. Verify the CLI exists with `chrome-devtools --help` or provide setup guidance if it does not.
2. Navigate or select a page.
3. Take a snapshot to obtain `uid`s.
4. Act with focused commands such as `click`, `fill`, `press_key`, or `upload_file`.
5. Verify with a fresh snapshot, console messages, network requests, or screenshot.

## Reference File Index

| File | Content | Read When |
| --- | --- | --- |
| `references/installation.md` | Optional global CLI install guidance and troubleshooting | The `chrome-devtools` binary is missing and the user wants CLI usage |
| `references/provenance.md` | Upstream source, commit, license, and adaptation notes | Before modifying this skill or auditing provenance |

## Critical Rules

1. Do not install or update global npm packages unless the user explicitly asks.
2. Prefer MCP tools directly unless the user specifically needs CLI commands or scripts.
3. Use `--help` before unfamiliar CLI flags.
4. Use JSON output for scripts that need stable parsing.
5. Keep trace, screenshot, and snapshot artifacts out of version control.

## Canonical Vocabulary

| Term | Meaning |
| --- | --- |
| CLI | The `chrome-devtools` executable installed from `chrome-devtools-mcp` |
| Tool command | A bounded `chrome-devtools <tool>` invocation |
| JSON output | Stable machine-readable CLI output for scripts |
| Service lifecycle | `start`, `status`, and `stop` commands for diagnosing the CLI service |

## Validation Contract

Before declaring skill changes complete, run `uv run wagents validate`, `uv run python skills/skill-creator/scripts/audit.py skills/chrome-devtools-cli`, and `uv run wagents package chrome-devtools-cli --dry-run`.
