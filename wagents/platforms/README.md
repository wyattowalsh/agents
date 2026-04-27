# Platform Adapter Interface Design

## Goal
Replace the 1663-line `scripts/sync_agent_stack.py` monolith with a modular
`wagents/platforms/` package where each platform lives in its own adapter file.

## Directory Structure

```
wagents/platforms/
├── __init__.py      # Registry: get_adapter("claude-code"), list_adapters()
├── base.py          # Abstract base + shared utilities
├── claude.py        # Claude Code: settings.json merge, hooks, desktop MCP
├── codex.py         # Codex: TOML config merge (placeholder)
├── copilot.py       # GitHub Copilot: settings, MCP, rules (placeholder)
├── cursor.py        # Cursor: standard client MCP JSON merge
├── gemini.py        # Gemini CLI: settings + antigravity MCP (placeholder)
├── opencode.py      # OpenCode: complex JSON merge, providers, plugins
└── vscode.py        # VSCode: repo-local standard MCP JSON
```

## Adapter Interface (`PlatformAdapter`)

Each adapter subclasses `PlatformAdapter` and implements a small, focused surface:

### 1. Identity
- `name: str` — kebab-case platform identifier (e.g., `"claude-code"`, `"opencode"`)

### 2. Availability Detection
- `is_available() -> bool` — default heuristic checks if any `home_config_paths()` exist. Override for custom detection.

### 3. Path Discovery
- `repo_config_paths() -> list[Path]` — repo-local generated files
- `home_config_paths() -> list[Path]` — user home config files

### 4. Pure Renderers (testable, side-effect free)
- `render_mcp(registry, fallbacks) -> dict` — convert normalized MCP registry into platform-native format
  - VSCode: `{"mcpServers": {...}}` with env placeholders
  - Claude Desktop / Cursor: `{"mcpServers": {...}}` with resolved env values
  - OpenCode: `{"mcp": {name: {type: "local"|"remote", command: [...], environment: {...}}}}`
  - Copilot: `{"mcpServers": {...}}` with `tools` allowlists and resolved env
- `render_hooks(hook_registry) -> dict | None` — convert normalized hook registry into platform-native format
  - Default: standard event-mapped command hooks
  - Gemini: maps to `BeforeAgent` / `BeforeTool` / `AfterTool` / `AfterAgent`
  - Copilot: custom format with `bash`, `cwd`, `timeoutSec`

### 5. Impure Sync Entrypoints
- `sync_repo(ctx, registry, hook_registry, policy) -> None` — write repo-local targets
- `sync_home(ctx, registry, policy, fallbacks, hook_registry) -> None` — write home directory targets

These are the **only** methods that perform I/O. They call into the pure renderers and use base-class helpers for merging.

## Shared Utilities (`base.py`)

The base class provides deterministic, reusable helpers extracted from the monolith:

- **JSON I/O**: `load_json()`, `dump_json()` (handles `//` line comments)
- **Env resolution**: `env_placeholder()`, `resolve_env_value()`, `replace_arg_placeholders()`
- **Server-map merging**: `merge_server_maps()` — preserves unknown/existing servers while overwriting managed ones
- **Hook merging**: `merge_hook_groups()` — strips previously-managed entries before appending new ones
- **Path merging**: `merge_unique_path_strings()` — dedupes instruction/skills paths by resolved absolute path
- **SyncContext**: tracks pending changes and gates actual writes behind `ctx.apply`

## Design Principles

1. **Extract patterns, don't rewrite** — The monolith's render/merge logic is lifted almost verbatim into adapter methods. A future refactor can migrate `sync_agent_stack.py` to call `get_adapter(name).sync_home(...)` instead of hardcoded functions.

2. **One file per platform** — Adding a new platform means creating one new file (`wagents/platforms/<name>.py`) and registering it in `__init__.py`.

3. **Pure + Impure separation** — `render_*` methods are pure and testable; `sync_*` methods handle I/O and config preservation.

4. **No forced uniformity** — Complex platforms (Codex TOML, OpenCode nested JSON, Copilot rules generation) keep their bespoke logic in their own adapter rather than being forced into a one-size-fits-all abstraction.

5. **Graceful degradation** — Adapters check `path.exists()` before reading; unavailable platforms simply skip their sync step.
