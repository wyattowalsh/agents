---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Skill Signing and Provenance

## Goal

Make external skill installation reviewable, reproducible, and reversible.

## Proposed artifacts

```text
config/external-artifacts.lock.json
config/provenance/skills/<skill-id>.json
```

## Lock fields

```json
{
  "id": "vendor/skill",
  "source_url": "https://...",
  "resolved_ref": "git-sha-or-version",
  "sha256": "...",
  "license": "MIT",
  "reviewed_at": "2026-05-01",
  "reviewer": "external-skill-auditor",
  "trust_tier": "verified_maintainer"
}
```

## Verification hierarchy

1. signed release / Sigstore / cosign if available
2. git commit SHA pin
3. package lock hash
4. local checksum only

## CI gates

- Fail if a supported external skill has no lock entry.
- Fail if lock entry source URL and registry source URL diverge.
- Warn on stale verification date.
