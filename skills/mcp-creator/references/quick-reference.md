# Quick Reference: FastMCP v3 Essentials

Minimal examples to start without loading any reference file.

**Server:**
```python
from fastmcp import FastMCP, Context
mcp = FastMCP("my-server", instructions="Server description for clients.")
```

**Tool:**
```python
from typing import Annotated
from pydantic import Field
from fastmcp.exceptions import ToolError

@mcp.tool(annotations={"readOnlyHint": True})
async def get_item(
    item_id: Annotated[str, Field(description="Unique item identifier.")],
    ctx: Context | None = None,
) -> dict:
    """Retrieve an item by its ID.

    Use when you need to look up a specific item. Returns the item's
    full details including name, status, and metadata. Does not return
    archived items — use get_archived_item instead.
    """
    if ctx: await ctx.info(f"Fetching item {item_id}")
    item = await fetch_item(item_id)
    if not item: raise ToolError(f"Item {item_id} not found")
    return item
```

**Resource:**
```python
@mcp.resource("config://version", mime_type="text/plain")
def get_version() -> str:
    """Current server version."""
    return "1.0.0"
```

**Prompt:**
```python
from fastmcp.prompts import Message

@mcp.prompt
def analyze(topic: str) -> list[Message]:
    """Generate an analysis prompt."""
    return [Message(role="user", content=f"Analyze {topic} in detail.")]
```

**Context (lifespan):**
```python
from fastmcp.server.lifespan import lifespan

@lifespan
async def app_lifespan(server):
    import httpx
    async with httpx.AsyncClient() as client:
        yield {"http": client}

mcp = FastMCP("my-server", lifespan=app_lifespan)

@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def fetch_data(
    url: Annotated[str, Field(description="URL to fetch data from.")],
    ctx: Context | None = None,
) -> str:
    """Fetch data from an external URL."""
    http = ctx.lifespan_context["http"]
    resp = await http.get(url)
    return resp.text
```

**Test:**
```python
from fastmcp import Client
from server import mcp

async def test_get_item():
    async with Client(mcp) as c:
        result = await c.call_tool("get_item", {"item_id": "abc"})
        assert result.data is not None
        assert not result.is_error
```

**Run:**
```bash
fastmcp run server.py                               # stdio (default)
fastmcp run server.py --transport http --port 8000   # HTTP
fastmcp dev inspector server.py                      # Inspector UI
```
