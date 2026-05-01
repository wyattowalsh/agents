# MCP Audit Control Plane

## Scope

This lane classifies MCP servers by live-state necessity, transport, authentication, secret handling, sandbox needs, smoke fixtures, and skill-replacement opportunities. It does not edit live MCP config in this pass.

## MCP Inventory Model

Every MCP record must capture:

- Server id and canonical registry source.
- Command or remote URL shape.
- Transport type: stdio, HTTP, browser endpoint, desktop integration, or cloud API.
- Auth model: none, env var, OAuth, browser profile, keychain, cloud account, or local socket.
- Data sensitivity: public docs, repo files, browser state, SaaS account, filesystem, credentials, or live infrastructure.
- Live-state necessity and skill-replacement status.
- Smoke fixture and rollback requirement.

## Live-State Necessity

| Classification | Use When | Default Action |
| --- | --- | --- |
| `live-required` | Tool needs current browser, account, database, SaaS, or environment state. | Keep as MCP with smoke fixture and redaction gates. |
| `docs-or-static` | Tool primarily retrieves docs or static reference content. | Prefer skill/reference or deterministic CLI unless freshness requires MCP. |
| `repo-local` | Tool analyzes local files. | Prefer repo CLI or skill unless MCP provides unique structured access. |
| `secret-adjacent` | Tool can access credentials, profiles, tokens, or private accounts. | Route through security quarantine before support-tier promotion. |
| `redundant` | Another supported tool covers the same behavior with lower risk. | Mark for replacement or disablement. |

## Risk Matrix

| Risk | Evidence To Capture | Required Gate |
| --- | --- | --- |
| Secret exposure | Env keys, credential files, browser profiles, OAuth scopes. | Redaction fixture and quarantine review when secret-adjacent. |
| Live mutation | Write/delete/update tool capabilities. | Approval policy and rollback path. |
| Network dependency | Remote endpoint, package install, cloud service. | Timeout, retry, and offline behavior. |
| Filesystem breadth | Allowed roots and blocked paths. | Scope fixture and no-secret path check. |
| Generated config drift | Source registry and rendered target. | Idempotence and diff fixture. |

## Skill Replacement Candidates

MCP servers should be considered for skill replacement when they only provide static instructions, deterministic docs, or local file transformations that do not need live state. Replacement candidates must include a migration note and a no-behavior-loss fixture before removal.

## Smoke Fixture Requirements

Each retained MCP requires a smoke fixture defining:

- Minimal invocation that proves startup.
- Expected non-secret output.
- Failure mode when auth is missing.
- Redacted logs.
- Rollback or disable path.

## Security Boundary

Do not read local secret files during audit. Record path patterns, env var names, and access classes without exposing values.
