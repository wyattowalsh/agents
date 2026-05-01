---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Support Tier Policy

## Objective

Define a shared vocabulary for implementation status, external ecosystem maturity, and documentation badges.

## Tiers

| Tier | Meaning | Required evidence | CI gate |
|---|---|---|---|
| `first_class` | Actively supported by repo code and docs | Authoritative source, adapter implementation, tests, docs | Full conformance |
| `validated` | Known-good external or harness integration | Authoritative source, manual validation, fixtures | Smoke + docs |
| `curated_review` | High-quality candidate under review | Trusted source, license, maintenance, risk notes | Metadata validation |
| `experimental` | Works or appears promising but unstable | Caveats documented | Non-blocking |
| `watchlist` | Discovery item only | Catalog entry | None |
| `unsupported` | Known incompatible or unsafe | Reason documented | None |

## Promotion rule

A component may move from discovery to supported only after all of these pass:

1. authoritative source verification
2. license and provenance review
3. security risk classification
4. clean-room install or render test
5. generated docs update
6. rollback path exists

## Demotion rule

Demote when:

- official docs change incompatibly
- install breaks in clean room
- security posture deteriorates
- maintainer activity stops for a high-risk dynamic component
- CI conformance fails repeatedly
