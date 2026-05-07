# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| JSON configs | `jq empty opencode.json ~/.config/opencode/opencode.json ~/.config/opencode/tui.json .opencode/ocx.jsonc .ocx/receipt.jsonc` | All configs parse | Validates repo, live OpenCode, and OCX JSON. |
| Distribution tests | `uv run pytest tests/test_distribution_metadata.py` | Pass | Covers runtime plugin inventory, TUI-only exclusion rules, OCX component-file coverage, and distribution registry invariants. |
| Agent assets | `uv run wagents validate` | Pass | Ensures changed instructions/docs did not break asset validation. |
| OpenSpec | `uv run wagents openspec validate` | Pass | Ensures this change is structurally valid. |
| OCX | `ocx --version && test -f .opencode/plugin/worktree.ts && test -f .ocx/receipt.jsonc` | Pass | Confirms OCX CLI and KDCO worktree component are present. |
| WakaTime config | `python3 -c 'import configparser, os, stat, sys; p=os.path.join(os.environ.get("WAKATIME_HOME", os.path.expanduser("~")), ".wakatime.cfg"); c=configparser.ConfigParser(); c.read(p); sys.exit(0 if oct(stat.S_IMODE(os.stat(p).st_mode))[2:] == "600" and c.get("settings", "api_key", fallback="").strip() else 1)'` | Mode is `600`; key is present | Do not print the API key. |
| README | `uv run wagents readme --check` | Pass | Ensures generated README reflects the distribution text source. |
| Whitespace | `git diff --check` | Pass | Catches trailing whitespace and patch issues. |
| OpenCode startup | `opencode models anthropic` | No plugin load failures | Keep startup checks local. If debug logs are needed, redact auth/provider/telemetry output before sharing. Langfuse env warnings may be expected if keys are unset. Claude Auth may warn when local Claude credentials are expired; re-authenticate with `claude` before treating Anthropic provider startup as fully healthy. |

## Blockers

- None known.

## Deferred Checks

- Do not create scheduler jobs during validation.
- Do not create, switch, delete, or auto-commit worktrees during validation.
- Do not add CodeMCP workflow plugins or run broad CodeMCP setup unless the user explicitly re-approves local workflow-state artifacts.
- Do not run the Plannotator install script unless the user explicitly wants slash-command installation beyond npm plugin loading.
