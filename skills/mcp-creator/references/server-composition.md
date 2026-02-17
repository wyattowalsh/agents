# Composing and Mounting FastMCP v3 Servers

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

Patterns for combining multiple FastMCP servers, proxying remote endpoints, and
shaping components with providers and transforms.
Read when designing multi-server architectures or building gateway servers.

## 1. mount() -- Live Composition

`mount(server, namespace=)` creates a dynamic link between a parent and child
server. The parent delegates requests to the child at runtime. Tools on the
child become `{namespace}_{tool_name}` on the parent. Changes to the child
reflect immediately through the parent without restarting.

```python
from fastmcp import FastMCP

gateway = FastMCP("gateway")
weather = FastMCP("weather")
stocks = FastMCP("stocks")

@weather.tool
def get_forecast(city: str) -> str:
    """Return weather forecast for a city."""
    return f"Sunny in {city}"

@stocks.tool
def get_price(ticker: str) -> float:
    """Return current stock price."""
    return 142.50

# Mount with namespace prefix
# Clients see: weather_get_forecast, stocks_get_price
gateway.mount(weather, namespace="weather")
gateway.mount(stocks, namespace="stocks")
```

- Clients see child components as part of the parent.
- Namespace prevents name collisions (see Section 3).
- Most recently mounted server wins on name conflicts within the same namespace.
- Add tools to the child after mounting and they appear immediately.

## 2. import_server() -- Static Snapshot

`await main.import_server(server, namespace=)` performs a one-time copy of all
components from the child into the parent. No dynamic delegation occurs after
import. Later changes to the child are NOT reflected.

```python
weather = FastMCP("weather")

@weather.tool
def get_forecast(city: str) -> str:
    """Return weather forecast for a city."""
    return f"Sunny in {city}"

gateway = FastMCP("gateway")

# One-time copy -- must be awaited
await gateway.import_server(weather, namespace="weather")

# Adding tools to `weather` after this point has no effect on `gateway`
```

Use `import_server()` when you want a frozen, self-contained copy with no
runtime delegation overhead.

| Aspect | `mount()` | `import_server()` |
|--------|-----------|--------------------|
| Link type | Dynamic -- live forwarding | Static -- one-time copy |
| Update propagation | Reflected immediately | Not reflected after import |
| Performance | Runtime delegation overhead per request | No delegation overhead |
| Use case | Modular runtime composition, dev servers | Bundling finalized components, production snapshots |

## 3. Namespace Prefixing

When `namespace="api"` is applied (via `mount()` or `import_server()`), all
component names from the child are prefixed:

| Component | Pattern | Example |
|-----------|---------|---------|
| Tools | `{ns}_{name}` | `api_get_data` |
| Prompts | `{ns}_{name}` | `api_my_prompt` |
| Resources | `{scheme}://{ns}/{path}` | `data://api/info` |
| Templates | `{scheme}://{ns}/{id}` | `data://api/{id}` |

Without a namespace, names merge directly into the parent -- risk of collision.
The most recently mounted server takes precedence for conflicting names.

Always set `namespace=` in production to prevent accidental shadowing.

## 4. Proxy Mounting

Use `create_proxy()` to mount remote HTTP endpoints, local scripts, or npm/uvx
packages as if they were native FastMCP servers.

```python
from fastmcp import FastMCP
from fastmcp.server import create_proxy

gateway = FastMCP("gateway")

# Remote HTTP MCP server
gateway.mount(
    create_proxy("http://localhost:8001/mcp"),
    namespace="remote",
)

# Local Python script (runs as subprocess)
gateway.mount(
    create_proxy("./path/to/server.py"),
    namespace="local",
)

# npm package via config dict
npx_config = {
    "mcpServers": {
        "default": {
            "command": "npx",
            "args": ["@some/mcp-package"],
        }
    }
}
gateway.mount(create_proxy(npx_config), namespace="npm_pkg")

# uvx tool via config dict
uvx_config = {
    "mcpServers": {
        "default": {
            "command": "uvx",
            "args": ["tool-name"],
        }
    }
}
gateway.mount(create_proxy(uvx_config), namespace="uv_tool")
```

Latency implications:
- Local tools: ~1-2ms per call.
- HTTP-proxied servers: ~300-400ms per call due to network round-trip.
  This affects the entire parent server during `list_tools()` calls since
  proxied providers are queried sequentially.
- Each request gets its own isolated backend session by default.
- MCP features (sampling, logging, progress) are forwarded automatically.

## 5. FileSystemProvider

`FileSystemProvider(root=Path("./tools"), reload=True)` discovers decorated
functions from a directory tree of Python files, making them available as
tools, resources, and prompts without explicit registration.

```python
from pathlib import Path
from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

mcp = FastMCP("my-server", providers=[
    FileSystemProvider(
        root=Path(__file__).parent / "mcp",
        reload=True,  # dev only -- re-scans on every request
    )
])
```

Files use standalone decorators (not server-bound):

```python
# mcp/tools/search.py
from fastmcp.tools import tool

@tool
def search_docs(query: str) -> list[dict]:
    """Search documentation by keyword."""
    ...

# mcp/resources/config.py
from fastmcp.resources import resource

@resource("data://app-config")
def get_config() -> dict:
    """Return application configuration."""
    return {"debug": False}

# mcp/prompts/analysis.py
from fastmcp.prompts import prompt

@prompt
def analyze_data(topic: str) -> str:
    """Generate an analysis prompt for the given topic."""
    return f"Analyze the following topic in depth: {topic}"
```

Directory conventions (purely organizational -- any structure works):

```
mcp/
  tools/        # @tool functions
  resources/    # @resource functions
  prompts/      # @prompt functions
```

Scanning rules:
- Only `.py` files are scanned recursively.
- `__init__.py` and `__pycache__` are skipped.
- Private functions (names starting with `_`) are ignored.
- Failed imports log warnings but do not prevent server startup.
- `reload=True` re-imports changed files on every request. Use in development
  only -- disable in production for performance.

## 6. OpenAPI Integration

Two approaches exist for turning an OpenAPI spec into MCP tools. Choose based
on whether you need composability or convenience.

### Preferred (v3 idiomatic): OpenAPIProvider

Fits the provider architecture. Composable with transforms and other providers.
Use when building a larger server that combines multiple sources.

```python
import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import OpenAPIProvider

spec = httpx.get("https://api.example.com/openapi.json").json()
client = httpx.AsyncClient(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer TOKEN"},
)

provider = OpenAPIProvider(spec=spec, client=client)
mcp = FastMCP("api-server", providers=[provider])
```

### Convenience: FastMCP.from_openapi()

Creates a new FastMCP instance internally. Use when the OpenAPI server IS the
entire MCP server and no further composition is needed.

```python
import httpx
from fastmcp import FastMCP

spec = httpx.get("https://api.example.com/openapi.json").json()
client = httpx.AsyncClient(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer TOKEN"},
)

mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    name="api-server",
    timeout=30.0,
)
```

### RouteMap -- Control Endpoint Mapping

Use `RouteMap` to decide which endpoints become tools, resources, or get
excluded entirely:

```python
from fastmcp.server.openapi import RouteMap, MCPType

route_maps = [
    # GET endpoints under /public/ become resources (read-only data)
    RouteMap(methods=["GET"], pattern=r"^/public/.*", mcp_type=MCPType.RESOURCE),
    # Everything under /admin/ is excluded
    RouteMap(pattern=r"^/admin/.*", mcp_type=MCPType.EXCLUDE),
    # Exclude endpoints tagged "internal"
    RouteMap(tags={"internal"}, mcp_type=MCPType.EXCLUDE),
]

# With from_openapi
mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    route_maps=route_maps,
)

# Or with OpenAPIProvider
provider = OpenAPIProvider(spec=spec, client=client, route_maps=route_maps)
```

### Advanced Control

For fine-grained control beyond `RouteMap`:

```python
# route_map_fn -- custom function for endpoint classification
def classify_route(method: str, path: str, operation: dict) -> MCPType:
    if operation.get("deprecated"):
        return MCPType.EXCLUDE
    if method == "GET":
        return MCPType.RESOURCE
    return MCPType.TOOL

mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    route_map_fn=classify_route,
)

# mcp_names -- override tool/resource names
mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    mcp_names={"GET /users": "list_users", "POST /users": "create_user"},
)

# mcp_component_fn -- full control over component creation
def customize_component(method, path, operation, mcp_type):
    """Return a dict of overrides for the MCP component."""
    return {"description": f"[API] {operation.get('summary', '')}"}

mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=client,
    mcp_component_fn=customize_component,
)
```

## 7. FastAPI Conversion

`FastMCP.from_fastapi(app=)` converts a FastAPI application into an MCP server.
Set `operation_id` on FastAPI routes for clean, predictable tool names.

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI()

@app.get("/users", operation_id="list_users")
async def list_users(limit: int = 10):
    return [{"id": 1, "name": "Alice"}]

@app.post("/users", operation_id="create_user")
async def create_user(name: str):
    return {"id": 2, "name": name}

# Convert to MCP server -- tools are named list_users, create_user
mcp = FastMCP.from_fastapi(app=app)
```

Without `operation_id`, tool names are auto-generated from the HTTP method and
path (e.g., `get_users_users_get`), which is less readable. Always set
`operation_id` explicitly.

Accepts the same `route_maps`, `route_map_fn`, `mcp_names`, and
`mcp_component_fn` parameters as `from_openapi()`.

## 8. Custom Providers

Subclass `Provider` and implement the tool, resource, and prompt interfaces.
Return empty lists for component types you do not serve.

```python
from fastmcp.server.providers import Provider
from fastmcp.tools.tool import Tool
from mcp.types import CallToolResult, TextContent
from collections.abc import Sequence

class DatabaseToolProvider(Provider):
    """Serve tools backed by a database connection."""

    def __init__(self, db_url: str):
        self.db_url = db_url

    async def list_tools(self) -> Sequence[Tool]:
        """Return all tools this provider offers."""
        return [
            Tool.from_function(self.query_table),
            Tool.from_function(self.list_tables),
        ]

    async def get_tool(self, name: str) -> Tool | None:
        """Return a single tool by name, or None."""
        tools = {t.name: t for t in await self.list_tools()}
        return tools.get(name)

    async def call_tool(
        self, name: str, arguments: dict
    ) -> CallToolResult:
        """Execute the named tool with the given arguments."""
        tool = await self.get_tool(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        result = await tool.run(arguments)
        return result

    # Resource and prompt equivalents -- return empty if unused
    async def list_resources(self) -> Sequence:
        return []

    async def get_resource(self, uri: str):
        return None

    async def list_prompts(self) -> Sequence:
        return []

    async def get_prompt(self, name: str):
        return None

    # --- Actual tool implementations ---

    async def query_table(self, table: str, limit: int = 10) -> list[dict]:
        """Query rows from a database table."""
        ...

    async def list_tables(self) -> list[str]:
        """List all tables in the database."""
        ...
```

Register the provider at server construction:

```python
from fastmcp import FastMCP

mcp = FastMCP("db-server", providers=[
    DatabaseToolProvider(db_url="postgresql://localhost/mydb"),
])
```

## 9. Transform System

Transforms modify components as they flow from providers to clients. Apply at
server level (all providers) or provider level (single provider).

### Built-in Transforms

| Transform | Purpose |
|-----------|---------|
| `Namespace` | Prefix component names to prevent collisions |
| `ToolTransform` | Rename tools, modify descriptions, reshape arguments |
| `ResourcesAsTools` | Expose resources to tool-only clients |
| `PromptsAsTools` | Expose prompts to tool-only clients |
| `VersionFilter` | Filter components by version range |

### Custom Transform

Subclass `Transform` and override the methods you need. Two patterns:

- **Pure filter** (`list_tools`, `list_resources`, etc.): receive the full list,
  return a filtered/modified list.
- **Middleware** (`get_tool`, `get_resource`, etc.): receive a name and
  `call_next` callback, resolve or intercept.

```python
from fastmcp.server.transforms import Transform, GetToolNext
from fastmcp.tools.tool import Tool
from collections.abc import Sequence

class TagFilter(Transform):
    """Only expose tools matching required tags."""

    def __init__(self, required_tags: set[str]):
        self.required_tags = required_tags

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        # Pure filter -- return only matching tools
        return [t for t in tools if t.tags & self.required_tags]

    async def get_tool(self, name: str, call_next: GetToolNext) -> Tool | None:
        # Middleware -- call_next resolves, then validate
        tool = await call_next(name)
        return tool if tool and tool.tags & self.required_tags else None
```

Apply transforms:

```python
# Server-level -- applies to all providers
mcp.add_transform(TagFilter(required_tags={"public"}))

# Provider-level -- applies to one provider only
provider.add_transform(TagFilter(required_tags={"public"}))
```

Transforms stack in order added. First added = innermost (closest to provider).

### ToolTransform -- Rename, Hide Args, Set Defaults

Reshape mounted tools without modifying the source server:

```python
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig

mcp.add_transform(ToolTransform({
    "verbose_internal_data_fetcher": ToolTransformConfig(
        name="search",                    # rename the tool
        description="Search the knowledge base.",
        args={
            "internal_api_key": {          # hide and default an arg
                "hide": True,
                "default": "sk-xxx",
            },
            "verbose_query_string": {      # rename an arg
                "name": "query",
            },
        },
    ),
}))
```

Tool-level options:

| Option | Purpose |
|--------|---------|
| `name` | Rename the tool |
| `description` | Replace the description |
| `enabled` | Hide from clients (`False`) |
| `tags` | Override categorization tags |

Argument-level options:

| Option | Purpose |
|--------|---------|
| `name` | Rename a parameter |
| `description` | Replace parameter docs |
| `default` | Set a static default |
| `default_factory` | Dynamic default (requires `hide=True`) |
| `hide` | Remove from client schema |
| `required` | Force mandatory |
| `type` | Change parameter type |

## 10. Gateway Pattern

Full example combining local tools, mounted servers, remote proxies, and
visibility rules behind a single endpoint.

```python
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig

# --- Sub-servers ---

auth = FastMCP("auth")

@auth.tool
def verify_token(token: str) -> dict:
    """Verify an authentication token."""
    return {"valid": True, "user": "alice"}

analytics = FastMCP("analytics")

@analytics.tool(tags={"admin"})
def usage_report(days: int = 30) -> dict:
    """Generate usage report for the last N days."""
    return {"total_requests": 12345, "period_days": days}

# --- Gateway ---

gateway = FastMCP("api-gateway", instructions="Unified API access point.")

# Local tools defined directly on the gateway
@gateway.tool
def health_check() -> str:
    """Check gateway health."""
    return "ok"

# Mount local sub-servers
gateway.mount(auth, namespace="auth")
gateway.mount(analytics, namespace="analytics")

# Mount remote servers via proxy
gateway.mount(
    create_proxy("http://search-service:8001/mcp"),
    namespace="search",
)
gateway.mount(
    create_proxy("http://email-service:8002/mcp"),
    namespace="email",
)

# Reshape a proxied tool for clarity
gateway.add_transform(ToolTransform({
    "search_internal_query_v2": ToolTransformConfig(
        name="search_query",
        description="Search the document index.",
    ),
}))

# Hide admin tools from general access
gateway.disable(tags={"admin"})

# Run the gateway
gateway.run(transport="http", port=8000)
```

Clients connect to `http://localhost:8000/mcp` and see a unified tool surface
from all mounted servers, filtered by visibility rules. Tools are namespaced:
`auth_verify_token`, `analytics_usage_report`, `search_query`, `email_*`, and
the local `health_check`.

## 11. DRY Registration Pattern

Share tool definitions between auth-enabled and no-auth server entries using
a `common.py` module. Avoid duplicating decorator registrations.

```python
# common.py
from fastmcp import FastMCP

def register_all(mcp: FastMCP):
    """Register all tools on the given server instance."""

    @mcp.tool
    def search_docs(query: str, limit: int = 10) -> list[dict]:
        """Search documentation by keyword."""
        ...

    @mcp.tool
    def get_status() -> dict:
        """Return service status."""
        return {"status": "healthy"}
```

```python
# main.py -- production entry point with auth
from fastmcp import FastMCP
from common import register_all

mcp = FastMCP("my-service", auth=oauth_provider)
register_all(mcp)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

```python
# main_noauth.py -- dev/testing entry point without auth
from fastmcp import FastMCP
from common import register_all

mcp = FastMCP("my-service-dev")
register_all(mcp)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

This pattern keeps tool logic in one place. Change `common.py` and both server
entries pick up the update. Extend it for lifespan, middleware, and provider
registration as needed.
