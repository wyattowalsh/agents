# Security Quarantine Checklist

## Scope

This checklist makes the existing quarantine register operational for downstream lanes. It does not edit quarantined skills, MCP servers, or external repos.

## Quarantine Triggers

- Credential, token, cookie, keychain, browser profile, or account proxy access.
- Offensive security, exploit, jailbreak, or red-team tooling.
- Live infrastructure mutation.
- Unpinned executable downloads or package-manager side effects.
- Broad filesystem traversal without scoped allowlist.

## Required Review

Every exception request must include:

- Source id and pinned provenance.
- Business need and safer alternatives considered.
- Exact executable surface and data access class.
- Secrets and redaction model.
- Sandboxing and network policy.
- Fixture evidence.
- Rollback/disable procedure.
- Expiration or re-review date.

## Default Decision

Quarantine is deny-by-default. A quarantined item can be referenced in planning docs, but cannot be installed, executed, promoted, or rendered as supported until an approved exception is recorded.
