# Change: Add Grok Harness Integration

## Why

Grok Build is documented as a supported harness but implementation was thin: MCP projection and skills inventory worked, while the platform adapter was a stub, there was no repo-owned policy template for `~/.grok/config.toml`, `wagents install -a grok` passed an unsupported Skills CLI agent id, bundle/registry omitted Grok, and home sync could not target Grok in isolation when unrelated OpenCode config drops blocked full home sync.

## What Changes

- Add OpenSpec contract for TOML ownership (`GROK_OWNED_*`), managed markers, blend vs replace merge semantics, and marker-less MCP reconciliation
- Add `config/grok-config.toml`, `instructions/grok-global.md`, and `config/grok-env.sh`
- Add `model_defaults.grok` in `tooling-policy.json` (default `grok-composer-2.5-fast`)
- Implement full `wagents/platforms/grok.py` adapter; delegate monolith sync; add `--platforms grok` on `sync_agent_stack.py`
- Fix `wagents install -a grok` via Claude Skills CLI alias with post-install mirror to `~/.grok/skills`
- Add `wagents grok doctor`, repo project skill inventory, tests, docs, and validation matrix

## Non-Goals

- Native Skills CLI `grok` adapter
- Subagent depth greater than 1
- Auto-editing user dotfiles outside managed merge
- Fixing unrelated OpenCode home `ConfigDropError` paths
