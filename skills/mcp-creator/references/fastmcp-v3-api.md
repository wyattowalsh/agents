# FastMCP v3 API Reference

Comprehensive API surface for FastMCP v3. Read during server implementation or when selecting patterns.

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

---

## Table of Contents

1. [Imports Map](#1-imports-map)
2. [FastMCP Constructor](#2-fastmcp-constructor)
3. [Decorators](#3-decorators)
4. [Context Object](#4-context-object)
5. [Rich Return Types](#5-rich-return-types)
6. [Resources](#6-resources)
7. [Prompts](#7-prompts)
8. [Dependency Injection](#8-dependency-injection)
9. [Composable Lifespans](#9-composable-lifespans)
10. [Background Tasks](#10-background-tasks)
11. [Component Versioning](#11-component-versioning)
12. [Server-Level Visibility](#12-server-level-visibility)
13. [Middleware](#13-middleware)
14. [Auto Threadpool](#14-auto-threadpool)
15. [v2 to v3 Breaking Changes](#15-v2-to-v3-breaking-changes)
16. [Logging](#16-logging)

---

## 1. Imports Map

Verify current paths via Context7 -- they shift between releases.

```python
# Core
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from fastmcp.prompts import Message

# Resources
from fastmcp.resources import (
    ResourceResult, TextResource, BinaryResource,
    FileResource, HttpResource, DirectoryResource,
)

# Dependency injection
from fastmcp.dependencies import (
    Depends, CurrentContext, CurrentFastMCP, CurrentRequest,
    CurrentHeaders, CurrentAccessToken, TokenClaim,
    CurrentDocket, CurrentWorker, Progress,
)

# Lifespans
from fastmcp.server.lifespan import lifespan

# Providers
from fastmcp.server.providers import FileSystemProvider
from fastmcp.server.openapi import OpenAPIProvider, RouteMap, MCPType
from fastmcp.server import create_proxy

# Transforms
from fastmcp.server.transforms import (
    Transform, ToolTransform, Namespace,
    ResourcesAsTools, PromptsAsTools, VersionFilter,
)

# Middleware
from fastmcp.server.middleware import Middleware, MiddlewareContext

# Tasks
from fastmcp.server.tasks import TaskConfig

# Auth
from fastmcp.server.auth import require_scopes, AuthContext
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier, StaticTokenVerifier
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.auth.providers.google import GoogleProvider

# Rich return types
from fastmcp.utilities.types import Image, Audio, File

# MCP protocol types
from mcp.types import ToolAnnotations, TextContent, ImageContent, AudioContent

# Pydantic / typing
from pydantic import Field, BaseModel
from typing import Annotated, Literal
```

---

## 2. FastMCP Constructor

```python
mcp = FastMCP(
    name="MyServer",                     # str -- server name (default: "FastMCP")
    instructions="...",                  # str | None -- guidance for LLMs
    version="1.0.0",                     # str | None -- server version
    auth=None,                           # OAuthProvider | TokenVerifier | None -- HTTP auth
    lifespan=None,                       # Lifespan | AsyncContextManager | None -- setup/teardown
    tools=None,                          # list[Tool | Callable] | None -- programmatic tool list
    providers=None,                      # list[Provider] | None -- component sources
    middleware=None,                     # list[Middleware] | None -- MCP traffic interceptors
    on_duplicate_tools="error",          # DuplicateBehavior -- "warn" | "error" | "replace"
    on_duplicate_resources="warn",       # DuplicateBehavior
    on_duplicate_prompts="replace",      # DuplicateBehavior
    strict_input_validation=False,       # bool -- reject type coercion on tool inputs
    list_page_size=None,                 # int | None -- max items per paginated list
    mask_error_details=False,            # bool -- hide internal errors from clients
    tasks=None,                          # bool | None -- enable background tasks server-wide
    include_tags=None,                   # set[str] | None -- expose only matching components
    exclude_tags=None,                   # set[str] | None -- hide matching components
    stateless_http=False,                # bool -- no session state; for horizontal scaling
)
```

**`on_duplicate` behavior** applies per component type. A unified `on_duplicate` kwarg sets all three at once; per-type kwargs override:

```python
mcp = FastMCP("S", on_duplicate="warn")                          # all warn
mcp = FastMCP("S", on_duplicate="warn", on_duplicate_tools="error")  # tools error, rest warn
```

**`tasks`** enables the server-wide tasks primitive. `TaskConfig` controls per-decorator behavior (mode, poll interval), NOT the constructor.

**Removed kwargs.** 16 deprecated constructor kwargs (`host`, `port`, `debug`, `log_level`, `ui`, `reload`, `workers`, etc.) were removed in rc1. Passing them raises `TypeError`. Use CLI flags or ASGI deployment instead.

---

## 3. Decorators

### @mcp.tool

```python
@mcp.tool(
    name="custom_name",              # str | None -- override function name
    description="...",               # str | None -- override docstring
    tags={"math", "util"},           # set[str] | None -- categorization tags
    annotations=ToolAnnotations(     # ToolAnnotations | dict | None -- client hints
        title="Sum Calculator",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    timeout=30.0,                    # float | None -- execution timeout (seconds)
    version="2.0",                   # str | int | None -- component version
    output_schema=None,              # dict | type[BaseModel] | None -- typed structured output
    meta={"team": "backend"},        # dict[str, Any] | None -- custom metadata
    icons=None,                      # list[Icon] | None -- tool icons
    task=False,                      # TaskConfig | bool -- background execution
    sequential=False,                # bool -- prevent parallel execution
    auth=None,                       # AuthCheck | None -- per-tool authorization
)
```

**Annotated + Field pattern** (preferred -- exposes constraints in the JSON schema):

```python
from typing import Annotated, Literal
from pydantic import Field

@mcp.tool
async def search_issues(
    query: Annotated[str, Field(description="Boolean search query.", min_length=1)],
    status: Annotated[Literal["open", "closed", "all"], Field(
        description="Filter by issue status."
    )] = "open",
    limit: Annotated[int, Field(description="Max results to return.", ge=1, le=100)] = 20,
    ctx: Context | None = None,
) -> list[dict]:
    """Search project issues by query string and optional filters.

    Use when you need to find issues matching a keyword or boolean expression.
    Returns a list of issue dicts with id, title, status, and assignee fields.
    """
    ...
```

**Simple string annotation pattern** (lighter weight, no constraints):

```python
@mcp.tool
def resize(
    url: Annotated[str, "URL of the image to process"],
    width: Annotated[int, "Target width in pixels"] = 800,
) -> dict:
    """Resize an image to a target width."""
    ...
```

**`output_schema`** for typed structured output:

```python
class SearchResult(BaseModel):
    items: list[dict]
    total: int
    query: str

@mcp.tool(output_schema=SearchResult)
async def search(query: str) -> dict:
    """Search and return typed results."""
    results = await do_search(query)
    return {"items": results, "total": len(results), "query": query}
```

### @mcp.resource

```python
@mcp.resource(
    "data://app-status",             # str (required) -- resource URI
    name="ApplicationStatus",        # str | None -- display name
    description="...",               # str | None -- override docstring
    mime_type="application/json",    # str | None -- MIME type (auto-inferred if omitted)
    tags={"monitoring"},             # set[str] | None
    annotations=None,                # Annotations | dict | None
    meta=None,                       # dict[str, Any] | None
    icons=None,                      # list[Icon] | None
    version=None,                    # str | int | None
    auth=None,                       # AuthCheck | None -- per-resource authorization
)
```

**Resource template** with `{param}` in URI:

```python
@mcp.resource("users://{user_id}/profile")
async def get_profile(user_id: str) -> str:
    """User profile by ID."""
    return json.dumps(await fetch_profile(user_id))
```

### @mcp.prompt

```python
@mcp.prompt(
    name="analyze_data",             # str | None -- override function name
    title="Data Analysis",           # str | None -- human-readable title
    description="...",               # str | None -- override docstring
    tags={"analysis"},               # set[str] | None
    meta=None,                       # dict[str, Any] | None
    icons=None,                      # list[Icon] | None
    version=None,                    # str | int | None
)
```

---

## 4. Context Object

```python
from fastmcp import Context
```

**Injection methods (pick one):**

```python
# Preferred (v2.14+) -- explicit dependency
from fastmcp.dependencies import CurrentContext
async def my_tool(query: str, ctx: Context = CurrentContext()) -> str: ...

# Type-hint injection (legacy) -- also works
async def my_tool(query: str, ctx: Context) -> str: ...

# Default-None pattern -- for testability outside MCP runtime
async def my_tool(query: str, ctx: Context | None = None) -> str: ...

# Utility function -- for non-decorated helpers
from fastmcp.server.dependencies import get_context
ctx = get_context()
```

### Logging

Send log messages to the MCP client. All methods are async. Pass `extra={}` for structured metadata.

```python
await ctx.debug("Cache miss for key={key}", extra={"key": key})
await ctx.info("Processing started")
await ctx.warning("Rate limit approaching", extra={"remaining": 5})
await ctx.error("External API unreachable", extra={"url": url, "status": 503})
```

| Method | Level |
|--------|-------|
| `await ctx.debug(message, extra=)` | DEBUG |
| `await ctx.info(message, extra=)` | INFO |
| `await ctx.warning(message, extra=)` | WARNING |
| `await ctx.error(message, extra=)` | ERROR |

### Progress

Report progress to the client for long-running operations.

```python
await ctx.report_progress(progress=50, total=100, message="Halfway done")
```

Parameters:
- `progress` (float) -- current progress value
- `total` (float) -- total expected value
- `message` (str | None) -- optional status message

### State (v3 -- ASYNC)

Session-scoped key-value state. All methods are async in v3 -- always `await` them.

```python
await ctx.set_state("user_prefs", {"theme": "dark"})   # JSON-serializable by default
value = await ctx.get_state("user_prefs")               # Returns None if missing
await ctx.delete_state("user_prefs")

# For non-JSON-serializable values (single request only, not persisted):
await ctx.set_state("db_conn", conn, serializable=False)
```

State expires after 1 day to prevent unbounded memory growth.

### Sampling

Request LLM completions from the connected client.

```python
result = await ctx.sample(
    messages=[{"role": "user", "content": "Summarize this data"}],
    model_preferences="claude-sonnet-4-20250514",  # str | list[str] | None -- model hint
    system_prompt="You are a data analyst.",       # str | None -- system prompt
    max_tokens=1024,                   # int -- max response tokens
    temperature=0.7,                   # float | None
    tools=None,                        # list | None -- tools the LLM can use
    tool_concurrency=1,                # int -- parallel tool calls
    result_type=None,                  # type | None -- parse response into type
)
# result.text    -- string content of the response
# result.result  -- parsed result if result_type was set
# result.history -- full message history
```

Use `ctx.sample_step()` for a single LLM call without automatic tool-call loops:

```python
step = await ctx.sample_step(
    messages=[{"role": "user", "content": "Classify this text"}],
    max_tokens=50,
)
```

### Elicitation

Request interactive input from the connected client.

```python
from pydantic import BaseModel

class ApiKeyInput(BaseModel):
    key: str
    region: str = "us-east-1"

response = await ctx.elicit(
    message="Provide your API credentials",
    response_type=ApiKeyInput,
)

match response.action:
    case "accept":
        api_key = response.data.key
        region = response.data.region
        await ctx.info(f"Configured for {region}")
    case "decline":
        raise ToolError("User declined to provide credentials")
    case "cancel":
        raise ToolError("User cancelled the operation")
```

- `response.action` -- `"accept"` | `"decline"` | `"cancel"`
- `response.data` -- the user's input (typed per `response_type`), or `None` if not accepted

### Resource/Prompt Access

Read resources and prompts from within tool implementations.

```python
resources = await ctx.list_resources()
content = await ctx.read_resource("data://config")

prompts = await ctx.list_prompts()
prompt = await ctx.get_prompt("summarize", arguments={"text": "..."})
```

### Session Visibility (v3)

Dynamically show or hide components for the current session.

```python
await ctx.enable_components(tags={"premium"})
await ctx.enable_components(keys={"tool:admin_panel"})
await ctx.enable_components(names=["secret_tool"])     # names= ONLY on session-level methods

await ctx.disable_components(tags={"beta"})
await ctx.disable_components(keys={"tool:dangerous_delete"})
await ctx.disable_components(names=["deprecated_tool"])

await ctx.reset_visibility()  # restore to server-level defaults
```

The `names=` parameter exists ONLY on session-level methods (`ctx.enable_components`, `ctx.disable_components`), not on server-level `mcp.enable()` / `mcp.disable()`.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `ctx.transport` | `str` | `"stdio"`, `"sse"`, or `"streamable-http"` |
| `ctx.request_id` | `str` | Unique request identifier |
| `ctx.client_id` | `str \| None` | Client identifier |
| `ctx.session_id` | `str` | MCP session identifier |
| `ctx.fastmcp` | `FastMCP` | Server instance |
| `ctx.request_context` | `object` | Request metadata (may be `None` during init) |

---

## 5. Rich Return Types

| Return Type | MCP Content |
|-------------|-------------|
| `str` | `TextContent` |
| `dict` / Pydantic model / dataclass | Structured content (JSON) |
| `bytes` | `BlobResourceContents` |
| `Image(path=)` or `Image(data=, media_type=)` | `ImageContent` (base64) |
| `Audio(path=)` or `Audio(data=, media_type=)` | `AudioContent` (base64) |
| `File(path=)` | `BlobResourceContents` |

```python
from fastmcp.utilities.types import Image, Audio, File

@mcp.tool
def chart() -> Image:
    """Generate a chart image."""
    return Image(path="chart.png")

@mcp.tool
def recording() -> Audio:
    """Return an audio recording."""
    return Audio(path="output.wav")

@mcp.tool
def export() -> File:
    """Export data as a binary file."""
    return File(path="export.xlsx")
```

**Full control with `ToolResult`:**

```python
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

@mcp.tool
def advanced() -> ToolResult:
    """Return structured and human-readable content."""
    return ToolResult(
        content=[TextContent(type="text", text="Human-readable summary")],
        structured_content={"data": "value", "count": 42},
        meta={"execution_time_ms": 145},
    )
```

**Typed structured output with `output_schema`:**

```python
class AnalysisResult(BaseModel):
    sentiment: str
    confidence: float
    keywords: list[str]

@mcp.tool(output_schema=AnalysisResult)
async def analyze_text(text: str) -> dict:
    """Analyze text sentiment. Returns typed AnalysisResult."""
    return {"sentiment": "positive", "confidence": 0.92, "keywords": ["good", "great"]}
```

When `output_schema` is set, the client receives the schema definition and the tool validates its return value against it.

---

## 6. Resources

Use resources for static or slow-changing data addressed by URI. Use tools for actions, computations, or data that changes per-request.

### URI Patterns

URIs require a scheme. Templates use `{param}` for path parameters, `{?query}` for query parameters, and `{path*}` for wildcard path segments.

```
config://settings              # static URI
users://{user_id}/profile      # path template
search://results{?query,limit} # query parameters
files://{path*}                # wildcard path
```

### Static String Resource

```python
@mcp.resource("config://version", mime_type="text/plain")
def get_version() -> str:
    """Current server version."""
    return "1.0.0"
```

### Dynamic Function Resource

```python
@mcp.resource("status://health", mime_type="application/json")
async def health_status() -> str:
    """Live system health check."""
    return json.dumps({"status": "healthy", "uptime": get_uptime()})
```

### Template Resource

```python
@mcp.resource("users://{user_id}/profile")
async def get_user_profile(user_id: str) -> str:
    """User profile by ID."""
    profile = await fetch_profile(user_id)
    return json.dumps(profile)
```

### Query Parameter Resource

```python
@mcp.resource("search://logs{?level,limit}")
async def search_logs(level: str = "info", limit: int = 50) -> str:
    """Search logs by level."""
    logs = await query_logs(level=level, limit=limit)
    return json.dumps(logs)
```

### Wildcard Resource

```python
@mcp.resource("files://{path*}")
async def read_file(path: str) -> str:
    """Read a file by path."""
    return Path(path).read_text()
```

### Multi-Format ResourceResult

```python
from fastmcp.resources import ResourceResult

@mcp.resource("data://report", mime_type="application/json")
async def get_report() -> ResourceResult:
    """Return resource with explicit metadata."""
    return ResourceResult(
        content=json.dumps({"revenue": 1000}),
        mime_type="application/json",
        uri="data://report",
    )
```

### Class-Based Resources

Register resources without decorators using the built-in resource classes.

```python
from fastmcp.resources import TextResource, FileResource, HttpResource, DirectoryResource, BinaryResource

mcp.add_resource(TextResource(
    uri="config://readme",
    name="README",
    text="Welcome to the server.",
    mime_type="text/plain",
))

mcp.add_resource(FileResource(
    uri="files://data.csv",
    path=Path("data.csv"),
    mime_type="text/csv",
))

mcp.add_resource(HttpResource(
    uri="http://api.example.com/status",
    url="https://api.example.com/status",
    mime_type="application/json",
))

mcp.add_resource(DirectoryResource(
    uri="files://templates/",
    path=Path("./templates"),
    recursive=True,
))

mcp.add_resource(BinaryResource(
    uri="files://logo.png",
    data=logo_bytes,
    mime_type="image/png",
))
```

### Common MIME Types

| MIME Type | Use For |
|-----------|---------|
| `text/plain` | Plain text, config values |
| `application/json` | Structured data, API responses |
| `text/markdown` | Documentation, formatted text |
| `text/csv` | Tabular data |
| `text/html` | HTML content |
| `application/octet-stream` | Binary data (default for bytes) |
| `image/png`, `image/jpeg` | Images |

---

## 7. Prompts

Prompts are reusable message templates that guide LLM behavior. Use prompts for repeatable workflows the user triggers by name. Use tools for actions. Use resources for data retrieval.

### Simple String Return

```python
@mcp.prompt
def greet(name: str) -> str:
    """Generate a greeting."""
    return f"Hello, {name}! How can I help you today?"
```

### Message List Return

```python
from fastmcp.prompts import Message

@mcp.prompt
def code_review(code: str, language: str = "python") -> list[Message]:
    """Generate a code review prompt with system context."""
    return [
        Message(role="user", content=f"Review this {language} code for bugs, "
                f"performance issues, and style problems:\n\n```{language}\n{code}\n```"),
    ]
```

`Message(content, role=)` -- default role is `"user"`. Valid roles: `"user"`, `"assistant"`.

### Parameterized Prompt

```python
@mcp.prompt(
    name="summarize",
    title="Document Summarizer",
    description="Summarize a document at a specified detail level.",
)
def summarize_doc(
    document: str,
    detail: str = "brief",
    audience: str = "technical",
) -> list[Message]:
    """Generate a summarization prompt."""
    return [
        Message(
            role="user",
            content=f"Summarize the following document for a {audience} audience "
                    f"at {detail} detail level:\n\n{document}",
        ),
    ]
```

---

## 8. Dependency Injection

Injected parameters are hidden from the MCP schema -- clients never see them.

```python
from fastmcp.dependencies import Depends

def get_config() -> dict:
    return {"api_url": "https://api.example.com", "timeout": 30}

@mcp.tool
async def fetch_data(query: str, config: dict = Depends(get_config)) -> str:
    """Fetch data from the API. Client sees only 'query'."""
    return f"Fetching '{query}' from {config['api_url']}"
```

**Async context manager pattern** for resource cleanup:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_database():
    db = await connect()
    try:
        yield db
    finally:
        await db.close()

@mcp.tool
async def query_data(sql: str, db=Depends(get_database)) -> list:
    """Run a SQL query. DB connection is injected and cleaned up automatically."""
    return await db.execute(sql)
```

Dependencies resolve once per request and reuse the same instance across nested dependencies.

### Built-in Dependencies

| Dependency | Import Path | Description |
|------------|-------------|-------------|
| `CurrentContext()` | `fastmcp.dependencies` | MCP request context |
| `CurrentFastMCP()` | `fastmcp.dependencies` | Server instance |
| `CurrentRequest()` | `fastmcp.dependencies` | Starlette `Request` (HTTP only) |
| `CurrentHeaders()` | `fastmcp.dependencies` | HTTP headers dict |
| `CurrentAccessToken()` | `fastmcp.dependencies` | OAuth/JWT access token |
| `TokenClaim("sub")` | `fastmcp.dependencies` | Extract a specific JWT claim |
| `CurrentDocket()` | `fastmcp.dependencies` | Docket instance for background tasks |
| `CurrentWorker()` | `fastmcp.dependencies` | Worker config access |
| `Progress()` | `fastmcp.dependencies` | Task progress tracking |

---

## 9. Composable Lifespans

Manage shared resources (DB pools, HTTP clients, caches) across the server lifetime.

```python
from fastmcp.server.lifespan import lifespan

@lifespan
async def db_lifespan(server):
    db = await create_pool("postgres://...")
    try:
        yield {"db": db}
    finally:
        await db.close()

@lifespan
async def cache_lifespan(server):
    redis = await aioredis.from_url("redis://...")
    try:
        yield {"cache": redis}
    finally:
        await redis.close()

# Combine with | operator: left-to-right enter, right-to-left (LIFO) exit
mcp = FastMCP("MyServer", lifespan=db_lifespan | cache_lifespan)
```

Context dicts merge on composition. Later lifespans override on key conflict.

**Access lifespan state in tools:**

```python
@mcp.tool
async def query_users(ctx: Context) -> list:
    """Query all users from the database."""
    db = ctx.lifespan_context["db"]
    return await db.fetch("SELECT * FROM users")
```

**Legacy compatibility.** Wrap existing `@asynccontextmanager` functions with `ContextManagerLifespan` before composing:

```python
from fastmcp.server.lifespan import ContextManagerLifespan

legacy = ContextManagerLifespan(my_existing_context_manager)
mcp = FastMCP("S", lifespan=db_lifespan | legacy)
```

---

## 10. Background Tasks

Run long-running operations asynchronously. Requires `pip install "fastmcp[tasks]>=3.0.0"`. Only async functions are supported.

> MCP Tasks primitive is experimental.

```python
from fastmcp.server.tasks import TaskConfig

# Shorthand -- mode="optional"
@mcp.tool(task=True)
async def analyze(data: str) -> str:
    """Analyze data. Can run in background if client requests it."""
    await asyncio.sleep(10)
    return "Analysis complete"

# Explicit config
@mcp.tool(task=TaskConfig(mode="required", poll_interval=timedelta(seconds=2)))
async def long_job(input: str) -> str:
    """Long-running job. Always runs as background task."""
    ...
```

| Mode | Sync Call | Task Call |
|------|-----------|-----------|
| `"optional"` | Runs synchronously | Runs in background |
| `"required"` | Raises error | Runs in background |
| `"forbidden"` | Runs synchronously | Runs synchronously |

**Progress reporting in tasks:**

```python
from fastmcp.dependencies import Progress

@mcp.tool(task=True)
async def process_files(files: list[str], progress: Progress = Progress()) -> str:
    """Process files with progress tracking."""
    await progress.set_total(len(files))
    for f in files:
        await progress.set_message(f"Processing {f}")
        # ... process file ...
        await progress.increment()
    return "Done"
```

**Docket backends** (via `FASTMCP_DOCKET_URL` env var or constructor):

| Backend | URL | Use Case |
|---------|-----|----------|
| In-memory | `memory://` | Development (default, ephemeral) |
| Redis | `redis://localhost:6379` | Production (persistent, scalable) |
| SQLite | `sqlite:///tasks.db` | Lightweight persistence |

**CLI workers** for processing tasks outside the server process:

```bash
fastmcp tasks worker
```

---

## 11. Component Versioning

Register multiple versions of the same component. Clients see the highest version by default.

```python
@mcp.tool(version="1.0")
def process(data: str) -> str:
    """Process data (v1)."""
    return data.upper()

@mcp.tool(version="2.0")
def process(data: str, mode: str = "default") -> str:
    """Process data with mode selection (v2)."""
    return data[::-1].upper() if mode == "reverse" else data.upper()
```

**Client-side version selection:**

```python
# FastMCP client
result = await client.call_tool("process", {"data": "hello"}, version="1.0")

# Generic MCP client -- pass via _meta
{"data": "hello", "_meta": {"fastmcp": {"version": "1.0"}}}
```

**Version filtering with transforms:**

```python
from fastmcp.server.transforms import VersionFilter

mcp.add_transform(VersionFilter(version_gte="2.0"))   # expose only v2.0+
mcp.add_transform(VersionFilter(version_lt="2.0"))    # expose only pre-v2.0
```

Rule: either version ALL implementations of a name or none. Mixing versioned and unversioned raises an error.

---

## 12. Server-Level Visibility

Control which components are exposed globally. Use session-level visibility (Section 4) for per-connection overrides.

```python
# Hide by tag
mcp.disable(tags={"admin"})

# Allowlist mode -- show ONLY matching tags, hide everything else
mcp.enable(tags={"public"}, only=True)

# Hide a specific component by key
mcp.disable(keys={"tool:dangerous_delete"})

# Key format: {type}:{identifier}
# Examples: tool:search_docs, resource:data://config, prompt:summarize
```

**`enabled=False`** on decorators and **`remove_tool()`** are both deprecated. Use the visibility API instead.

**Filter parameters** (same for `mcp.enable()` and `mcp.disable()`):

| Parameter | Description |
|-----------|-------------|
| `tags` | Tag-based matching |
| `keys` | Specific component keys (e.g., `"tool:my_tool"`) |
| `version` | Version specifications |
| `components` | Component types: `"tool"`, `"resource"`, `"prompt"`, `"template"` |
| `only` | `True` = allowlist mode (disable everything except matches) |
| `match_all` | Match all components regardless of other criteria |

Note: `names=` is NOT available on server-level methods. Use `keys=` instead.

---

## 13. Middleware

Middleware intercepts all MCP traffic. Execution is bidirectional: requests flow in registration order, responses flow in reverse.

### Registration

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext

mcp.add_middleware(MyMiddleware())
# Or at construction:
mcp = FastMCP("S", middleware=[MyMiddleware()])
```

### Built-in Middleware (14)

| Middleware | Key Parameters | Purpose |
|-----------|----------------|---------|
| `LoggingMiddleware` | `include_payloads`, `max_payload_length` | Log all MCP messages |
| `StructuredLoggingMiddleware` | `include_payloads`, `max_payload_length` | JSON-formatted logs |
| `TimingMiddleware` | -- | Log request durations |
| `DetailedTimingMiddleware` | -- | Per-phase timing breakdown |
| `ResponseCachingMiddleware` | Per-operation TTL settings | Cache responses by operation |
| `RateLimitingMiddleware` | `max_requests_per_second`, `burst_capacity` | Fixed-window rate limiting |
| `SlidingWindowRateLimitingMiddleware` | `max_requests`, `window_minutes` | Sliding-window rate limiting |
| `ErrorHandlingMiddleware` | `include_traceback`, `transform_errors` | Catch and transform errors |
| `RetryMiddleware` | `max_retries`, `retry_exceptions` | Auto-retry failed operations |
| `PingMiddleware` | `interval_ms` | Keep-alive pings |
| `ToolInjectionMiddleware` | `tools` (list) | Inject extra tools dynamically |
| `PromptToolMiddleware` | -- | Expose prompts as tools |
| `ResourceToolMiddleware` | -- | Expose resources as tools |
| `ResponseLimitingMiddleware` | `max_size`, `truncation_suffix` | Truncate oversized responses |

### Custom Middleware

```python
class AuditMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        log.info(f"Tool called: {tool_name}")
        result = await call_next(context)
        log.info(f"Tool completed: {tool_name}")
        return result
```

### Hook Levels

Override any combination of hooks. More specific hooks take precedence over general ones.

| Level | Hooks |
|-------|-------|
| Message | `on_message()`, `on_request()`, `on_notification()` |
| Operation | `on_call_tool()`, `on_read_resource()`, `on_get_prompt()` |
| List | `on_list_tools()`, `on_list_resources()`, `on_list_prompts()` |
| Lifecycle | `on_initialize()` |
| Raw | `__call__(context, call_next)` -- bypasses hook dispatch entirely |

**`MiddlewareContext` properties:**

| Property | Type | Description |
|----------|------|-------------|
| `method` | `str` | MCP method name |
| `source` | `str` | `"client"` or `"server"` |
| `type` | `str` | `"request"` or `"notification"` |
| `message` | `object` | The MCP message being processed |
| `timestamp` | `datetime` | When the message was received |
| `fastmcp_context` | `Context` | The FastMCP Context object |

---

## 14. Auto Threadpool

Sync tools are dispatched to a threadpool automatically. No special configuration needed. Define sync functions and they run without blocking the event loop:

```python
@mcp.tool
def compute_hash(data: str) -> str:
    """CPU-bound hash computation. Runs in threadpool automatically."""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()
```

Async tools run on the event loop as expected. Prefer async for I/O-bound work.

---

## 15. v2 to v3 Breaking Changes

| Change | v2 | v3 | Migration |
|--------|----|----|-----------|
| Decorators | Return component object | Return original function | Functions are now directly callable |
| State methods | Synchronous `ctx.set_state()` | `await ctx.set_state()` | Add `async`/`await` to all state calls |
| Auth config | Auto-loaded from env | Manual loading required | Explicitly configure providers |
| `enabled=False` | `@mcp.tool(enabled=False)` | Deprecated | Use `mcp.disable(keys={"tool:name"})` |
| `remove_tool()` | Available | Deprecated | Use visibility API |
| `on_duplicate_tools` | Per-type only | Unified `on_duplicate` + per-type overrides | Use `on_duplicate=` for all, per-type to override |
| Mount prefix | `mount(server, prefix="api")` | `mount(server, namespace="api")` | Rename `prefix` to `namespace` |
| `tool_serializer` | Custom serializer function | `ToolResult` return type | Return `ToolResult` directly |
| `Message` import | `from mcp.types import PromptMessage` | `from fastmcp.prompts import Message` | Update import path |
| `WSTransport` | Available | Removed | Use `StreamableHttpTransport` |
| Constructor kwargs | 16 kwargs accepted (`host`, `port`, `debug`, `log_level`, etc.) | Removed; raise `TypeError` | Use CLI flags or ASGI deployment |
| `require_auth` | Global auth flag | Removed | Use scope-based auth per component |
| `ui=` param | `mcp.run(ui=True)` | Removed | Use `app=` (rc1+) or CLI `fastmcp dev` |
| OAuth storage | `DiskStore` default | `FileTreeStore` default | Clients auto-re-register |
| Env banner var | `FASTMCP_SHOW_CLI_BANNER` | `FASTMCP_SHOW_SERVER_BANNER` | Rename env variable |
| State values | Any Python object | JSON-serializable default | Use `serializable=False` for non-JSON |
| Tag filtering | `include_tags`/`exclude_tags` params | `disable()`/`enable()` methods | Refactor to visibility API |
| Metadata key | `_fastmcp` in `_meta` | `fastmcp` in `_meta` | Update metadata access paths |
| Listing methods | `get_tools()` returns dict | `list_tools()` returns list | Update calls and access patterns |

---

## 16. Logging

Configure server-side logging independently of MCP client logging (Section 4).

```python
from fastmcp import get_logger, configure_logging, temporary_log_level

# Get a named logger
logger = get_logger("my-server")
logger.info("Server starting")

# Configure global log level
configure_logging(level="DEBUG")

# Temporary log level for a block
with temporary_log_level("DEBUG"):
    logger.debug("Verbose output here")
```

Set the log level via environment variable:

```bash
FASTMCP_LOG_LEVEL=DEBUG fastmcp run server.py
```

Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
