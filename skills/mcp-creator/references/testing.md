# Testing FastMCP v3 Servers

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

Patterns for writing automated tests against MCP servers using the FastMCP Client.
Read during test implementation or when reviewing a server's test coverage.

---

## 1. Anti-Pattern: Vibe Testing

"Vibe testing" = manually prompting an LLM to exercise your tools. This catches roughly 20% of issues. The other 80% hide in parameter validation, error paths, edge cases, and regressions that only surface after deployment.

MCP servers are API surfaces. Test them like APIs:

- **Parameter validation** -- missing required fields, wrong types, out-of-range values.
- **Error handling** -- bad input produces a `ToolError`, not an unhandled crash.
- **Edge cases** -- empty results, special characters, concurrent calls, boundary values.
- **Regressions** -- a passing test suite proves refactors did not break callers.

Test deterministically. Every tool call, every resource read, every prompt render -- automate it.

---

## 2. In-Memory Client Testing (Primary Pattern)

The FastMCP `Client` accepts a server instance directly as its transport. No network, no subprocess -- tests run in-process, fast and deterministic. The full MCP protocol is exercised (initialization, discovery, tool calls).

```python
import pytest
from fastmcp import FastMCP, Client

from server import mcp  # Import your FastMCP server instance

@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c

async def test_list_tools(client):
    tools = await client.list_tools()
    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert "my_tool" in tool_names

async def test_call_tool(client):
    result = await client.call_tool("my_tool", {"query": "test"})
    assert result.data is not None
```

Key details:

- `Client(mcp)` connects directly to the server object in-memory.
- `call_tool()` returns a `CallToolResult` with:
  - `.data` -- deserialized Python object (parsed from JSON text content).
  - `.content` -- raw MCP content blocks (list of `TextContent`, `ImageContent`, etc.).
  - `.is_error` -- boolean indicating tool failure.
- By default `call_tool()` raises `ToolError` on failure. Pass `raise_on_error=False` to inspect errors without exceptions.
- `call_tool_mcp()` returns the raw `mcp.types.CallToolResult` -- use only when you need the raw MCP protocol response (e.g., inspecting content block types directly, checking `isError` field).

```python
async def test_raw_mcp_result(client):
    result = await client.call_tool_mcp("my_tool", {"query": "test"})
    assert not result.isError
    assert result.content[0].type == "text"
    assert len(result.content[0].text) > 0
```

---

## 3. pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.25"]
```

With `asyncio_mode = "auto"`, every `async def test_*` function runs as an async test without needing the `@pytest.mark.asyncio` decorator on each one. Drop the decorator entirely -- it is redundant in auto mode and adds noise.

---

## 4. conftest.py Template

Place this file at `mcp/<name>/tests/conftest.py`. It provides reusable fixtures for every test module.

```python
import pytest
from unittest.mock import AsyncMock

from fastmcp import Client
from server import mcp


@pytest.fixture
async def client():
    """In-memory MCP client connected to the server.

    Handles full MCP lifecycle: initialize, use, shutdown.
    """
    async with Client(mcp) as c:
        yield c


@pytest.fixture
def mock_context():
    """Mock MCP Context for direct function calls.

    Stubs all Context methods so tools can be called without the MCP runtime.
    """
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.get_state = AsyncMock(return_value=None)
    ctx.set_state = AsyncMock()
    return ctx


@pytest.fixture(autouse=True)
async def reset_state():
    """Reset any shared state between tests.

    Add cleanup logic here for module-level caches, databases, etc.
    """
    yield
    # Add cleanup after each test:
    # e.g., cache.clear(), await db.rollback()
```

---

## 5. Eight Test Categories

### 5.1 Discovery

Verify all tools, resources, and prompts are registered and discoverable.

```python
async def test_tool_discovery(client):
    tools = await client.list_tools()
    expected = {"search_docs", "create_item", "delete_item"}
    actual = {t.name for t in tools}
    assert expected.issubset(actual), f"Missing tools: {expected - actual}"

async def test_resource_discovery(client):
    resources = await client.list_resources()
    uris = [str(r.uri) for r in resources]
    assert "config://settings" in uris

async def test_prompt_discovery(client):
    prompts = await client.list_prompts()
    names = [p.name for p in prompts]
    assert "code_review" in names

async def test_tool_descriptions_nonempty(client):
    tools = await client.list_tools()
    for tool in tools:
        assert tool.description, f"Tool '{tool.name}' has empty description"
```

### 5.2 Happy Path

Each tool with valid input returns the expected output format.

```python
async def test_search_returns_results(client):
    result = await client.call_tool("search_docs", {"query": "python"})
    assert isinstance(result.data, dict)
    assert "results" in result.data
    assert len(result.data["results"]) > 0

async def test_create_item_returns_id(client):
    result = await client.call_tool("create_item", {
        "name": "Test Item",
        "description": "A test item",
    })
    assert "id" in result.data
    assert isinstance(result.data["id"], str)
```

### 5.3 Error Handling

Invalid input produces `ToolError`, not unhandled crashes. Missing required parameters raise errors.

```python
async def test_missing_required_param(client):
    """Missing 'query' parameter must raise an error."""
    with pytest.raises(Exception):
        await client.call_tool("search_docs", {})

async def test_invalid_input_returns_error(client):
    """Empty query violates min_length constraint."""
    result = await client.call_tool(
        "search_docs", {"query": ""}, raise_on_error=False
    )
    assert result.is_error

async def test_not_found_returns_tool_error(client):
    """Nonexistent ID must produce ToolError, not a crash."""
    result = await client.call_tool(
        "get_item", {"item_id": "nonexistent-id"}, raise_on_error=False
    )
    assert result.is_error
    # Verify the error message is informative
    assert "not found" in str(result.content[0].text).lower()
```

### 5.4 Edge Cases

Empty strings, boundary values (ge/le limits), Unicode, large inputs, None where optional.

```python
async def test_empty_results(client):
    result = await client.call_tool("search_docs", {"query": "xyznonexistent"})
    assert result.data["results"] == []

async def test_special_characters(client):
    result = await client.call_tool("search_docs", {"query": "test & <script>"})
    assert not result.is_error

async def test_unicode_input(client):
    result = await client.call_tool("search_docs", {"query": "日本語テスト"})
    assert not result.is_error

async def test_boundary_limit_min(client):
    """Limit at lower bound (ge=1) must succeed."""
    result = await client.call_tool("search_docs", {"query": "test", "limit": 1})
    assert len(result.data["results"]) <= 1

async def test_boundary_limit_max(client):
    """Limit at upper bound (le=100) must succeed."""
    result = await client.call_tool("search_docs", {"query": "test", "limit": 100})
    assert not result.is_error

async def test_boundary_limit_exceeded(client):
    """Limit above upper bound must raise an error."""
    result = await client.call_tool(
        "search_docs", {"query": "test", "limit": 101}, raise_on_error=False
    )
    assert result.is_error

async def test_large_input(client):
    """Very large query string must not crash the server."""
    large_query = "a" * 10_000
    result = await client.call_tool(
        "search_docs", {"query": large_query}, raise_on_error=False
    )
    # Either succeeds or returns a clean ToolError -- never crashes
    assert isinstance(result.is_error, bool)
```

### 5.5 Resources

`read_resource(uri)` returns correct content and MIME type. Template resources expand parameters.

```python
async def test_read_resource(client):
    content = await client.read_resource("config://settings")
    assert content is not None
    assert len(content) > 0

async def test_resource_content_type(client):
    """Verify resource returns valid JSON."""
    import json
    content = await client.read_resource("config://settings")
    data = json.loads(content[0].text)
    assert isinstance(data, dict)

async def test_resource_template(client):
    """Template resource expands user_id parameter."""
    import json
    content = await client.read_resource("users://123/profile")
    data = json.loads(content[0].text)
    assert data["id"] == "123"

async def test_resource_not_found(client):
    """Nonexistent resource URI must raise an error."""
    with pytest.raises(Exception):
        await client.read_resource("config://nonexistent")
```

### 5.6 Prompts

`get_prompt(name, args)` returns expected messages with correct roles and content.

```python
async def test_prompt_returns_messages(client):
    result = await client.get_prompt("code_review", {"code": "x = 1"})
    assert len(result.messages) > 0

async def test_prompt_message_roles(client):
    result = await client.get_prompt("code_review", {"code": "x = 1"})
    roles = {m.role for m in result.messages}
    assert "user" in roles

async def test_prompt_content_includes_input(client):
    result = await client.get_prompt("code_review", {"code": "x = 1"})
    content = result.messages[0].content
    assert "x = 1" in str(content)

async def test_prompt_with_defaults(client):
    """Prompt with optional parameters uses correct defaults."""
    result = await client.get_prompt("summarize_pr", {"pr_number": 42})
    assert len(result.messages) > 0
```

### 5.7 Integration

Test tool chains -- output of one tool feeds into another. Test lifespan setup and teardown.

```python
async def test_tool_chain(client):
    """Create an item, then retrieve it by ID."""
    create_result = await client.call_tool("create_item", {
        "name": "Chain Test",
        "description": "Created for integration test",
    })
    item_id = create_result.data["id"]

    get_result = await client.call_tool("get_item", {"item_id": item_id})
    assert get_result.data["name"] == "Chain Test"

async def test_create_then_delete(client):
    """Full lifecycle: create, verify, delete, verify gone."""
    create_result = await client.call_tool("create_item", {
        "name": "Delete Me",
        "description": "Will be deleted",
    })
    item_id = create_result.data["id"]

    delete_result = await client.call_tool("delete_item", {"item_id": item_id})
    assert not delete_result.is_error

    get_result = await client.call_tool(
        "get_item", {"item_id": item_id}, raise_on_error=False
    )
    assert get_result.is_error

async def test_lifespan_resources():
    """Verify lifespan initializes and cleans up shared resources."""
    async with Client(mcp) as c:
        # If lifespan sets up an HTTP client, tools depending on it must work
        result = await c.call_tool("fetch_data", {"id": "1"})
        assert not result.is_error
    # After exiting the context, lifespan teardown has run.
    # Re-entering creates fresh resources.
    async with Client(mcp) as c:
        result = await c.call_tool("fetch_data", {"id": "1"})
        assert not result.is_error
```

### 5.8 Concurrent

Multiple simultaneous tool calls must not interfere with each other. Use `asyncio.gather()`.

```python
import asyncio

async def test_concurrent_reads(client):
    """Parallel read-only calls must not interfere."""
    tasks = [
        client.call_tool("search_docs", {"query": f"term_{i}"})
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)
    assert all(not r.is_error for r in results)
    assert len(results) == 10

async def test_concurrent_writes(client):
    """Parallel write calls must each produce a unique result."""
    tasks = [
        client.call_tool("create_item", {
            "name": f"Concurrent Item {i}",
            "description": f"Item {i}",
        })
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    ids = [r.data["id"] for r in results]
    assert len(set(ids)) == 5, "Concurrent writes produced duplicate IDs"

async def test_concurrent_mixed(client):
    """Mixed read/write operations must not corrupt state."""
    write_task = client.call_tool("create_item", {
        "name": "Mixed Test",
        "description": "Concurrent mixed test",
    })
    read_task = client.call_tool("search_docs", {"query": "test"})
    write_result, read_result = await asyncio.gather(write_task, read_task)
    assert not write_result.is_error
    assert not read_result.is_error
```

---

## 6. Context-Optional Pattern

Declare `ctx: Context | None = None` on tool functions to allow calling them directly in unit tests without the MCP runtime. This enables fast, focused unit tests alongside full-protocol integration tests.

```python
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

mcp = FastMCP("my-server")

@mcp.tool(annotations={"readOnlyHint": True})
async def my_tool(
    query: str,
    ctx: Context | None = None,
) -> dict:
    """Search for items by query."""
    if ctx:
        await ctx.info(f"Searching: {query}")
    results = await do_search(query)
    if not results:
        raise ToolError("No results found")
    return {"results": results}
```

```python
# In test -- call function directly, no MCP runtime
result = await my_tool(query="test", ctx=None)
assert result == {"results": ["item1", "item2"]}

# Or with mock context to verify logging
result = await my_tool(query="test", ctx=mock_context)
mock_context.info.assert_called_once_with("Searching: test")
```

This pattern is ideal for testing pure business logic without MCP overhead. Use in-memory `Client` tests (Section 2) for protocol-level verification.

---

## 7. Testing with Mocks

Patch external dependencies (HTTP clients, databases, APIs) -- not the MCP layer. The MCP protocol must be exercised end-to-end.

```python
from unittest.mock import AsyncMock, patch

async def test_with_mocked_api(client):
    """Mock the external API, exercise the full MCP path."""
    with patch("server.external_api.fetch", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": "mocked"}
        result = await client.call_tool("fetch_data", {"id": "42"})
        assert result.data["data"] == "mocked"
        mock.assert_called_once_with("42")

async def test_api_failure_produces_tool_error(client):
    """External failure must surface as ToolError, not unhandled exception."""
    with patch("server.external_api.fetch", new_callable=AsyncMock) as mock:
        mock.side_effect = ConnectionError("timeout")
        result = await client.call_tool(
            "fetch_data", {"id": "42"}, raise_on_error=False
        )
        assert result.is_error

async def test_database_mock(client):
    """Mock database queries to test without a running database."""
    with patch("server.db.query", new_callable=AsyncMock) as mock:
        mock.return_value = [{"id": "1", "name": "Test"}]
        result = await client.call_tool("search_items", {"query": "test"})
        assert len(result.data["items"]) == 1
        mock.assert_called_once()

async def test_mock_context_logging(mock_context):
    """Verify tool logs the expected messages via Context."""
    from server import search_items
    await search_items(query="test", ctx=mock_context)
    mock_context.info.assert_called()
    mock_context.error.assert_not_called()
```

---

## 8. Parametrized Testing

`@pytest.mark.parametrize` runs the same test function with multiple input/output combinations. Each parameter set is an independent test case with its own pass/fail status.

```python
@pytest.mark.parametrize("query,min_count", [
    ("python", 1),
    ("nonexistent_xyz", 0),
    ("rust", 1),
])
async def test_search_result_counts(client, query, min_count):
    result = await client.call_tool("search_docs", {"query": query})
    assert len(result.data["results"]) >= min_count

@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, -100, 0),
])
async def test_add(client, x, y, expected):
    result = await client.call_tool("add", {"x": x, "y": y})
    assert result.data == expected

@pytest.mark.parametrize("invalid_input", [
    {"query": ""},           # Empty string
    {"query": None},         # Null value
    {},                      # Missing required param
])
async def test_invalid_inputs(client, invalid_input):
    result = await client.call_tool(
        "search_docs", invalid_input, raise_on_error=False
    )
    assert result.is_error
```

---

## 9. Snapshot Testing

For tools returning complex or large outputs, save the expected output once and compare on subsequent runs. Catch unexpected regressions in output structure or content.

```python
import json
from pathlib import Path

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

def save_snapshot(name: str, data: dict):
    """Save expected output to a snapshot file."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    (SNAPSHOT_DIR / f"{name}.json").write_text(
        json.dumps(data, indent=2, sort_keys=True)
    )

def load_snapshot(name: str) -> dict:
    """Load expected output from a snapshot file."""
    return json.loads((SNAPSHOT_DIR / f"{name}.json").read_text())

async def test_complex_output_matches_snapshot(client):
    result = await client.call_tool("get_schema", {"table": "users"})
    snapshot_path = SNAPSHOT_DIR / "get_schema_users.json"

    if not snapshot_path.exists():
        # First run: save the snapshot
        save_snapshot("get_schema_users", result.data)
        pytest.skip("Snapshot created -- rerun to verify")

    expected = load_snapshot("get_schema_users")
    assert result.data == expected, (
        "Output differs from snapshot. "
        "If intentional, delete the snapshot file and rerun."
    )
```

Tip: Use `pytest-snapshot` or `syrupy` for more ergonomic snapshot management with automatic update flags (`--snapshot-update`).

---

## 10. MCP Inspector

`fastmcp dev inspector server.py` launches a browser-based interactive testing UI. Use it for exploratory testing alongside automated tests.

```bash
fastmcp dev inspector server.py
```

The Inspector provides:

- **Tool browser** -- list all registered tools with their schemas.
- **Tool executor** -- call tools with custom arguments, inspect results.
- **Resource browser** -- read resources by URI.
- **Prompt browser** -- render prompts with arguments.
- **Request/response inspector** -- view raw MCP protocol messages.

Use the Inspector when:

- Developing a new tool and iterating on its behavior.
- Debugging a test failure by manually reproducing the call.
- Demonstrating server capabilities to users.

Do NOT use the Inspector as a substitute for automated tests. It is a complement, not a replacement.

---

## 11. CLI Testing

Quick smoke tests from the command line without writing Python. Useful for CI pipelines and quick verification.

```bash
# List all registered tools, resources, and prompts
fastmcp list server.py

# Call a specific tool with JSON arguments
fastmcp call server.py tool_name '{"param": "value"}'

# Full server discovery (tools + resources + prompts + metadata)
fastmcp discover server.py

# Launch the Inspector UI
fastmcp dev inspector server.py
```

Example workflow for CI:

```bash
# Verify server starts and all components register
fastmcp list server.py | grep -q "search_docs" || exit 1

# Smoke-test a critical tool
fastmcp call server.py search_docs '{"query": "test"}' | grep -q "results" || exit 1
```

---

## 12. 18-Item What-to-Test Checklist

Run through this list before declaring a server's test suite complete:

1. All tools discoverable via `list_tools()`
2. All resources discoverable via `list_resources()`
3. All prompts discoverable via `list_prompts()`
4. Tool names match expected values exactly
5. Tool descriptions are non-empty strings
6. Required parameters enforced (missing param -> error)
7. Optional parameters use correct defaults
8. Happy path produces expected output format
9. Invalid input produces `ToolError`, not unhandled crash
10. Empty/null results handled gracefully
11. Special characters in input don't cause issues
12. Slow operations respect timeout settings
13. Resource URIs resolve correctly
14. Template resources expand parameters correctly
15. Prompts return valid message structures
16. Concurrent calls don't interfere with each other
17. Lifespan resources initialized and cleaned up properly
18. No stdout writes (verify with subprocess capture or log inspection)

Map each item to at least one test. If a checklist item has no corresponding test, write one.
