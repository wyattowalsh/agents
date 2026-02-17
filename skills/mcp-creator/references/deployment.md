# Deploying FastMCP v3 Servers

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

Practical deployment patterns for FastMCP servers: transports, CLI, HTTP/ASGI, client configuration, Docker, background tasks.
Read when choosing a transport, deploying to production, or configuring MCP clients.

## 1. Transport Selection

| Transport | Best For | Protocol | Status |
|-----------|----------|----------|--------|
| stdio | Local tools, CLI integrations, desktop apps | stdin/stdout | Recommended for local |
| Streamable HTTP | Remote servers, multi-client, web services | HTTP POST + SSE | Recommended for remote |
| SSE | Legacy remote servers | HTTP GET (SSE) + POST | Deprecated |

- **Default to stdio** for single-user local tools. The client spawns one process per session.
- **Use Streamable HTTP** for any server that needs remote access or multiple concurrent clients.
- **Never use SSE for new projects** -- it is deprecated in the MCP spec and will be removed.

## 2. Running with FastMCP CLI

```bash
fastmcp run server.py                                    # stdio (default)
fastmcp run server.py --transport http --port 8000       # Streamable HTTP
fastmcp run server.py --transport http --port 8000 --reload  # Hot-reload dev
fastmcp run server.py --with httpx --with beautifulsoup4 # Extra dependencies
fastmcp run server.py --with-requirements requirements.txt
fastmcp run server.py --python 3.12                      # Pin Python version
fastmcp run server.py -- --config config.json --debug    # Pass server args after --
```

The CLI auto-discovers FastMCP instances named `mcp`, `server`, or `app`. If the server module uses a different variable name, specify it via `fastmcp.json` `source.entrypoint` or pass `server.py:my_instance` directly.

## 3. Running with mcp.run()

```python
if __name__ == "__main__":
    mcp.run()                                          # stdio by default
    mcp.run(transport="http", host="127.0.0.1", port=8000)  # Streamable HTTP
```

For async contexts use `run_async()` -- do **not** call `mcp.run()` inside async functions:

```python
async def main():
    await mcp.run_async(transport="http", port=8000)
```

## 4. ASGI Deployment

Create a standard ASGI app with `mcp.http_app()`:

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")
# ... register tools, resources, prompts ...

app = mcp.http_app()                      # ASGI app at default path
app = mcp.http_app(path="/api/mcp/")      # Custom endpoint path
```

Deploy with uvicorn:

```bash
uvicorn server:app --host 127.0.0.1 --port 8000             # Development
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4   # Production
```

**Stateless mode** for horizontal scaling behind load balancers -- each request is self-contained with no server-side session state:

```python
mcp = FastMCP("my-server", stateless_http=True)
app = mcp.http_app()
```

Or set via environment variable:

```bash
FASTMCP_STATELESS_HTTP=true uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

**Mounting in FastAPI:**

```python
from fastapi import FastAPI
from fastmcp import FastMCP

mcp = FastMCP("my-server")
# ... register tools ...

mcp_app = mcp.http_app(path="/")
api = FastAPI(lifespan=mcp_app.lifespan)
api.mount("/mcp", mcp_app)
```

Pass the `mcp_app.lifespan` to FastAPI so server startup/shutdown hooks run correctly. The MCP endpoint is then available at `/mcp/`.

## 5. Custom Routes

Add non-MCP HTTP endpoints alongside the MCP server:

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})
```

**SECURITY: custom routes bypass MCP auth entirely.** Protect sensitive custom routes with manual authentication checks. See the auth reference for patterns.

## 6. fastmcp.json -- Full Schema

Declarative project configuration covering source location, environment, and deployment settings:

```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "path": "server.py",
    "entrypoint": "mcp"
  },
  "environment": {
    "python": "3.12",
    "dependencies": ["pandas>=2.0", "httpx"]
  },
  "deployment": {
    "transport": "stdio",
    "host": "127.0.0.1",
    "port": 8000,
    "log_level": "INFO",
    "env": {
      "API_KEY": "${API_KEY}",
      "DATABASE_URL": "${DATABASE_URL}"
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source.path` | string | Path to server module (required) |
| `source.entrypoint` | string | FastMCP instance name; auto-detects `mcp`, `server`, `app` |
| `environment.python` | string | Python version constraint |
| `environment.dependencies` | list | Additional pip dependencies |
| `deployment.transport` | string | `"stdio"`, `"http"`, or `"sse"` |
| `deployment.host` | string | Bind address (default `"127.0.0.1"`) |
| `deployment.port` | integer | Port number (default `8000` for HTTP) |
| `deployment.log_level` | string | Logging level: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
| `deployment.env` | object | Environment variables; supports `${VAR}` interpolation from host env |

Run with `fastmcp run` (auto-detects `fastmcp.json` in cwd) or `fastmcp run fastmcp.json` explicitly.

## 7. Client Configs

### stdio Transport

All stdio clients use the same JSON structure. The `command`/`args` pattern launches the server as a subprocess.

**Claude Desktop (macOS)** -- `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp/my-server", "python", "server.py"],
      "env": { "API_KEY": "your-key-here" }
    }
  }
}
```

**Claude Desktop (Windows)** -- `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\mcp\\my-server", "python", "server.py"],
      "env": { "API_KEY": "your-key-here" }
    }
  }
}
```

**Claude Code** -- `.claude/settings.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp/my-server", "python", "server.py"],
      "env": { "API_KEY": "your-key-here" }
    }
  }
}
```

**Cursor / VS Code** -- `.cursor/mcp.json` or VS Code MCP settings:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp/my-server", "python", "server.py"],
      "env": { "API_KEY": "your-key-here" }
    }
  }
}
```

### Streamable HTTP Transport

For remote servers, specify `url` instead of `command`/`args`:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:8000/mcp/",
      "transport": "streamable-http"
    }
  }
}
```

For authenticated remote servers, add headers:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://api.example.com/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer ${MCP_AUTH_TOKEN}"
      }
    }
  }
}
```

## 8. This Repo's MCP Conventions

Per AGENTS.md:

- MCP servers live in `mcp/<name>/`
- Entry point: `server.py` with `mcp = FastMCP("Name")`
- Config: `fastmcp.json` pointing to `server.py`
- Package: `pyproject.toml` with `fastmcp>=2` dependency (for v3 servers built with this skill, use `fastmcp>=3.0.0rc2`)
- Workspace: Root `pyproject.toml` includes `[tool.uv.workspace]` with `members = ["mcp/*"]`

Minimal `fastmcp.json` for this repo:

```json
{
  "source": { "path": "server.py", "entrypoint": "mcp" },
  "environment": { "dependencies": [] }
}
```

After creating a new MCP server:

1. Add `"mcp/<name>"` to root `pyproject.toml` workspace members
2. Run `uv sync` to install
3. Run `uv run wagents validate`

## 9. Development Workflow

Use the built-in development and inspection tools:

```bash
fastmcp dev inspector server.py            # Launch MCP Inspector UI in browser
fastmcp list server.py                     # List all registered tools, resources, prompts
fastmcp call server.py tool_name '{"param": "value"}'  # Call a tool directly
fastmcp discover server.py                 # Full discovery: components, schemas, metadata
```

The Inspector UI (`fastmcp dev inspector`) provides an interactive web interface for testing tools, viewing resource schemas, and debugging request/response cycles. Use it during development to validate tool behavior before connecting real clients.

## 10. Background Task Workers

Enable background task processing with Docket workers:

```bash
fastmcp tasks worker                       # Start a Docket worker
```

Configure the task backend via environment variables:

| Variable | Description | Examples |
|----------|-------------|----------|
| `FASTMCP_DOCKET_URL` | Task storage backend URL | `memory://`, `redis://localhost:6379`, `sqlite:///tasks.db` |

- Use `memory://` for development and testing (non-persistent, single-process only).
- Use `redis://` for production multi-worker setups.
- Use `sqlite:///` for persistent single-node deployments.

Enable tasks on the server:

```python
mcp = FastMCP("my-server", tasks=True)
# Optionally configure the Docket backend:
mcp = FastMCP("my-server", tasks=True, docket="redis://localhost:6379")
```

Worker count and queue configuration follow Docket conventions. Scale workers horizontally by running multiple `fastmcp tasks worker` processes against the same backend URL.

## 11. Docker Deployment

**Dockerfile:**

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY server.py .
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
```

In `server.py`, bind to `0.0.0.0` for container networking:

```python
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

**.dockerignore:**

```
__pycache__/
*.pyc
.git/
.env
.venv/
*.egg-info/
dist/
build/
.mypy_cache/
.pytest_cache/
```

**Notes:**

- Pin dependency versions with `uv.lock` (committed to repo).
- Bind to `0.0.0.0` inside Docker, never `127.0.0.1` (container-external traffic cannot reach loopback).
- Add a `/health` endpoint for container orchestration health checks (Section 5).
- Set `stateless_http=True` when running multiple replicas behind a load balancer.
- Pass secrets via environment variables at runtime, never bake them into the image.

## 12. Production Checklist

- [ ] `mask_error_details=True` set on the FastMCP constructor
- [ ] Annotations set on all tools (readOnlyHint, destructiveHint, etc.)
- [ ] All tool parameters have descriptions
- [ ] `asyncio_mode = "auto"` in pytest config
- [ ] Import check passes: `uv run python -c "from server import mcp"`
- [ ] `fastmcp list` shows expected components
- [ ] No deprecated constructor kwargs (v2 kwargs raise `TypeError` in v3)
- [ ] Custom routes have manual auth if needed (they bypass MCP auth)
- [ ] Secrets stored in environment variables only, not in code or config files
- [ ] Bind to `127.0.0.1` locally (or `0.0.0.0` only in Docker / behind a reverse proxy)
- [ ] Dependencies declared in both `pyproject.toml` and `fastmcp.json`
- [ ] Tests pass: `uv run pytest -v`
