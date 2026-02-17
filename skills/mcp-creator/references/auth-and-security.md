# Authentication and Security

> Targets FastMCP 3.0.0rc2. Verify exact signatures via Context7 before relying on bundled specs.

Practical security patterns for FastMCP v3 servers.
Read when implementing auth, handling secrets, or hardening a server for production.

## 1. Transport-Based Auth Strategy

| Transport | Auth Method | Notes |
|-----------|------------|-------|
| stdio | Environment variables | No MCP-level auth. Secrets loaded at startup. |
| Streamable HTTP | OAuth 2.1 / Bearer tokens | Full MCP auth flow with PKCE, DCR, token verification. |
| SSE (deprecated) | OAuth 2.1 / Bearer tokens | Legacy transport. Migrate to Streamable HTTP. |

Authorization checks require OAuth tokens from HTTP transports. In stdio mode, `get_access_token()` returns `None` and auth checks are skipped. Design servers to handle both modes gracefully (see Section 17: Dual-Mode Pattern).

## 2. Environment Variable Auth (stdio)

Read secrets at startup. Fail fast if required variables are missing. Never defer validation to tool invocation time.

```python
import os
import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("my-api")

API_KEY = os.environ.get("MY_API_KEY")
API_BASE = os.environ.get("MY_API_BASE", "https://api.example.com")

if not API_KEY:
    raise RuntimeError("MY_API_KEY environment variable required")

@mcp.tool
async def call_api(query: str) -> dict:
    """Call external API with authenticated requests.

    Use when you need to query the external service. Returns the JSON
    response body. Raises ToolError on HTTP failures.
    """
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}/data",
            headers=headers,
            params={"q": query},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()
```

Rules:
- Load ALL secrets from environment variables at module level.
- Fail with a clear error message if any required variable is missing.
- Never hardcode secrets in source code.
- Never log or return secrets in tool output.

## 3. OAuth 2.1 with PKCE

MCP uses OAuth 2.1 with Proof Key for Code Exchange (PKCE) for HTTP transport authentication. Key characteristics:

- **S256 challenge method** — Clients generate a `code_verifier`, derive a `code_challenge` via SHA-256, and send the challenge during authorization. The verifier is sent during token exchange. S256 is mandatory; `plain` is not supported.
- **Discovery flow** — Clients discover the authorization server via `/.well-known/oauth-authorization-server` on the MCP server's origin. FastMCP serves this automatically when an auth provider is configured.
- **Dynamic Client Registration (DCR)** — Clients register themselves at the `registration_endpoint` returned by discovery. This eliminates manual client setup. Not all providers support DCR (see Section 5 for proxying non-DCR providers).
- **RFC 8707 resource indicators** — Clients include a `resource` parameter in authorization and token requests, binding tokens to a specific MCP server URL. Prevents token reuse across unrelated servers.

FastMCP handles the server side of this flow automatically when you provide an `auth` parameter to the constructor. Configure token verification (Section 4), a built-in provider (Section 5), or a remote provider (Section 6) depending on your identity provider.

## 4. Token Verification (JWTVerifier)

Validate bearer tokens issued by an external identity provider. The server acts as a resource server only — it does not issue tokens.

```python
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier

verifier = JWTVerifier(
    jwks_uri=os.environ["JWT_JWKS_URI"],
    issuer=os.environ["JWT_ISSUER"],
    audience=os.environ["JWT_AUDIENCE"],
)

mcp = FastMCP("secure-server", auth=verifier)
```

JWTVerifier validates signature, expiration, and audience claims. Supported key sources:

| Key Source | Description |
|------------|-------------|
| JWKS endpoints | Auto-rotates keys by fetching from `jwks_uri`. Preferred for production. |
| Static public keys | RSA or ECDSA keys loaded at startup. Use when the IdP has no JWKS endpoint. |
| Symmetric keys | HMAC HS256/384/512. Use only for internal services with shared secrets. |

Prefer JWKS endpoints. They handle key rotation automatically without server restarts.

## 5. Built-in OAuth Providers

### GitHubProvider

```python
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider

auth = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url=os.environ.get("BASE_URL", "https://your-server.com"),
)

mcp = FastMCP("github-server", auth=auth)
```

### GoogleProvider

```python
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider

auth = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    base_url=os.environ.get("BASE_URL", "https://your-server.com"),
)

mcp = FastMCP("google-server", auth=auth)
```

### OAuthProxy (Other Providers)

For identity providers that do not support Dynamic Client Registration and have no built-in FastMCP provider, use `OAuthProxy` with explicit endpoint URLs and a token verifier:

```python
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.oauth_proxy import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier

verifier = JWTVerifier(
    jwks_uri="https://idp.example.com/.well-known/jwks.json",
    issuer="https://idp.example.com",
    audience="mcp-server",
)

auth = OAuthProxy(
    authorization_endpoint="https://idp.example.com/authorize",
    token_endpoint="https://idp.example.com/token",
    client_id=os.environ["IDP_CLIENT_ID"],
    client_secret=os.environ["IDP_CLIENT_SECRET"],
    token_verifier=verifier,
    base_url=os.environ.get("BASE_URL", "https://your-server.com"),
)

mcp = FastMCP("custom-idp-server", auth=auth)
```

## 6. Remote Auth (DCR-Compatible)

For identity providers supporting Dynamic Client Registration (Descope, WorkOS AuthKit). Clients register automatically — no manual client ID provisioning required.

```python
from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl

auth = RemoteAuthProvider(
    token_verifier=JWTVerifier(
        jwks_uri="https://auth.example.com/.well-known/jwks.json",
        issuer="https://auth.example.com",
        audience="mcp-server",
    ),
    authorization_servers=[AnyHttpUrl("https://auth.example.com")],
    base_url="https://your-server.com",
)

mcp = FastMCP("remote-auth-server", auth=auth)
```

`RemoteAuthProvider` delegates the entire OAuth flow (including DCR, authorization, and token endpoints) to the remote authorization server. The MCP server only verifies tokens using the supplied `token_verifier`.

## 7. Per-Component Auth

Control access per-tool, per-resource, or per-prompt with the `auth` parameter. Use scope-based checks with `require_scopes`.

> **Note:** `require_auth` was removed in beta 2. Use scope-based patterns instead.

### Tools

```python
from fastmcp.server.auth import require_scopes

@mcp.tool(auth=require_scopes("read"))
async def get_profile() -> dict:
    """Get user profile. Requires 'read' scope."""
    return {"user": "alice", "role": "member"}

@mcp.tool(auth=require_scopes("admin", "write"))
async def delete_user(user_id: str) -> str:
    """Delete a user. Requires both 'admin' and 'write' scopes."""
    return f"Deleted user {user_id}"
```

### Resources

```python
@mcp.resource("secret://config", auth=require_scopes("read"))
def secret_config() -> str:
    """Sensitive configuration data. Requires 'read' scope."""
    return '{"db_host": "internal.db.example.com"}'
```

### Prompts

```python
@mcp.prompt(auth=require_scopes("analyst"))
def financial_report(quarter: str) -> str:
    """Generate financial report prompt. Requires 'analyst' scope."""
    return f"Generate a financial report for {quarter}."
```

Unauthorized requests receive not-found responses and are filtered from list operations. The client never learns that a restricted component exists.

## 8. Custom Auth Checks

Any callable accepting `AuthContext` and returning `bool` works as an auth check. Use factory functions for parameterized checks. Pass a list of checks to combine with AND logic — all must pass.

```python
from fastmcp.server.auth import AuthContext

def require_premium_user(ctx: AuthContext) -> bool:
    """Allow only premium users."""
    if ctx.token is None:
        return False
    return ctx.token.claims.get("premium", False) is True

def require_access_level(min_level: int):
    """Factory: require a minimum access level claim."""
    def check(ctx: AuthContext) -> bool:
        if ctx.token is None:
            return False
        return ctx.token.claims.get("level", 0) >= min_level
    return check

@mcp.tool(auth=require_premium_user)
async def premium_feature() -> str:
    """Access premium content. Requires premium account."""
    return "Premium content"

@mcp.tool(auth=[require_scopes("admin"), require_access_level(5)])
async def advanced_admin_action() -> str:
    """Perform advanced admin action.

    Multiple checks combine with AND logic — all must pass.
    Requires 'admin' scope AND access level >= 5.
    """
    return "Done"
```

Raise `AuthorizationError` for explicit denial messages. Other exceptions are masked for security.

## 9. Server-Level Auth Middleware

Apply authorization globally instead of per-component. Use `AuthMiddleware` in the middleware list. Use `restrict_tag` for tag-based scope requirements — any component tagged with a specific tag requires the associated scopes.

```python
from fastmcp import FastMCP
from fastmcp.server.auth import require_scopes, restrict_tag
from fastmcp.server.middleware import AuthMiddleware

mcp = FastMCP(
    "enforced-auth-server",
    middleware=[
        AuthMiddleware(auth=require_scopes("api")),
        AuthMiddleware(auth=restrict_tag("admin", scopes=["admin"])),
    ],
)

@mcp.tool(tags={"admin"})
async def admin_action() -> str:
    """Perform admin action.

    Requires both 'api' scope (from global middleware) and 'admin' scope
    (from tag restriction).
    """
    return "Admin action completed"

@mcp.tool
async def public_action() -> str:
    """Perform public action. Requires only 'api' scope."""
    return "Public action completed"
```

Middleware checks run before per-component auth checks. A request must pass all middleware checks AND the component's own auth check to succeed.

## 10. Session-Based Visibility for Auth

Disable sensitive tools at startup. Enable them per-session after verifying the user's permissions. This provides defense-in-depth — even if auth checks fail, tools remain invisible until explicitly unlocked.

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("admin-server")

# Disable admin tools globally at startup
mcp.disable(tags={"admin"})

@mcp.tool(tags={"admin"})
async def wipe_database() -> str:
    """Wipe the entire database. Admin only."""
    return "Database wiped"

@mcp.tool(tags={"admin"})
async def rotate_keys() -> str:
    """Rotate all API keys. Admin only."""
    return "Keys rotated"

@mcp.tool
async def unlock_admin(ctx: Context) -> str:
    """Unlock admin tools for this session.

    Verify the user has admin permissions, then enable admin-tagged
    tools for the current session only. Other sessions are unaffected.
    """
    # Verify user has admin permissions (check token, role, etc.)
    await ctx.enable_components(tags={"admin"})
    return "Admin tools unlocked for this session"
```

Session visibility changes are scoped to the individual connection. Other sessions remain unaffected. Clients receive automatic `list_changed` notifications when visibility changes.

## 11. Custom Route Auth Bypass

> **SECURITY WARNING:** `@mcp.custom_route()` routes bypass MCP OAuth entirely. These routes are raw Starlette endpoints with no automatic authentication. Protect sensitive custom routes manually.

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint. PUBLIC — no MCP auth applied."""
    return JSONResponse({"status": "ok"})

@mcp.custom_route("/admin/reset", methods=["POST"])
async def admin_reset(request: Request) -> JSONResponse:
    """Admin reset endpoint.

    MUST manually verify auth — MCP OAuth does NOT apply here.
    """
    token = request.headers.get("Authorization")
    if not token or not verify_admin_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    # Perform reset logic
    return JSONResponse({"status": "reset complete"})
```

Rules for custom routes:
- Assume every custom route is public by default.
- Add explicit authentication checks to any route that accesses or modifies sensitive data.
- Document whether each route is intentionally public or requires auth.
- Prefer MCP tools over custom routes when possible — tools get auth for free.

## 12. Input Validation

Validate all tool inputs at the boundary. Use Pydantic constraints in type annotations.

```python
from typing import Annotated, Literal
from pathlib import Path
from pydantic import Field
from fastmcp.exceptions import ToolError

WORKSPACE_ROOT = Path("/safe/workspace")

@mcp.tool
async def read_file(
    path: Annotated[str, Field(
        description="File path relative to workspace root.",
        pattern=r'^[a-zA-Z0-9_/.-]+$',
    )],
    encoding: Literal["utf-8", "ascii", "latin-1"] = "utf-8",
    max_lines: Annotated[int, Field(
        description="Maximum lines to read.",
        ge=1,
        le=10000,
    )] = 1000,
) -> str:
    """Read file contents safely within the workspace."""
    resolved = (WORKSPACE_ROOT / path).resolve()
    if not resolved.is_relative_to(WORKSPACE_ROOT):
        raise ToolError("Path outside workspace")
    if not resolved.exists():
        raise ToolError(f"File not found: {path}")
    return resolved.read_text(encoding=encoding)
```

Validation patterns:
- `Field(pattern=...)` — Constrain string formats with regex.
- `Literal[...]` — Restrict to a fixed set of allowed values.
- `Field(ge=, le=)` — Set numeric bounds.
- Runtime path validation — Always resolve and check against a root directory.
- **NEVER use string interpolation for database queries** — Use parameterized queries exclusively.

```python
# WRONG — SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# CORRECT — parameterized query
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
```

## 13. SSRF Prevention

Validate all URLs before making outbound requests. Block cloud metadata endpoints and private IP addresses.

```python
import ipaddress
from urllib.parse import urlparse
import httpx
from fastmcp.exceptions import ToolError

BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal"}
BLOCKED_PREFIXES = ("http://169.254.", "http://10.", "http://192.168.", "http://172.16.")

def validate_url(url: str) -> str:
    """Reject requests to cloud metadata endpoints and private IPs."""
    parsed = urlparse(url)

    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        raise ToolError("Only HTTP and HTTPS URLs are allowed")

    if parsed.hostname in BLOCKED_HOSTS:
        raise ToolError("Blocked host")

    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ToolError("Private/loopback/link-local IP not allowed")
    except ValueError:
        pass  # Not an IP literal — hostname is acceptable

    return url

@mcp.tool
async def fetch_url(url: str) -> str:
    """Fetch content from an external URL."""
    url = validate_url(url)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0, follow_redirects=False)
        resp.raise_for_status()
        return resp.text
```

Additional SSRF defenses:
- Disable redirect following (`follow_redirects=False`) or re-validate after each redirect.
- Set strict timeouts to prevent slowloris-style attacks.
- Allowlist known-good domains when possible.

## 14. DNS Rebinding Protection

DNS rebinding attacks trick a server into making requests to internal resources by manipulating DNS resolution.

- Bind to `127.0.0.1`, never `localhost`. DNS can resolve `localhost` to arbitrary IPs.
- For HTTP transport, validate the `Host` header against expected values.
- FastMCP handles this by default when using `mcp.run()`.

```python
# WRONG — vulnerable to DNS rebinding
mcp.run(transport="http", host="localhost", port=8000)

# CORRECT — bind to explicit IP
mcp.run(transport="http", host="127.0.0.1", port=8000)
```

For production deployments behind a reverse proxy, configure the proxy to validate `Host` headers and reject unexpected values.

## 15. Secrets Management

| Environment | Strategy |
|-------------|----------|
| Development | `.env` files (never commit to version control) |
| CI/CD | Pipeline secrets / environment variables |
| Production | Secret managers (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager) |

Rules:
- **Never hardcode secrets** in source code, config files, or comments.
- **Never log secrets.** Use `ctx.debug()` carefully — ensure no sensitive values leak into log messages.
- **Never return secrets in tool output.** Mask sensitive fields before returning data to clients.
- **Rotate secrets regularly.** Automate rotation through your secret manager.
- **Use `mask_error_details=True` in production** to hide internal error details (including potential secret leaks in stack traces) from clients.

```python
mcp = FastMCP(
    "production-server",
    mask_error_details=True,  # Hide internal errors from clients
)
```

## 16. Development Auth Helpers

Use `StaticTokenVerifier` for local development and tests. This verifier accepts predefined tokens without cryptographic validation.

> **NEVER use `StaticTokenVerifier` in production.** It provides no real security.

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

verifier = StaticTokenVerifier(
    tokens={
        "dev-token-alice": {
            "client_id": "alice@dev.local",
            "scopes": ["read", "write", "admin"],
        },
        "dev-token-bob": {
            "client_id": "bob@dev.local",
            "scopes": ["read"],
        },
    },
    required_scopes=["read"],
)

mcp = FastMCP("dev-server", auth=verifier)
```

Use environment variables or a feature flag to switch between `StaticTokenVerifier` (dev) and a real verifier (production). See Section 17 for the dual-mode pattern.

## 17. Dual-Mode Pattern

Maintain a shared module with tool registrations and separate entry points for authenticated and unauthenticated modes. This keeps tool logic DRY while supporting both local development and production deployments.

```python
# common.py — shared tool registrations
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

def register_all(mcp: FastMCP):
    """Register all tools, resources, and prompts on the given server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def search_items(
        query: Annotated[str, Field(description="Search query", min_length=1)],
    ) -> dict:
        """Search for items by keyword."""
        return {"results": [], "query": query}

    @mcp.tool(auth=require_scopes("admin"))
    async def delete_item(
        item_id: Annotated[str, Field(description="Item to delete")],
    ) -> str:
        """Delete an item. Requires admin scope."""
        return f"Deleted {item_id}"
```

```python
# main.py — production entry point (with OAuth)
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from common import register_all

verifier = JWTVerifier(
    jwks_uri=os.environ["JWT_JWKS_URI"],
    issuer=os.environ["JWT_ISSUER"],
    audience=os.environ["JWT_AUDIENCE"],
)

mcp = FastMCP("server", auth=verifier, mask_error_details=True)
register_all(mcp)
```

```python
# main_noauth.py — development entry point (no auth)
from fastmcp import FastMCP
from common import register_all

mcp = FastMCP("server-dev")
register_all(mcp)
```

Run with:
```bash
# Production
fastmcp run main.py

# Development (no auth)
fastmcp run main_noauth.py
```

Per-component `auth` checks (like `require_scopes("admin")`) are automatically skipped in stdio mode where `get_access_token()` returns `None`.

## 18. Security Rules (Non-Negotiable)

1. **No token passthrough.** Auth happens at the transport level, not in tool parameters. Never accept API keys, tokens, or passwords as tool inputs.
2. **Minimal scopes.** Request only the OAuth scopes the server actually needs. Avoid blanket `admin` scopes unless required.
3. **Bind to 127.0.0.1.** Never bind HTTP servers to `0.0.0.0` without explicit intent and documented justification.
4. **Secrets in environment only.** Use environment variables or secret managers. Never hardcode secrets in source code, config files, or tool descriptions.
5. **Use `mask_error_details=True` in production.** Prevent internal error details, stack traces, and potential secret leaks from reaching clients.
6. **Restrict redirect URIs.** Use `allowed_client_redirect_uris` to limit OAuth callback URLs. Prevent open redirectors.
7. **Prefer token verification over full OAuth server.** `OAuthProvider` (full authorization server) is extremely advanced and error-prone. Use `JWTVerifier`, `OAuthProxy`, or `RemoteAuthProvider` instead.
8. **Validate all file paths.** Resolve paths and check containment within an allowed root directory. Prevent path traversal attacks (`../../../etc/passwd`).
9. **Sanitize all URLs.** Validate schemes, block private IPs, block cloud metadata endpoints. Prevent SSRF attacks.
10. **No secrets in tool output.** Never return API keys, tokens, passwords, or connection strings in tool responses. Mask sensitive fields before returning.
11. **Parameterize all queries.** Never use string interpolation or f-strings for SQL, shell commands, or other injectable contexts. Use parameterized queries exclusively.
12. **Protect custom routes.** `@mcp.custom_route()` bypasses MCP OAuth. Add manual auth checks to sensitive custom routes.
13. **Set timeouts on all outbound requests.** Prevent tools from hanging indefinitely on slow or malicious external services.
14. **Log access, not secrets.** Log tool invocations and auth decisions for audit trails. Never log token values, API keys, or credentials.
15. **Rotate secrets regularly.** Automate rotation through secret managers. Design servers to reload credentials without restarts when possible.
