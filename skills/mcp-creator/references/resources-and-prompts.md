# Resources and Prompts

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

How to expose read-only data via MCP resources and reusable prompt templates via MCP prompts.
Read when implementing `@mcp.resource` or `@mcp.prompt` decorators.

## 1. Resources Overview

Resources expose read-only data to MCP clients. They are identified by URI and return content the client can read without side effects.

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.resource("config://app")
def get_config() -> dict:
    """Return application configuration."""
    return {"debug": False, "version": "1.0"}
```

**Key properties:**
- Resources are **read-only** — they expose data, not actions.
- Each resource has a **URI** (e.g., `config://app`, `file://data.json`).
- Resources can return `str`, `bytes`, `dict`, or any JSON-serializable type.
- Resources are listed by clients via `list_resources()` and read via `read_resource(uri)`.

## 2. Static Resources

For data that doesn't change:

```python
@mcp.resource("info://version")
def version() -> str:
    """Return the server version."""
    return "2.1.0"

@mcp.resource("data://schema")
def schema() -> dict:
    """Return the data schema."""
    return {
        "fields": ["id", "name", "email"],
        "types": {"id": "int", "name": "str", "email": "str"},
    }
```

## 3. Dynamic Resources (Templates)

Use URI templates with `{param}` placeholders for parameterized resources:

```python
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """Get profile for a specific user."""
    return fetch_profile(user_id)

@mcp.resource("reports://{year}/{month}")
def get_monthly_report(year: int, month: int) -> dict:
    """Get monthly report for the given period."""
    return generate_report(year, month)
```

Template resources appear as resource templates in client discovery. The client fills in parameters when reading.

## 4. Async Resources

Resources can be async:

```python
@mcp.resource("data://live-stats")
async def live_stats() -> dict:
    """Return live system statistics."""
    stats = await fetch_live_stats()
    return stats
```

## 5. Binary Resources

Return `bytes` for binary content. Set the MIME type via the decorator:

```python
@mcp.resource("images://logo", mime_type="image/png")
async def get_logo() -> bytes:
    """Return the application logo."""
    return Path("logo.png").read_bytes()
```

## 6. Resource Metadata

Add descriptions and MIME types for better client discovery:

```python
@mcp.resource(
    "data://metrics",
    description="Real-time application metrics including latency, throughput, and error rates.",
    mime_type="application/json",
)
async def metrics() -> dict:
    """Return current application metrics."""
    return await collect_metrics()
```

## 7. Prompts Overview

Prompts are reusable templates that clients can discover and fill in. They generate messages for LLM interactions.

```python
@mcp.prompt()
def analyze(topic: str) -> str:
    """Generate an analysis prompt for the given topic."""
    return f"Analyze the following topic in depth, covering key trends, challenges, and opportunities: {topic}"
```

## 8. Multi-Message Prompts

Return a list of message dicts for multi-turn prompts:

```python
from fastmcp.prompts import UserMessage, AssistantMessage

@mcp.prompt()
def code_review(code: str, language: str = "python") -> list:
    """Generate a code review prompt."""
    return [
        UserMessage(f"Review this {language} code for bugs, security issues, and style:\n\n```{language}\n{code}\n```"),
        AssistantMessage("I'll review this code systematically, checking for:"),
    ]
```

## 9. Prompt Parameters

Prompts accept typed parameters with defaults:

```python
@mcp.prompt()
def summarize(
    text: str,
    style: str = "concise",
    max_sentences: int = 5,
) -> str:
    """Summarize text in the given style."""
    return (
        f"Summarize the following text in a {style} style, "
        f"using at most {max_sentences} sentences:\n\n{text}"
    )
```

## 10. Resources vs. Tools

| Aspect | Resource | Tool |
|--------|----------|------|
| Purpose | Expose data | Perform actions |
| Side effects | None (read-only) | May have side effects |
| Parameters | URI template params | Function params with Field() |
| Discovery | `list_resources()` | `list_tools()` |
| Invocation | `read_resource(uri)` | `call_tool(name, args)` |
| Error handling | Raise exceptions | Raise `ToolError` |
| Annotations | N/A | `readOnlyHint`, `destructiveHint`, etc. |

**When to use resources:**
- Exposing configuration, schemas, or reference data
- Providing file contents or database records
- Any read-only data retrieval

**When to use tools:**
- Actions with side effects (create, update, delete)
- Complex queries with multiple parameters
- Operations needing progress reporting or logging

## 11. Testing Resources and Prompts

```python
import pytest
from fastmcp import Client
from server import mcp

@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c

async def test_list_resources(client):
    resources = await client.list_resources()
    uris = [r.uri for r in resources]
    assert "config://app" in uris

async def test_read_resource(client):
    result = await client.read_resource("config://app")
    assert result is not None

async def test_list_prompts(client):
    prompts = await client.list_prompts()
    names = [p.name for p in prompts]
    assert "analyze" in names

async def test_get_prompt(client):
    result = await client.get_prompt("analyze", {"topic": "AI safety"})
    assert len(result.messages) > 0
```
