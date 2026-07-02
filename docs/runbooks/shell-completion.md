# Shell Completion Runbook

Smoke-test and install instructions for `wagents` Typer shell completion.

## Install completion

Typer exposes completion through the root CLI:

```bash
# Zsh (default in self completion helper)
wagents --install-completion zsh

# Bash
wagents --install-completion bash

# Fish
wagents --install-completion fish
```

For repo development, prefer the self helper which prints the exact command:

```bash
uv run wagents self completion --shell zsh
```

Restart the shell or `source ~/.zshrc` after install.

## Smoke test

After installation, verify tab completion resolves subcommands:

```bash
# Should complete to subcommands like validate, docs, new, eval, hooks
wagents <TAB><TAB>

# Nested groups
wagents docs <TAB><TAB>
wagents new <TAB><TAB>
wagents eval <TAB><TAB>
```

Non-interactive smoke (no TTY required):

```bash
uv run wagents --help | rg -q "validate"
uv run wagents self completion --shell zsh | rg -q "install-completion"
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No completions after install | Restart shell; confirm completion script is sourced from rc file |
| Stale subcommand list | Re-run `wagents --install-completion <shell>` after CLI upgrades |
| `command not found: wagents` | Use `uv run wagents` in repo, or `uv tool install wagents --from git+https://github.com/wyattowalsh/agents` globally |

## CI note

Completion is user-local UX; CI validates CLI `--help` and command registration via pytest (`tests/test_cli_integration.py`, `tests/test_cli_failure_paths.py`). No completion install runs in GitHub Actions.
