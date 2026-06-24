# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| Skills CLI discovery | `npx skills add --help` and related source-list/help commands | Supported target agent IDs are known | Use output to choose exact `-a` suffixes. |
| Harness discovery | `harness-master` review of requested harnesses | Supported and unsupported target surfaces are evidence-backed | Include desktop/web/CLI variants where observable. |
| Docs generation | `uv run wagents docs generate` | Generated docs/site data include curated external entries | Required because docs surfaces change. |
| README generation | `uv run wagents readme` | README reflects generated external skill/install data | Do not hand-edit generated output. |
| Skill sync dry-run | `uv run wagents skills sync --dry-run` | Newly curated skills are either satisfied or reported as missing for supported adapters | Run before applying sync. |
| Skill sync apply | `uv run wagents skills sync --apply` | Approved missing curated installs are reconciled | Only run if dry-run findings match approved scope. |
| CTF installer dry-run | `bash scripts/install_ctf_tools.sh --dry-run all` from audited source | Installer actions are visible before execution | Report package managers and privileged prompts. |
| CTF installer | `bash scripts/install_ctf_tools.sh all` from audited source | CTF tooling setup completes or fails with actionable evidence | Run after dry-run unless blocked. |
| Asset validation | `uv run wagents validate` | Pass | Validates skills/agents/MCP metadata. |
| OpenSpec validation | `uv run wagents openspec validate` | Pass | Validates change artifacts. |
| Docs build | `cd docs && pnpm build` | Pass | Required because docs change. |
| Docs review | docs-steward subagent review | No blocking docs drift, or blockers are fixed/reported | Run after generation/build. |

## Blockers

- Plan mode currently permits only markdown/spec/documentation edits. Non-markdown source edits, live installs, installer execution, and generated output changes must wait until execution mode.

## Evidence To Capture

- Exact expanded target suffix or per-harness command set used.
- Read-only discovery established the execution-pass suffix as `-a antigravity claude-code codex cursor gemini-cli github-copilot opencode` for the requested installable harnesses.
- Desktop/app surfaces without distinct Skills CLI targets: `claude-desktop`, `chatgpt`, `perplexity-desktop`, and `cherry-studio`.
- Skills CLI unsupported-adapter messages, if any.
- Harness-master findings for requested harnesses without programmatic skill install support.
- CTF installer dry-run and execution output summary.
- Docs-steward findings and validation command results.
