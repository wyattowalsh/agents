# Config Transaction Blueprint

## Scope

This blueprint defines preview/apply/rollback behavior for repo-managed and user-owned config surfaces. It does not mutate live user config in this pass.

## Transaction Operation Model

Each config operation has:

- Operation id, harness id, target path, target scope, and owner lane.
- Mode: `preview`, `apply`, `rollback`, or `verify`.
- Input source: canonical registry, instruction source, plugin manifest, or user-owned existing file.
- Rendered diff with secret-safe summaries.
- Backup reference before apply.
- Rollback command or restoration procedure.

## Backup Snapshot Format

Backups must capture:

- Target path and scope.
- File hash before apply.
- Redacted preview of changed keys.
- Timestamp and tool version.
- Restore path or serialized prior content stored outside public logs.

## Redaction And Environment Overlay

- Env var names can be printed; values cannot.
- Secrets, tokens, cookies, browser profile data, and keychain values are excluded.
- Local user values override repo defaults only at render/apply time.
- Repo-managed config must keep placeholder syntax when committed.

## Sandbox Profiles

| Profile | Use |
| --- | --- |
| `repo-preview` | Render config without writes. |
| `repo-apply` | Write repo-owned generated files only. |
| `home-preview` | Read user config metadata and show redacted planned changes. |
| `home-apply` | Requires explicit approval and backup. |
| `quarantine` | Used for secret-adjacent or live-risk surfaces. |

## Policy Exceptions

Exceptions require owner, reason, expiry, rollback, and security review when secret-adjacent. Plan mode and dry-run mode are no-touch for live user configs.

## Global Desktop Config Rules

Global desktop surfaces, such as Claude Desktop, Cherry Studio, Gemini-compatible desktop settings, and browser-profile-backed MCP launchers, require the strictest transaction shape:

- `preview` is mandatory before `apply`.
- `apply` requires explicit user approval in the active session.
- Backup snapshots must be created before writes.
- Diff output must show changed keys and path classes, not credential values.
- Rollback must restore the previous file or disable the generated block.
- Plan mode and dry-run mode cannot write global desktop config.

## Per-Harness Redaction Fixtures

Each harness fixture must assert redaction for its secret-adjacent fields:

| Harness Class | Redacted Fields |
| --- | --- |
| Desktop MCP apps | Env values, OAuth tokens, profile directories, local sockets with private paths. |
| Browser automation | Cookie stores, browser profile paths, debugging endpoints when private. |
| CLI harnesses | API tokens, config secrets, local provider keys, auth cache paths. |
| Plugin surfaces | Marketplace tokens, install credentials, package-manager auth, webhook secrets. |

Fixtures should verify both success and failure output avoid raw secrets.
