# MCP Security Controls

## Objective

Reduce MCP-specific risks while preserving live-systems utility.

## Required controls

- Curated allowlist.
- Version pinning where feasible.
- Transport classification.
- OAuth/secret handling review.
- Tool-description pinning/diffing.
- mcp-scan or equivalent scanner.
- Runtime sandboxing for local servers.
- No broad filesystem/network access without explicit policy.
- Audit log of enabled MCP servers and tools.
- Periodic drift checks against generated config.

## Risk categories

- token/secret exposure.
- scope creep.
- tool poisoning.
- supply-chain compromise.
- command injection.
- prompt injection/contextual payloads.
- auth/authz weaknesses.
- insufficient telemetry.
- shadow MCP servers.
- context over-sharing.

## Acceptance criteria

- Every MCP registry record has a threat note.
- Every promoted MCP has smoke tests and security classification.
- Every rejected/quarantined MCP has a reason.
