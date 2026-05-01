# Installation

Install the package globally only when the user explicitly wants CLI usage and the `chrome-devtools` binary is missing.

```sh
npm i chrome-devtools-mcp@latest -g
chrome-devtools status
```

## Troubleshooting

- Command not found: ensure the global npm bin directory is in `PATH`, then restart the terminal.
- Permission errors: avoid `sudo`; use a Node version manager or configure npm to use a user-owned global directory.
- Old version running: run `chrome-devtools stop`, uninstall the old global package, then reinstall if the user approves.
