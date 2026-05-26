# Validation Matrix

| Surface                 | Validation                                                                                                                         |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| External Golang skills  | `npx skills add https://github.com/samber/cc-skills-golang --list`; install command exit status; installed skill spot-checks       |
| NotebookLM skill        | `npx skills add https://github.com/nghyane/opencode-plugin-notebooklm --list`; install command exit status; `nlm-index` spot-check |
| OpenCode runtime config | JSON parse; plugin order check; `opencode-websearch-cited@latest` last                                                             |
| OpenCode TUI config     | JSON parse; `opencodeBar` registered only in `tui.json`                                                                            |
| OpenSpec                | `uv run wagents openspec validate`                                                                                                 |
