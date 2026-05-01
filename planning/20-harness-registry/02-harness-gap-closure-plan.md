# Harness Gap Closure Plan

## Objective

Close planning gaps across Claude Desktop, Claude Code, ChatGPT, Codex, GitHub Copilot Web, GitHub Copilot CLI, OpenCode, Gemini CLI, Antigravity, Perplexity Desktop, Cherry Studio, Cursor Editor, Cursor Agent Web, and Cursor Agent CLI.

## Gap Closure Waves

### Wave 1: Normalize Surface Names

Output: canonical harness IDs and aliases.

- `claude-code`
- `claude-desktop`
- `chatgpt`
- `codex`
- `github-copilot-web`
- `github-copilot-cli`
- `opencode`
- `gemini-cli`
- `antigravity`
- `cursor-editor`
- `cursor-agent-web`
- `cursor-agent-cli`
- `perplexity-desktop`
- `cherry-studio`
- `crush` if retained in supported surfaces

Acceptance criteria: registry fragments do not collapse desktop/cloud/CLI/editor variants unless a fixture proves shared behavior.

### Wave 2: Evidence And Docs Ledger

Output: one source ledger entry per harness.

Each entry must record:

- First-party docs URL or `llms.txt` attempt.
- Repo-observed files.
- Global config paths, if any.
- Generated surfaces, if any.
- Merge/symlink mode, if any.
- Blind spots.
- Confidence cap.

Acceptance criteria: no lane can assign `validated` without fixture evidence and no lane can claim `latest` without current docs/source evidence.

### Wave 3: Projection Fixtures

Output: dry-run fixture definitions for each projection class.

Required fixture classes:

- Instructions projection.
- Skills projection.
- MCP projection.
- Plugin/extension projection.
- Hook/guard projection.
- Config merge projection.
- Rollback projection.

Acceptance criteria: each fixture has input, expected output, forbidden output, rollback, and redaction requirements.

### Wave 4: Safety And Quarantine

Output: config safety and quarantine rules.

Required coverage:

- Desktop app config edits require preview, backup, rollback, redaction, and user approval.
- Credential bridges, auth reuse, proxy/account sharing, browser profile access, and offensive tooling route to `agents-c15-security-quarantine`.
- MCP servers with credentials require secrets model, transport model, sandbox model, and smoke fixture.

### Wave 5: Docs Truth And UX

Output: generated docs ownership and user-facing install/update flows.

Required coverage:

- README and docs support matrices generated from registry fragments.
- Installation commands surfaced only for supported adapters.
- Experimental harnesses clearly labeled and never presented as validated.
- UX groups surfaces by user intent: coding harness, desktop app, web/cloud agent, terminal CLI, plugin/extension, MCP/live state.

## Per-Harness Required Additions

| Harness Surface | Missing Plan Detail | Required Addition |
|---|---|---|
| Claude Code | Plugin, skills, hooks, MCP, OpenSpec artifacts are present but need unified fixture contract. | Add Claude Code fixture matrix and rollback note. |
| Claude Desktop | Desktop MCP merge exists but support is not separated from Claude Code. | Add Claude Desktop MCP-first fragment and no-skill-projection caveat. |
| ChatGPT | App/desktop/MCP connector behavior is under-specified. | Add ChatGPT connector/app surface research checklist and Apps SDK boundary. |
| Codex | Plugin and config surfaces exist; ChatGPT relation needs boundary. | Split Codex plugin/config from ChatGPT app/connector support. |
| Copilot Web | Web/coding-agent surface needs no-fabricated-skills caveat. | Add support-tier caveats and prompt/instruction fixture. |
| Copilot CLI | CLI config and skills/MCP behavior need separate verification. | Add CLI-specific config/MCP fixture and blind spots. |
| OpenCode | Strong surface coverage but plugin/DCP/model-neutral rules need central fixture. | Add OpenCode policy fixture and plugin placement tests. |
| Gemini CLI | Needs explicit bridge from `GEMINI.md` and generated artifacts. | Add Gemini projection fragment and OpenSpec wrapper fixture. |
| Antigravity | Needs first-party-vs-repo-observed separation. | Add Antigravity caveat fragment and docs/source requirement. |
| Cursor Editor | Needs explicit editor rules/skills/MCP fixture. | Add Cursor Editor fragment. |
| Cursor Agent Web | Currently blind-spot. | Add planned-research-backed fragment, no install claims. |
| Cursor Agent CLI | Currently blind-spot. | Add planned-research-backed fragment, no install claims. |
| Perplexity Desktop | Requested but unverified. | Add experimental fragment and docs/source lookup task. |
| Cherry Studio | Config/import surfaces exist but not planned in detail. | Add experimental MCP import/export fragment. |
| Crush | Present in sync manifest and bundle but not user-highlighted. | Decide retain, experimental, or unsupported in registry core. |

## Plan Gaps Now Filled By Markdown Artifacts

- `planning/20-harness-registry/00-expanded-harness-surface-map.md` establishes the cross-harness surface map.
- `planning/20-harness-registry/01-harness-projection-contract.md` defines how canonical assets project to harness surfaces.
- `planning/20-harness-registry/02-harness-gap-closure-plan.md` defines closure waves and per-harness missing details.

## Remaining Non-Markdown Work

These remain blocked while plan mode is active:

- Registry schema updates for distinct Cursor Agent Web/CLI and ChatGPT surfaces.
- JSON support-tier fragments.
- Fixture files and code-backed validation.
- Docs generation and README regeneration.
- Commit creation.
