# Designing LLM-Optimized MCP Tools

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

Patterns for writing FastMCP v3 tools that LLMs can discover, understand, and use correctly.
Read during tool design (Phase 1) and implementation (Phase 3).

---

## 1. Naming

Use `snake_case` with a `verb_noun` pattern. Aim for under 32 characters; hard limit is 64.

| Quality | Name | Why |
|---------|------|-----|
| Good | `search_issues` | Verb-noun, specific action, clear target |
| Good | `get_pull_request` | Verb-noun, unambiguous resource |
| Good | `create_user` | Standard CRUD verb |
| Good | `github_list_repos` | Service prefix for multi-service server |
| Good | `slack_send_message` | Service prefix, verb-noun |
| Bad | `process` | No noun -- what does it process? |
| Bad | `do_thing` | Meaningless verb and noun |
| Bad | `handle` | Ambiguous, no resource target |
| Bad | `data` | Noun-only, no action indicated |
| Bad | `files` | Noun-only, LLM cannot infer the operation |
| Bad | `run` | No noun, could mean anything |
| Bad | `searchIssues` | camelCase -- MCP convention is snake_case |
| Bad | `search_and_delete_files` | Two actions -- split into `search_files` + `delete_file` |

Prefix with the service name when a server exposes tools for multiple external services (`github_list_repos`, `slack_send_message`, `jira_update_ticket`). Skip the prefix when the entire server represents a single domain.

---

## 2. Descriptions for LLMs

Descriptions are how LLMs decide which tool to call. They are the tool's primary interface. Be extremely verbose -- 3-5 sentences minimum. LLMs have plenty of context window; you pay nothing for longer descriptions.

Structure every description as: **WHAT** it does, **WHEN** to use it, **WHEN NOT** to use it, **WHAT** it returns.

### Side-by-Side Comparison

**Bad -- vague, no guidance:**

```python
@mcp.tool
async def search_files(pattern: str) -> list[str]:
    """Search files."""
```

Problems: LLM does not know what kind of search (name? content?), what pattern format to use, what it returns, or when to prefer this over other tools.

**Good -- LLM knows exactly when and how to use this:**

```python
@mcp.tool
async def search_files(
    pattern: Annotated[str, Field(
        description="Glob pattern for name search (e.g., '*.py') or regex for content search. "
                    "Supports standard glob wildcards: *, **, ?.",
        min_length=1,
    )],
    search_type: Annotated[Literal["name", "content"], Field(
        description="Whether to match file names or search inside file contents.",
    )] = "name",
    ctx: Context | None = None,
) -> list[dict]:
    """Search for files in the project directory by name pattern or content regex.

    Use when you need to find specific files by glob pattern (e.g., '*.py') or
    search file contents with a regular expression. Do NOT use this for listing
    all files in a directory -- use list_directory instead. Returns a list of
    matching file paths with line numbers for content matches. Results are capped
    at 1000 entries. Searches only the current project root, not external
    directories or symlinked paths outside the project.
    """
```

### Description Rules

- Start with a verb phrase: "Search for...", "Create a new...", "Delete the..."
- State the return shape: "Returns a list of...", "Returns a dictionary with..."
- Mention limits: max results, rate limits, size constraints, timeouts.
- Mention what the tool does NOT do -- prevents the LLM from misusing it.
- Mention related tools when disambiguation helps: "Use get_user for a single user; use this for batch lookups."
- Add `Annotated[type, Field(description=...)]` on EVERY parameter. LLMs cannot fill parameters they do not understand. A parameter without a description is invisible to reasoning.

---

## 3. Parameter Design

Every parameter must carry a description. Use `Annotated` with `Field` for rich constraints.

### Annotated + Field Pattern (Preferred)

```python
from typing import Annotated, Literal
from pydantic import BaseModel, Field

@mcp.tool
async def search_issues(
    query: Annotated[str, Field(
        description="Search query string. Supports boolean operators: AND, OR, NOT. "
                    "Example: 'auth AND login NOT deprecated'.",
        min_length=1,
    )],
    status: Annotated[Literal["open", "closed", "all"], Field(
        description="Filter by issue status. Use 'all' to include both open and closed.",
    )] = "open",
    max_results: Annotated[int, Field(
        description="Maximum number of results to return. Higher values increase response time.",
        ge=1,
        le=100,
    )] = 20,
) -> list[dict]:
    """Search project issues by query string and optional filters.

    Use when you need to find issues matching keywords or boolean expressions.
    Do NOT use for retrieving a single issue by ID -- use get_issue instead.
    Returns a list of issue objects with id, title, status, and assignee fields.
    Limited to 100 results per call; use offset for pagination.
    """
```

### Simple String Annotations (Quick Alternative)

```python
@mcp.tool
def resize_image(
    url: Annotated[str, "URL of the image to process. Must be publicly accessible."],
    width: Annotated[int, "Target width in pixels. Height scales proportionally."] = 800,
) -> dict:
    """Resize an image to the specified width, preserving aspect ratio.

    Use when you need to generate thumbnails or fit images to a target container.
    Returns a dictionary with 'url' (resized image URL) and 'dimensions' (width, height).
    Maximum input size: 20MB. Supported formats: PNG, JPEG, WebP.
    """
```

### Literal for Fixed Option Sets

```python
format: Annotated[Literal["json", "markdown", "csv"], Field(
    description="Output format. Use 'json' for structured processing, "
                "'markdown' for human-readable display, 'csv' for spreadsheet import.",
)] = "json"
```

### Pydantic BaseModel for Complex Grouped Inputs

Group 3+ related fields into a model. Describe every field.

```python
class CreateIssueInput(BaseModel):
    title: Annotated[str, Field(
        description="Issue title. Keep under 256 characters.",
        max_length=256,
    )]
    body: Annotated[str, Field(
        description="Issue body in GitHub-flavored markdown.",
    )]
    labels: Annotated[list[str], Field(
        description="Labels to apply to the issue. Must be pre-existing labels.",
        default_factory=list,
    )]
    assignee: Annotated[str | None, Field(
        description="GitHub username to assign. Omit to leave unassigned.",
    )] = None
    priority: Annotated[Literal["low", "medium", "high", "critical"], Field(
        description="Issue priority level.",
    )] = "medium"

@mcp.tool(annotations={"destructiveHint": False, "idempotentHint": False})
async def create_issue(input: CreateIssueInput) -> dict:
    """Create a new issue in the project tracker.

    Use when you need to file a bug report, feature request, or task.
    Do NOT use for updating existing issues -- use update_issue instead.
    Returns the created issue object with id, url, title, and status fields.
    """
```

### Parameter Rules

- Every parameter MUST have a `description`. No exceptions.
- Use `Literal["a", "b", "c"]` instead of `str` for fixed option sets.
- Use `Field(ge=..., le=...)` for numeric bounds -- LLMs respect validated ranges.
- Use `Field(min_length=1)` to prevent empty strings on required text inputs.
- Default values signal "optional" to LLMs. Required parameters have no default.
- Never use `*args`, `**kwargs`, or `dict[str, Any]` -- LLMs cannot fill unstructured inputs. MCP requires a fixed JSON schema for tool inputs.

---

## 4. Annotations

Annotations tell MCP clients about tool behavior without calling the tool. Clients use these for confirmation dialogs, retry logic, and safety guards. Include annotations on EVERY tool.

### Hint Reference

| Hint | Set `True` when | Set `False` when | Examples |
|------|-----------------|------------------|----------|
| `readOnlyHint` | Tool reads but does not modify any state | Tool creates, updates, or deletes state | `True`: `search_*`, `list_*`, `get_*`. `False`: `create_*`, `update_*`, `delete_*` |
| `destructiveHint` | Tool performs irreversible changes | Changes are reversible or tool is read-only | `True`: `delete_*`, `overwrite_*`, `drop_*`, `purge_*`. `False`: `create_*`, `get_*` |
| `idempotentHint` | Calling N times with same input = same result | Each call produces different side effects | `True`: `get_user`, `set_config`, `upsert_record`. `False`: `increment_counter`, `send_email`, `create_issue` |
| `openWorldHint` | Tool calls external services or the internet | Tool operates only on local/internal data | `True`: API calls, web fetches, email sends, webhook triggers. `False`: local file reads, in-memory computations |

### ToolAnnotations Object Syntax

```python
from mcp.types import ToolAnnotations

@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
))
async def search_external_api(query: str) -> list[dict]:
    """Search the external catalog API for products."""
```

### Dict Syntax (Equivalent)

```python
@mcp.tool(annotations={
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
})
async def search_external_api(query: str) -> list[dict]:
    """Search the external catalog API for products."""
```

Both syntaxes produce identical MCP metadata. Use whichever reads cleaner in context.

### Common Annotation Profiles

| Tool type | readOnly | destructive | idempotent | openWorld |
|-----------|----------|-------------|------------|-----------|
| `get_*` / `list_*` (local) | True | False | True | False |
| `search_*` (external API) | True | False | True | True |
| `create_*` | False | False | False | varies |
| `update_*` / `set_*` | False | False | True | varies |
| `delete_*` | False | True | True | varies |
| `send_*` (email, webhook) | False | False | False | True |

---

## 5. Error Handling

FastMCP uses a two-tier error system. Understand which tier applies before writing error handling code.

### Tier 1: ToolError (Expected, Always Visible)

```python
from fastmcp.exceptions import ToolError
```

`ToolError` messages always reach the client, even when `mask_error_details=True`. Use for recoverable, expected conditions: not found, invalid input, rate limited, permission denied, service unavailable.

### Tier 2: Standard Exceptions (Internal, Masked in Production)

Standard Python exceptions (`ValueError`, `RuntimeError`, `KeyError`, etc.) propagate as MCP errors with tracebacks in development. When `mask_error_details=True` is set on the server (recommended for production), these show a generic error message to the client. Use for unexpected failures.

### Complete Example with httpx

```python
import httpx
from fastmcp import Context
from fastmcp.exceptions import ToolError

@mcp.tool(
    timeout=30.0,
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
)
async def fetch_user_profile(
    username: Annotated[str, Field(
        description="GitHub username to look up. Case-insensitive.",
        min_length=1,
        max_length=39,
    )],
    ctx: Context | None = None,
) -> dict:
    """Fetch a GitHub user's public profile by username.

    Use when you need profile details (name, bio, repos, followers) for a
    specific GitHub user. Do NOT use for organization profiles -- use
    fetch_org_profile instead. Returns a dictionary with login, name, bio,
    public_repos, and followers fields. Timeout: 30 seconds.
    """
    if ctx:
        await ctx.info(f"Fetching GitHub profile for {username}")
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.get(
                f"https://api.github.com/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "login": data["login"],
                "name": data.get("name"),
                "bio": data.get("bio"),
                "public_repos": data["public_repos"],
                "followers": data["followers"],
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ToolError(f"User '{username}' not found on GitHub.")
        if e.response.status_code == 403:
            raise ToolError("GitHub API rate limit exceeded. Wait 60 seconds and retry.")
        raise ToolError(
            f"GitHub API returned HTTP {e.response.status_code}: "
            f"{e.response.text[:200]}"
        )
    except httpx.ConnectError:
        raise ToolError("Cannot connect to GitHub API. Check network connectivity.")
    except httpx.TimeoutException:
        raise ToolError("GitHub API request timed out after 25 seconds. Try again later.")
    # Do NOT catch broad Exception -- let unexpected errors propagate with tracebacks
```

### Error Handling Rules

- Use `ToolError` for expected, recoverable conditions. Include actionable context: what failed, why, and what to try instead.
- Never silence exceptions with bare `except: pass`. LLMs need error feedback to self-correct.
- Never catch `Exception` broadly -- it masks bugs and prevents debugging.
- Set inner httpx/aiohttp timeouts slightly below the `@mcp.tool(timeout=...)` value so the tool can raise a descriptive `ToolError` before the decorator's timeout fires a generic error.
- For production servers, set `mask_error_details=True` on the `FastMCP` constructor to hide internal exception details from clients.

---

## 6. Timeout Protection

Set `@mcp.tool(timeout=...)` on every tool that calls external services, runs long computations, or touches the filesystem.

```python
@mcp.tool(timeout=30.0)
async def query_analytics(
    query: Annotated[str, Field(description="SQL-like analytics query.")],
) -> dict:
    """Query the analytics warehouse. May take up to 30 seconds for complex queries.

    Use when you need aggregate metrics or time-series data. Returns a dictionary
    with 'columns', 'rows', and 'row_count' fields. Timeout: 30 seconds.
    """
    return await analytics_client.execute(query)
```

- Default: no timeout (the tool runs indefinitely). Always override for external calls.
- Timeout fires a standard MCP error to the client. For a friendlier message, set an inner timeout (Section 5) and raise `ToolError` before the decorator's timeout triggers.
- Document the timeout in the tool description so LLMs can anticipate delays and inform users.

---

## 7. Structured Output

Choose the return type based on what the consuming LLM needs.

### str -- Freeform Text

```python
@mcp.tool
async def summarize(text: Annotated[str, Field(description="Text to summarize.")]) -> str:
    """Summarize the given text into 2-3 sentences."""
    return generate_summary(text)
```

### dict / Pydantic Model -- Structured Data

```python
@mcp.tool
async def get_user(
    user_id: Annotated[str, Field(description="Unique user identifier.")],
) -> dict:
    """Retrieve a user record by ID. Returns id, name, email, and role."""
    return {"id": user_id, "name": "Alice", "email": "alice@example.com", "role": "admin"}
```

### ToolResult -- Full Control Over Content

```python
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

@mcp.tool
async def analyze_data(
    dataset: Annotated[str, Field(description="Dataset identifier to analyze.")],
) -> ToolResult:
    """Run statistical analysis on a dataset. Returns human-readable summary
    and structured metrics.
    """
    stats = compute_stats(dataset)
    return ToolResult(
        content=[TextContent(type="text", text=f"Analysis of {dataset}: mean={stats['mean']:.2f}")],
        structured_content=stats,
        meta={"execution_time_ms": stats["elapsed_ms"]},
    )
```

### output_schema -- Typed Structured Output

Constrain the structured output with a JSON schema. Clients that support structured output can validate the response shape.

```python
@mcp.tool(
    output_schema={
        "type": "object",
        "properties": {
            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "keywords": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sentiment", "confidence", "keywords"],
    },
)
async def analyze_sentiment(
    text: Annotated[str, Field(description="Text to analyze for sentiment.", min_length=1)],
) -> dict:
    """Analyze sentiment of the given text.

    Returns a structured object with sentiment (positive/negative/neutral),
    confidence score (0-1), and extracted keywords.
    """
    return {"sentiment": "positive", "confidence": 0.92, "keywords": ["great", "excellent"]}
```

---

## 8. Response Patterns

### Format Negotiation

Let callers pick the output format for flexibility.

```python
@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
async def list_projects(
    format: Annotated[Literal["json", "markdown", "csv"], Field(
        description="Output format. 'json' for structured processing, "
                    "'markdown' for human-readable tables, 'csv' for data export.",
    )] = "json",
) -> str | dict:
    """List all projects in the workspace.

    Use when you need a summary of available projects. Returns project name,
    status, and last-updated timestamp. Supports json, markdown, and csv output.
    """
    projects = await fetch_projects()
    if format == "json":
        return {"projects": projects, "total": len(projects)}
    if format == "markdown":
        header = "| Name | Status | Updated |\n|------|--------|---------|\n"
        rows = "\n".join(f"| {p['name']} | {p['status']} | {p['updated']} |" for p in projects)
        return header + rows
    # csv
    lines = ["name,status,updated"]
    lines.extend(f"{p['name']},{p['status']},{p['updated']}" for p in projects)
    return "\n".join(lines)
```

### Pagination

Expose offset/limit parameters and always return total_count so the LLM knows whether more data exists.

```python
@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
async def list_events(
    offset: Annotated[int, Field(description="Number of items to skip.", ge=0)] = 0,
    limit: Annotated[int, Field(description="Max items to return per page.", ge=1, le=100)] = 20,
) -> dict:
    """List events with pagination.

    Returns a page of events plus pagination metadata. Use offset and limit
    to page through results. Check 'has_more' to know if additional pages exist.
    """
    all_events = await fetch_events()
    page = all_events[offset : offset + limit]
    return {
        "events": page,
        "total_count": len(all_events),
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < len(all_events),
    }
```

### Response Size Limit

Keep responses under ~25,000 characters. LLM context windows are large but not infinite, and excessively long tool outputs degrade reasoning quality. Truncate with an explicit note when output exceeds the limit.

```python
MAX_RESPONSE_CHARS = 25_000

def truncate_response(text: str) -> str:
    if len(text) <= MAX_RESPONSE_CHARS:
        return text
    return (
        text[:MAX_RESPONSE_CHARS]
        + f"\n\n[TRUNCATED: Response exceeded {MAX_RESPONSE_CHARS} characters. "
        f"Use offset/limit parameters to retrieve remaining data.]"
    )
```

---

## 9. Eight Tool Patterns

### Pattern 1: Basic Sync

Use when the operation is simple, fast, CPU-bound, and has no I/O.

```python
from typing import Annotated
from pydantic import Field

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
def calculate_bmi(
    weight_kg: Annotated[float, Field(description="Body weight in kilograms.", gt=0, le=700)],
    height_m: Annotated[float, Field(description="Height in meters.", gt=0, le=3.0)],
) -> dict:
    """Calculate Body Mass Index (BMI) from weight and height.

    Use when you need to compute BMI for a person. Do NOT use for animals or
    non-standard body composition analysis. Returns a dictionary with 'bmi'
    (float, rounded to 1 decimal) and 'category' (underweight/normal/overweight/obese).
    """
    bmi = round(weight_kg / (height_m ** 2), 1)
    if bmi < 18.5:
        category = "underweight"
    elif bmi < 25:
        category = "normal"
    elif bmi < 30:
        category = "overweight"
    else:
        category = "obese"
    return {"bmi": bmi, "category": category}
```

### Pattern 2: Async + Context (Logging and Progress)

Use when the operation involves I/O and you want to report progress or log status to the client.

```python
from fastmcp import Context

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True,
    },
)
async def index_documents(
    directory: Annotated[str, Field(
        description="Absolute path to the directory containing documents to index.",
    )],
    ctx: Context | None = None,
) -> dict:
    """Index all documents in a directory for full-text search.

    Use when you need to build or rebuild the search index for a directory.
    Returns a summary with 'indexed_count', 'skipped_count', and 'errors' list.
    May take several seconds for large directories.
    """
    files = list(Path(directory).rglob("*.md"))
    indexed, skipped, errors = 0, 0, []

    for i, f in enumerate(files):
        if ctx:
            await ctx.report_progress(i, len(files))
            await ctx.info(f"Indexing {f.name}")
        try:
            content = f.read_text(encoding="utf-8")
            await add_to_index(f.name, content)
            indexed += 1
        except UnicodeDecodeError:
            skipped += 1
        except Exception as e:
            errors.append({"file": str(f), "error": str(e)})

    if ctx:
        await ctx.report_progress(len(files), len(files))
    return {"indexed_count": indexed, "skipped_count": skipped, "errors": errors}
```

### Pattern 3: Stateful (Lifespan State)

Use when tools share a resource initialized at startup (database connection pool, cache client, loaded ML model).

```python
from contextlib import asynccontextmanager
from fastmcp import FastMCP, Context

@asynccontextmanager
async def lifespan(server):
    import asyncpg
    pool = await asyncpg.create_pool("postgresql://localhost/mydb")
    try:
        yield {"db": pool}
    finally:
        await pool.close()

mcp = FastMCP("database-server", lifespan=lifespan)

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def query_users(
    role: Annotated[str | None, Field(
        description="Filter users by role. Omit to return all users.",
    )] = None,
    limit: Annotated[int, Field(description="Max rows to return.", ge=1, le=500)] = 50,
    ctx: Context | None = None,
) -> list[dict]:
    """Query the user database with optional role filter.

    Use when you need to look up users. Returns a list of user objects with
    id, name, email, and role. Requires an active database connection managed
    by the server lifespan.
    """
    db = ctx.lifespan_context["db"]
    if role:
        rows = await db.fetch(
            "SELECT id, name, email, role FROM users WHERE role = $1 LIMIT $2",
            role, limit,
        )
    else:
        rows = await db.fetch("SELECT id, name, email, role FROM users LIMIT $1", limit)
    return [dict(row) for row in rows]
```

### Pattern 4: External API (httpx + Error Handling + Timeout)

Use when wrapping a third-party HTTP API. Combine decorator timeout, inner httpx timeout, and granular error handling.

```python
import httpx
from fastmcp import Context
from fastmcp.exceptions import ToolError

@mcp.tool(
    timeout=30.0,
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
)
async def search_npm_packages(
    query: Annotated[str, Field(
        description="Search query for npm packages. Use keywords, not exact package names.",
        min_length=1,
    )],
    size: Annotated[int, Field(
        description="Number of results to return.",
        ge=1,
        le=50,
    )] = 10,
    ctx: Context | None = None,
) -> dict:
    """Search the npm registry for packages matching a query.

    Use when you need to discover npm packages by keyword. Do NOT use for
    fetching a specific package's details -- use get_npm_package instead.
    Returns a dictionary with 'packages' (list of name, version, description)
    and 'total' (total matching packages). Timeout: 30 seconds.
    """
    if ctx:
        await ctx.info(f"Searching npm for: {query}")
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.get(
                "https://registry.npmjs.org/-/v1/search",
                params={"text": query, "size": size},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise ToolError(f"npm API returned HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.ConnectError:
        raise ToolError("Cannot connect to npm registry. Check network connectivity.")
    except httpx.TimeoutException:
        raise ToolError("npm registry request timed out after 25 seconds.")

    packages = [
        {
            "name": obj["package"]["name"],
            "version": obj["package"]["version"],
            "description": obj["package"].get("description", ""),
        }
        for obj in data.get("objects", [])
    ]
    return {"packages": packages, "total": data.get("total", len(packages))}
```

### Pattern 5: Data Processing (Transform + Pagination)

Use when the tool performs computation or transformation on local data and may return large results.

```python
import json
from fastmcp.exceptions import ToolError

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
async def aggregate_metrics(
    metric_name: Annotated[str, Field(
        description="Name of the metric to aggregate. Must exist in the metrics store.",
    )],
    group_by: Annotated[Literal["hour", "day", "week", "month"], Field(
        description="Time bucket for aggregation.",
    )] = "day",
    offset: Annotated[int, Field(description="Number of rows to skip for pagination.", ge=0)] = 0,
    limit: Annotated[int, Field(description="Max rows to return.", ge=1, le=500)] = 100,
    ctx: Context | None = None,
) -> dict:
    """Aggregate a named metric into time-bucketed summaries.

    Use when you need trend data or summary statistics for a metric over time.
    Do NOT use for raw event data -- use list_events instead. Returns a
    dictionary with 'buckets' (list of time, count, mean, min, max),
    'total_count', 'offset', 'limit', and 'has_more' for pagination.
    """
    all_data = await metrics_store.aggregate(metric_name, group_by=group_by)
    if not all_data:
        raise ToolError(f"Metric '{metric_name}' not found in the metrics store.")

    page = all_data[offset : offset + limit]
    return {
        "buckets": page,
        "total_count": len(all_data),
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < len(all_data),
    }
```

### Pattern 6: Dependency-Injected (Hidden Params via Depends)

Use when a tool needs runtime-resolved configuration, database connections, or authenticated clients that should NOT appear in the MCP schema.

```python
from fastmcp.dependencies import Depends

def get_api_config() -> dict:
    """Load API configuration from environment."""
    import os
    return {
        "base_url": os.environ["SERVICE_API_URL"],
        "api_key": os.environ["SERVICE_API_KEY"],
        "timeout": int(os.environ.get("SERVICE_TIMEOUT", "30")),
    }

@mcp.tool(
    timeout=30.0,
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
)
async def get_account_balance(
    account_id: Annotated[str, Field(
        description="Account identifier. Format: ACC-XXXXX.",
        pattern=r"^ACC-\d{5}$",
    )],
    config: dict = Depends(get_api_config),
    ctx: Context | None = None,
) -> dict:
    """Retrieve the current balance for an account.

    Use when you need to check an account's available and pending balance.
    Returns a dictionary with 'account_id', 'available', 'pending', and
    'currency' fields. Timeout: 30 seconds.

    The API configuration (URL, key) is injected automatically -- callers
    only provide the account_id.
    """
    async with httpx.AsyncClient(timeout=config["timeout"]) as client:
        resp = await client.get(
            f"{config['base_url']}/accounts/{account_id}/balance",
            headers={"Authorization": f"Bearer {config['api_key']}"},
        )
        resp.raise_for_status()
        return resp.json()
```

The `config` parameter is hidden from the MCP schema. Clients see only `account_id`. Dependencies resolve once per request and reuse the same instance across nested dependencies.

### Pattern 7: Sampling (LLM-in-the-Loop via ctx.sample)

Use when a tool needs to call the LLM to process, summarize, or transform data as part of its execution.

```python
from fastmcp import Context
from fastmcp.exceptions import ToolError

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def smart_summarize(
    document_path: Annotated[str, Field(
        description="Path to the document to summarize. Must be a text file.",
    )],
    max_sentences: Annotated[int, Field(
        description="Maximum number of sentences in the summary.",
        ge=1,
        le=20,
    )] = 5,
    ctx: Context | None = None,
) -> dict:
    """Summarize a document using LLM-powered analysis.

    Use when you need an intelligent summary that captures key themes and
    conclusions, not just the first N lines. Requires client-side sampling
    support. Do NOT use for binary files. Returns a dictionary with 'summary'
    (string) and 'sentence_count' (int).
    """
    if not ctx:
        raise ToolError("This tool requires MCP context for LLM sampling.")

    content = Path(document_path).read_text(encoding="utf-8")
    if len(content) > 100_000:
        content = content[:100_000] + "\n[TRUNCATED]"

    await ctx.info(f"Sampling LLM to summarize {document_path}")
    result = await ctx.sample(
        messages=[{
            "role": "user",
            "content": f"Summarize the following document in at most {max_sentences} sentences. "
                       f"Focus on key findings and conclusions.\n\n{content}",
        }],
        temperature=0.3,
    )

    summary_text = result.text if hasattr(result, "text") else str(result)
    sentences = [s.strip() for s in summary_text.split(".") if s.strip()]
    return {
        "summary": summary_text,
        "sentence_count": len(sentences),
    }
```

### Pattern 8: Elicitation (User Input via ctx.elicit)

Use when a tool needs interactive confirmation or additional input from the human user before proceeding.

```python
from fastmcp import Context
from fastmcp.exceptions import ToolError

@mcp.tool(
    annotations={
        "destructiveHint": True,
        "idempotentHint": False,
    },
)
async def delete_project(
    project_id: Annotated[str, Field(
        description="ID of the project to permanently delete.",
    )],
    ctx: Context | None = None,
) -> dict:
    """Permanently delete a project and all its associated data.

    Use only when explicit deletion is requested. This action is IRREVERSIBLE.
    The tool will ask the user for confirmation before proceeding. Returns a
    dictionary with 'deleted' (bool) and 'project_id'.
    """
    if not ctx:
        raise ToolError("This tool requires MCP context for user confirmation.")

    project = await fetch_project(project_id)
    if not project:
        raise ToolError(f"Project '{project_id}' not found.")

    # Ask the user for confirmation
    response = await ctx.elicit(
        message=f"Are you sure you want to permanently delete project '{project['name']}' "
                f"({project_id})? This will remove {project['file_count']} files and "
                f"{project['member_count']} member assignments. Type 'yes' to confirm.",
        response_type=str,
    )

    if response.action != "accept" or response.data.strip().lower() != "yes":
        return {"deleted": False, "project_id": project_id, "reason": "User cancelled deletion."}

    await ctx.info(f"Deleting project {project_id}")
    await perform_deletion(project_id)
    return {"deleted": True, "project_id": project_id}
```

---

## 10. Context-Optional Pattern

Make tools testable outside MCP by defaulting `ctx` to `None`. This allows calling the tool function directly in unit tests without spinning up an MCP server or mocking the context.

```python
from fastmcp import Context

@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
async def search_logs(
    query: Annotated[str, Field(description="Search query for log entries.")],
    ctx: Context | None = None,
) -> list[dict]:
    """Search server logs by keyword.

    Use when you need to find log entries matching a pattern. Returns a list
    of log objects with timestamp, level, and message fields.
    """
    if ctx:
        await ctx.info(f"Searching logs for: {query}")
        await ctx.report_progress(0, 100)

    results = await log_store.search(query)

    if ctx:
        await ctx.report_progress(100, 100)
    return results
```

**In tests -- no MCP runtime needed:**

```python
async def test_search_logs():
    # Direct call, no Context, no server
    results = await search_logs("error")
    assert isinstance(results, list)
```

**Under MCP -- context injected automatically:**

```python
# When called via MCP client, FastMCP injects Context automatically.
# The ctx parameter receives a live Context with logging, progress, etc.
result = await client.call_tool("search_logs", {"query": "error"})
```

Use `ctx: Context | None = None` for type-checker compatibility. FastMCP injects a live `Context` at runtime; the `None` default allows direct calls in tests.

---

## 11. Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Vague description: `"Does stuff with files"` | LLM cannot decide when to call it | Write 3-5 sentence description with WHAT/WHEN/WHEN NOT/RETURNS (Section 2) |
| Missing parameter descriptions | LLM guesses parameter values randomly | Add `Field(description=...)` to EVERY parameter (Section 3) |
| `print()` or `sys.stdout.write()` | Pollutes MCP protocol on stdio transport, corrupts JSON-RPC | Use `ctx.info()` / `ctx.warning()` / `ctx.error()` for logging |
| `*args` / `**kwargs` parameters | MCP requires fixed JSON schema; LLM cannot fill unstructured inputs | Use explicit typed parameters with descriptions |
| Response > 25K characters | Floods LLM context window, degrades reasoning quality | Paginate with offset/limit, truncate with note (Section 8) |
| Sync blocking in async tool | Blocks the event loop, freezes all concurrent tool calls | Use `await` with async I/O libraries (httpx, aiofiles, asyncpg) |
| Missing annotations | Client has no hints for confirmation flows, retry logic, or safety | Add `annotations` dict to every `@mcp.tool()` (Section 4) |
| Catching all exceptions (`except Exception: pass`) | LLM gets no feedback on failure; bugs are silenced | Use `ToolError` for expected errors, let unexpected ones propagate (Section 5) |
| Returning raw HTML/XML | LLMs struggle to parse markup reliably | Return structured `dict`, Markdown, or plain text |
| God tool that does everything | LLM picks wrong sub-behavior; description becomes a manual | Split into focused single-purpose tools (Section 12) |
| Boolean flag to switch behavior | Creates two tools masquerading as one; confuses tool selection | Split into separate tools or use `Literal` for distinct modes |
| No description at all (empty docstring) | Tool is invisible to LLM reasoning; selected at random or never | Every tool must have a multi-sentence docstring |

---

## 12. Tool Inventory Guidelines

### Organize as CRUD Sets Around Resources

```python
# Consistent resource-oriented naming
list_projects       # Read (collection)
get_project         # Read (single)
create_project      # Create
update_project      # Update
delete_project      # Delete
search_projects     # Search (if different from list)
```

### Server Sizing: 5-15 Tools

- **Fewer than 5** suggests the server is too narrow or underbuilt.
- **5-15** is the sweet spot. LLMs can hold the full tool list in working memory.
- **More than 15** overwhelms LLM tool selection. Split into composed sub-servers with `mcp.mount()` and namespaces.

### Build Order

Ship tools in this order. Each tier depends on the previous being stable.

1. **Read-only first** -- `list_*`, `get_*`, `search_*`. These are safe, idempotent, and testable. Get the data model right before building writes.
2. **Write tools** -- `create_*`, `update_*`. Add after reads are stable and the data model is proven.
3. **Destructive tools last** -- `delete_*`, `purge_*`, `overwrite_*`. Add only when needed. Mark every one with `destructiveHint=True`.

### One Tool, One Job

If a tool description contains "and" connecting two unrelated actions, split it.

- `search_and_delete_files` -- split into `search_files` + `delete_file`.
- `create_or_update_user` -- keep as `upsert_user` only if the backend is truly idempotent; otherwise split into `create_user` + `update_user`.
- `fetch_and_transform_data` -- split into `fetch_data` + `transform_data` unless the transform is inseparable from the fetch.
