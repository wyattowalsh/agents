# Common FastMCP v3 Errors and Solutions

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

34 numbered errors when building FastMCP servers. Consult when debugging startup failures, connection issues, migration breakage, or unexpected tool behavior.

---

## Quick-Fix Lookup Table

| Symptom | Error # |
|---------|---------|
| Garbled JSON / parse errors on stdio | [#1](#1--stdout-pollution-breaks-stdio-transport) |
| "Connection refused" or protocol parse errors | [#2](#2--transport-mismatch) |
| "Unsupported protocol version" | [#3](#3--protocol-version-mismatch) |
| "Could not find a FastMCP server" | [#4](#4--missing-module-level-mcp-variable) |
| ImportError: `from mcp.server.fastmcp` | [#5](#5--v2-import-path-used) |
| ImportError on startup (circular) | [#6](#6--circular-imports) |
| `.disable()` on decorated function fails | [#7](#7--decorator-returns-function-not-object) |
| Code expects v2 decorator behavior | [#8](#8--fastmcp_decorator_mode-compat) |
| TypeError on `mount(prefix=)` | [#9](#9--mountprefix--mountnamespace) |
| Unknown parameter `tool_serializer` | [#10](#10--tool_serializer--toolresult) |
| Tool schema shows no parameters | [#11](#11--argskwargs-in-tool-signature) |
| LLM picks wrong tool or can't decide | [#12](#12--vague-or-missing-tool-descriptions) |
| Server hangs during tool call | [#13](#13--sync-blocking-in-async-tool) |
| Client truncates or crashes on output | [#14](#14--25k-character-tool-output) |
| ValueError on resource registration | [#15](#15--missing-uri-scheme) |
| Resource 404 or param is None | [#16](#16--template-parameter-name-mismatch) |
| Resource returns Python repr string | [#17](#17--dict-return-without-jsondumps) |
| Coroutine object instead of state value | [#18](#18--sync-get_stateset_state-must-await) |
| Serialization error on state | [#19](#19--non-json-serializable-state-value) |
| NoneType error calling tool directly | [#20](#20--context-in-non-mcp-calls) |
| `ctx.info()` returns coroutine object | [#21](#21--missing-await-on-ctx-methods) |
| API keys in LLM history and logs | [#22](#22--token-passthrough-in-tool-parameters) |
| Auth not working after upgrade | [#23](#23--auth-env-auto-load-removed) |
| Server accessible from network unexpectedly | [#24](#24--binding-0000-unintentionally) |
| Bugs caught only in production | [#25](#25--vibe-testing-manual-prompting-only) |
| Async tests skipped or error | [#26](#26--missing-asyncio_mode--auto) |
| Deprecation warnings, newer clients refuse SSE | [#27](#27--sse-for-new-project) |
| ModuleNotFoundError in production | [#28](#28--missing-deps-in-fastmcpjson) |
| TypeError on `ui=` parameter | [#29](#29--deprecated-ui-parameter-now-app) |
| Error with `task=True` on sync function | [#30](#30--sync-function-with-tasktrue) |
| ImportError for task modules | [#31](#31--missing-fastmcptasks-extra) |
| Deprecation warning on `enabled=False` | [#32](#32--using-enabledfalse-or-remove_tool) |
| TypeError with migration message on constructor | [#33](#33--deprecated-constructor-kwargs-removed-in-rc1) |
| Sensitive endpoint accessible without auth | [#34](#34--unprotected-custom-route-bypasses-mcp-auth) |

---

## Category 1: Protocol

### #1 — stdout pollution breaks stdio transport

**Cause:** `print()` or logging writes to stdout. In stdio mode, stdout IS the MCP protocol channel -- any extra bytes corrupt the JSON-RPC framing.

**Fix:**
```python
# BEFORE (broken)
print("Debug info")
logging.basicConfig()  # defaults to stderr, but print() still pollutes

# AFTER (correct)
await ctx.info("Debug info")           # in-protocol logging
logging.basicConfig(stream=sys.stderr) # explicit stderr
```

### #2 — Transport mismatch

**Cause:** Client expects stdio but server runs HTTP, or vice versa. The two transports speak completely different wire formats.

**Fix:**
```python
# Match transport on both sides

# Server: stdio (for local subprocess spawning)
mcp.run(transport="stdio")

# Server: HTTP (for networked clients)
mcp.run(transport="http")

# Client config must match:
# stdio  → command: ["uv", "run", "server.py"]
# http   → url: "http://localhost:8000/mcp"
```

### #3 — Protocol version mismatch

**Cause:** Client and server negotiate different MCP protocol versions. Older fastmcp releases may not support the latest protocol revision.

**Fix:**
```bash
# Upgrade fastmcp to the latest version
uv add --upgrade fastmcp

# Pin minimum in pyproject.toml
# "fastmcp>=3.0.0rc2"
```

---

## Category 2: Server Setup

### #4 — Missing module-level `mcp` variable

**Cause:** `FastMCP` instance created inside a function or `if __name__ == "__main__"` block. `fastmcp run` scans the module's global scope for a `FastMCP` instance.

**Fix:**
```python
# BEFORE (broken)
def main():
    mcp = FastMCP("my-server")
    mcp.run()

if __name__ == "__main__":
    main()

# AFTER (correct)
from fastmcp import FastMCP

mcp = FastMCP("my-server")  # module-level

@mcp.tool
async def hello() -> str:
    return "world"
```

### #5 — v2 import path used

**Cause:** Using the v2 import path `from mcp.server.fastmcp import FastMCP`. FastMCP v3 is a standalone package with its own top-level module.

**Fix:**
```python
# BEFORE (v2 — broken)
from mcp.server.fastmcp import FastMCP

# AFTER (v3 — correct)
from fastmcp import FastMCP
```

### #6 — Circular imports

**Cause:** `server.py` imports a module that imports `server.py` back, creating an import cycle that fails at startup.

**Fix:**
```python
# BEFORE (circular)
# server.py
from fastmcp import FastMCP
from . import handlers  # handlers.py imports mcp from server.py

# AFTER (correct) — pass mcp as argument or use lazy imports
# server.py
from fastmcp import FastMCP
mcp = FastMCP("my-server")

# handlers.py — accept mcp as parameter, do not import it
def register_tools(mcp):
    @mcp.tool
    async def my_tool() -> str:
        return "ok"
```

---

## Category 3: Decorators — v3 Breaking Changes

### #7 — Decorator returns function not object

**Cause:** In v3, `@mcp.tool` returns the original function, not a component object. Calling methods like `.disable()` on the decorated function raises `AttributeError`.

**Fix:**
```python
# BEFORE (v2 — broken in v3)
@mcp.tool
async def my_tool() -> str:
    return "hello"

my_tool.disable()  # AttributeError

# AFTER (v3 — correct)
@mcp.tool
async def my_tool() -> str:
    return "hello"

mcp.disable(keys={"tool:my_tool"})  # use server-level visibility API
mcp.enable(keys={"tool:my_tool"})   # re-enable when needed
```

### #8 — `FASTMCP_DECORATOR_MODE` compat

**Cause:** Existing code relies on v2 decorator behavior (returning component objects). During migration, the codebase has not been fully updated.

**Fix:**
```bash
# Transitional: set env var to get v2-style decorator returns
export FASTMCP_DECORATOR_MODE=v2

# Then migrate all call sites and remove the env var:
# Replace: decorated_func.some_method()
# With:    mcp.disable(keys={"tool:func_name"})
```

### #9 — `mount(prefix=)` → `mount(namespace=)`

**Cause:** v2 used the `prefix` parameter in `mount()`. v3 renamed it to `namespace`.

**Fix:**
```python
# BEFORE (v2 — broken in v3)
gateway.mount(sub_server, prefix="sub")

# AFTER (v3 — correct)
gateway.mount(sub_server, namespace="sub")
```

### #10 — `tool_serializer` → `ToolResult`

**Cause:** v2 had a `tool_serializer` parameter on tools. v3 replaces this with the `ToolResult` return type for custom serialization.

**Fix:**
```python
# BEFORE (v2 — broken in v3)
@mcp.tool(tool_serializer=custom_serializer)
async def my_tool() -> dict: ...

# AFTER (v3 — correct)
from fastmcp import ToolResult

@mcp.tool
async def my_tool() -> ToolResult:
    data = {"key": "value"}
    return ToolResult(content=[TextContent(type="text", text=json.dumps(data))])
```

---

## Category 4: Tools

### #11 — `*args`/`**kwargs` in tool signature

**Cause:** MCP requires a JSON Schema for every tool's parameters. Dynamic signatures like `*args` and `**kwargs` cannot produce a valid schema.

**Fix:**
```python
# BEFORE (broken — schema has no parameters)
@mcp.tool
async def query(**kwargs) -> str:
    table = kwargs["table"]
    ...

# AFTER (correct — explicit typed parameters)
@mcp.tool
async def query(
    table: str,
    filter_column: str | None = None,
    limit: int = 100,
) -> str: ...
```

### #12 — Vague or missing tool descriptions

**Cause:** No docstring or a minimal one-liner. The LLM cannot distinguish between similarly named tools and picks the wrong one or gives up.

**Fix:**
```python
# BEFORE (vague)
@mcp.tool
async def search(q: str) -> str:
    """Search."""
    ...

# AFTER (clear — WHAT / WHEN / RETURNS)
@mcp.tool
async def search(q: str) -> str:
    """Search the product catalog by natural language query.

    Use when the user asks about product availability, pricing,
    or specifications. Supports boolean operators (AND, OR, NOT).
    Returns JSON array of matching products with name, price, and SKU.
    """
    ...
```

### #13 — Sync blocking in async tool

**Cause:** Calling blocking I/O (`requests.get`, `time.sleep`, `subprocess.run`) on the async event loop thread. The entire server freezes until the call completes.

**Fix:**
```python
# BEFORE (broken — blocks event loop)
@mcp.tool
async def fetch(url: str) -> str:
    return requests.get(url).text

# AFTER (correct — async HTTP)
@mcp.tool
async def fetch(url: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.text

# AFTER (alternative — use asyncio.sleep instead of time.sleep)
await asyncio.sleep(1.0)  # not time.sleep(1.0)
```

### #14 — >25K character tool output

**Cause:** Returning full datasets, entire file contents, or raw API dumps. Clients may truncate, crash, or flood the LLM context window.

**Fix:**
```python
# BEFORE (broken — dumps everything)
@mcp.tool
async def list_records() -> str:
    return json.dumps(await db.fetch_all())

# AFTER (correct — paginate and cap output)
@mcp.tool
async def list_records(page: int = 1, page_size: int = 50) -> str:
    """List records with pagination. Returns max 50 per page."""
    records = await db.fetch_page(page, page_size)
    result = json.dumps(records[:page_size])
    if len(result) > 20000:
        return result[:20000] + "\n... [truncated, use narrower filters]"
    return result
```

---

## Category 5: Resources

### #15 — Missing URI scheme

**Cause:** Registering a resource with a bare path like `"settings"` instead of a proper URI with a scheme. FastMCP requires `scheme://path` format.

**Fix:**
```python
# BEFORE (broken — no scheme)
@mcp.resource("settings")
async def get_settings() -> str: ...

# AFTER (correct — scheme://path)
@mcp.resource("config://settings")
async def get_settings() -> str: ...
```

### #16 — Template parameter name mismatch

**Cause:** The URI template placeholder name (e.g., `{user_id}`) does not match the function argument name. FastMCP binds by name, not by position.

**Fix:**
```python
# BEFORE (broken — "user_id" vs "uid")
@mcp.resource("data://users/{user_id}")
async def get_user(uid: str) -> str: ...

# AFTER (correct — names match exactly)
@mcp.resource("data://users/{user_id}")
async def get_user(user_id: str) -> str: ...
```

### #17 — Dict return without json.dumps

**Cause:** Returning a raw Python dict from a resource. FastMCP calls `str()` on it, producing Python repr syntax (`{'key': 'value'}`) instead of valid JSON.

**Fix:**
```python
# BEFORE (broken — returns Python repr)
@mcp.resource("config://app")
async def get_config() -> str:
    return {"debug": True, "port": 8080}

# AFTER (correct — returns JSON string)
import json

@mcp.resource("config://app")
async def get_config() -> str:
    return json.dumps({"debug": True, "port": 8080})
```

---

## Category 6: State — v3

### #18 — Sync `get_state`/`set_state` (must `await`)

**Cause:** v3 made state methods async. Calling them without `await` returns a coroutine object instead of the actual value.

**Fix:**
```python
# BEFORE (broken — missing await)
@mcp.tool
async def get_counter(ctx: Context) -> str:
    count = ctx.get_state("count")       # returns <coroutine>
    ctx.set_state("count", count + 1)    # TypeError
    return str(count)

# AFTER (correct — await both calls)
@mcp.tool
async def get_counter(ctx: Context) -> str:
    count = await ctx.get_state("count") or 0
    await ctx.set_state("count", count + 1)
    return str(count)
```

### #19 — Non-JSON-serializable state value

**Cause:** Storing objects that cannot be serialized to JSON (database connections, file handles, custom classes) in MCP state without marking them.

**Fix:**
```python
# BEFORE (broken — db connection is not JSON-serializable)
await ctx.set_state("db", db_connection)

# AFTER (correct — use serializable=False for non-JSON values)
await ctx.set_state("db", db_connection, serializable=False)

# Or store only serializable references
await ctx.set_state("db_url", "postgresql://localhost/mydb")
```

---

## Category 7: Context

### #20 — Context in non-MCP calls

**Cause:** Calling a tool function directly in tests or application code. Outside MCP request handling, the `Context` object is not injected and is `None`.

**Fix:**
```python
# BEFORE (broken — ctx is None when called directly)
@mcp.tool
async def my_tool(query: str, ctx: Context) -> str:
    await ctx.info("Processing...")  # NoneType error
    ...

# AFTER (correct — make ctx optional)
@mcp.tool
async def my_tool(query: str, ctx: Context | None = None) -> str:
    if ctx:
        await ctx.info("Processing...")
    ...
```

### #21 — Missing `await` on ctx methods

**Cause:** In v3, context logging and state methods (`ctx.info()`, `ctx.warning()`, `ctx.report_progress()`) are async. Calling without `await` produces a coroutine object and the method appears to silently fail.

**Fix:**
```python
# BEFORE (broken — returns coroutine, no log emitted)
@mcp.tool
async def my_tool(ctx: Context) -> str:
    ctx.info("Starting")
    ctx.report_progress(50, 100)
    return "done"

# AFTER (correct — await every ctx method)
@mcp.tool
async def my_tool(ctx: Context) -> str:
    await ctx.info("Starting")
    await ctx.report_progress(50, 100)
    return "done"
```

---

## Category 8: Auth — v3

### #22 — Token passthrough in tool parameters

**Cause:** Tool accepts API keys or secrets as regular parameters. These values flow through the LLM, appear in conversation history, and get logged in MCP traces.

**Fix:**
```python
# BEFORE (broken — secret in tool params)
@mcp.tool
async def call_api(query: str, api_key: str) -> str:
    return httpx.get(URL, headers={"Authorization": api_key}).text

# AFTER (correct — read from environment)
@mcp.tool
async def call_api(query: str) -> str:
    api_key = os.environ["API_KEY"]
    return httpx.get(URL, headers={"Authorization": f"Bearer {api_key}"}).text
```

### #23 — Auth env auto-load removed

**Cause:** v2 automatically loaded auth configuration from environment variables. v3 requires explicit auth provider configuration -- the implicit behavior was removed.

**Fix:**
```python
# BEFORE (v2 — worked implicitly)
mcp = FastMCP("my-server")  # auto-loaded OAUTH_* env vars

# AFTER (v3 — configure auth explicitly)
from fastmcp.server.auth import OAuthProvider

auth = OAuthProvider(
    client_id=os.environ["OAUTH_CLIENT_ID"],
    client_secret=os.environ["OAUTH_CLIENT_SECRET"],
    authorize_url="https://provider.com/authorize",
    token_url="https://provider.com/token",
)
mcp = FastMCP("my-server", auth=auth)
```

### #24 — Binding `0.0.0.0` unintentionally

**Cause:** Server binds to all network interfaces, making it accessible from the local network. For dev servers with no auth, this is a security risk.

**Fix:**
```python
# BEFORE (broken — exposed to network)
mcp.run(transport="http", host="0.0.0.0")

# AFTER (correct — local dev uses loopback)
mcp.run(transport="http", host="127.0.0.1", port=8000)

# Use 0.0.0.0 ONLY inside Docker or behind a reverse proxy with auth
```

---

## Category 9: Testing

### #25 — Vibe testing (manual prompting only)

**Cause:** No automated test suite. Bugs are caught by manually prompting an LLM and eyeballing the output -- zero reproducibility, zero regression coverage.

**Fix:**
```python
# Write real tests with fastmcp.Client
import pytest
from fastmcp import Client

async def test_my_tool():
    async with Client(mcp) as client:
        result = await client.call_tool("my_tool", {"query": "test"})
        assert result.data is not None  # verify non-empty response
        assert not result.is_error
```

### #26 — Missing `asyncio_mode = "auto"`

**Cause:** pytest does not automatically handle async test functions. Without the asyncio mode config, async tests are silently skipped or raise errors.

**Fix:**
```toml
# Add to pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

```bash
# Install the plugin
uv add --dev pytest-asyncio
```

---

## Category 10: Deployment

### #27 — SSE for new project

**Cause:** Using the deprecated SSE transport for a new server. Newer MCP clients may refuse to connect, and SSE will be removed in a future release.

**Fix:**
```python
# BEFORE (deprecated)
mcp.run(transport="sse")

# AFTER (correct — use streamable HTTP)
mcp.run(transport="http")
```

### #28 — Missing deps in `fastmcp.json`

**Cause:** Dependencies installed locally (e.g., via `uv add`) but not declared in the `fastmcp.json` environment config. Production deployment finds only the base fastmcp package.

**Fix:**
```jsonc
// fastmcp.json — declare ALL runtime dependencies
{
  "command": "uv",
  "args": ["run", "--with", "fastmcp", "fastmcp", "run", "server.py"],
  "environment": {
    "dependencies": [
      "fastmcp>=3.0.0rc2",
      "httpx>=0.27",
      "beautifulsoup4>=4.12"
    ]
  }
}
```

### #29 — Deprecated `ui=` parameter (now `app=`)

**Cause:** The `ui` constructor parameter was renamed to `app` in rc1. Using `ui=` raises a `TypeError` with a migration hint.

**Fix:**
```python
# BEFORE (rc0 — broken in rc1+)
from fastmcp import FastMCP
mcp = FastMCP("my-server", ui=UIConfig(enabled=True))

# AFTER (rc1+ — correct)
from fastmcp import FastMCP
from fastmcp.server import AppConfig

mcp = FastMCP("my-server", app=AppConfig(enabled=True))
# or using a dict:
mcp = FastMCP("my-server", app={"enabled": True})
```

---

## Category 11: Background Tasks

### #30 — Sync function with `task=True`

**Cause:** Background tasks require async functions. Passing a sync function with `task=True` raises an error because the task runner expects an awaitable.

**Fix:**
```python
# BEFORE (broken — sync function)
@mcp.tool(task=True)
def long_running_job(data: str) -> str:
    time.sleep(60)
    return "done"

# AFTER (correct — async function)
@mcp.tool(task=True)
async def long_running_job(data: str) -> str:
    await asyncio.sleep(60)
    return "done"
```

### #31 — Missing `fastmcp[tasks]` extra

**Cause:** The tasks feature requires additional dependencies shipped as an optional extra. Without it, importing task-related modules fails.

**Fix:**
```bash
# BEFORE (broken — base install only)
uv add "fastmcp>=3.0.0rc2"

# AFTER (correct — include tasks extra)
uv add "fastmcp[tasks]>=3.0.0rc2"
```

---

## Category 12: Visibility — v3

### #32 — Using `enabled=False` or `remove_tool()`

**Cause:** v2 patterns for controlling tool visibility (`enabled=False` on decorator, `mcp.remove_tool()`) are removed in v3. Using them raises deprecation warnings or `TypeError`.

**Fix:**
```python
# BEFORE (v2 — broken in v3)
@mcp.tool(enabled=False)
async def admin_tool() -> str: ...

mcp.remove_tool("admin_tool")

# AFTER (v3 — correct visibility API)
@mcp.tool(tags={"admin"})
async def admin_tool() -> str: ...

mcp.disable(keys={"tool:admin_tool"})  # hide by key
mcp.disable(tags={"admin"})            # hide by tag
mcp.enable(keys={"tool:admin_tool"})   # re-enable
```

### #33 — Deprecated constructor kwargs removed in rc1

**Cause:** 16 v2 constructor keyword arguments (`host`, `port`, `debug`, `log_level`, `on_duplicate`, etc.) were removed in rc1. Passing them raises `TypeError` with a migration message.

**Fix:**
```python
# BEFORE (v2 — broken in rc1+)
mcp = FastMCP(
    "my-server",
    host="0.0.0.0",
    port=8080,
    debug=True,
    log_level="DEBUG",
)

# AFTER (rc1+ — use CLI flags or ASGI config)
mcp = FastMCP("my-server")

# Set host/port via CLI:
#   fastmcp run server.py --host 0.0.0.0 --port 8080

# Set log level via environment:
#   FASTMCP_LOG_LEVEL=DEBUG fastmcp run server.py

# Or deploy as ASGI app with uvicorn directly
```

---

## Category 13: Custom Routes

### #34 — Unprotected custom route (bypasses MCP auth)

**Cause:** `@mcp.custom_route()` adds an HTTP endpoint outside the MCP protocol layer. MCP OAuth protects only the `/mcp` endpoint -- custom routes receive no automatic auth.

**Fix:**
```python
# BEFORE (broken — no auth on custom route)
@mcp.custom_route("/api/data", methods=["GET"])
async def get_data(request):
    return JSONResponse(await db.fetch_all())  # wide open

# AFTER (correct — manually verify auth in route handler)
@mcp.custom_route("/api/data", methods=["GET"])
async def get_data(request):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not await verify_token(token):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return JSONResponse(await db.fetch_all())
```
