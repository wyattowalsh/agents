---
skill: insecure-defaults
source_type: curated-external
researched_at: '2026-06-16T20:03:00Z'
research_tier: standard
mean_confidence: 0.73
---

## Purpose

Detects insecure default configurations causing vulns: hardcoded secrets/fallbacks, default creds (admin/admin), weak crypto (MD5/DES/ECB), permissive access (CORS *), fail-open patterns vs fail-secure. Scans manifests, env handling, auth, third-party integrations. Trail of Bits.

## Harness Coverage

Security/config audit agents.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Broad applicability leads to context-dependent findings; low direct exec surface but config changes could be sensitive. policy=Inspect source/hooks/dedupe.; evidence=trailofbits/skills batch + https://github.com/trailofbits/skills/plugins/insecure-defaults .

## Install Prerequisites

Grouped in `npx skills add trailofbits/skills --skill ... insecure-defaults ...` status=inspect-then-install; selector=named.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills).

## Comparable Alternatives

`secrets-management`, `sast-configuration`, `semgrep`/`codeql`. General "insecure defaults" instruction.

> Web evidence from repo plugin README.
