# Source Profiles

Use this reference with `data/research-sources.json` to decide which sources to probe, how to interpret evidence, and how to degrade confidence when access is blocked.

## Authority Tiers

- `primary`: official harness docs, `llms.txt`, official package or registry APIs, and local repo registries that define canonical ownership.
- `registry`: vendor-neutral or ecosystem registries with machine-readable metadata.
- `enrichment`: GitHub, package metadata, changelogs, releases, issues, discussions, downloads, stars, and maintainer signals.
- `security`: vulnerability and supply-chain feeds.
- `community`: Reddit, HN, blogs, vendor forums, and papers. These are advisory only.

## Programmatic Access Status

- `ready`: dry-run has a URL or command and no required env var is missing.
- `missing-env`: optional credential is absent. Lower confidence unless other sources corroborate the same evidence.
- `rate-limited`: source is reachable but temporarily constrained.
- `unavailable`: source cannot be reached or no longer exposes the expected endpoint.
- `manual-only`: source is useful but has no stable machine-readable access.
- `skipped`: source was irrelevant to the selected category or harness.

## Source Families

### Official Docs And `llms.txt`

Use first for semantics, config fields, support boundaries, and deprecation status. If `llms.txt` is absent, use first-party docs and canonical vendor repositories.

### Local Repo Registries

Use before external discovery to prevent duplicate owners, generated-file drift, and repo/global confusion. These are the highest authority for local fit and canonical home.

### GitHub

Use REST search for broad discovery with `topic:`, `stars:`, `pushed:`, `license:`, `in:readme`, org/user scopes, and code/file lookup. Use GraphQL after candidate discovery for batched enrichment of known repositories.

GraphQL is not a full replacement for REST search. It is best for stars, forks, releases, topics, license, activity, issues/PRs, and maintainer signals in one query.

### MCP Registries

Compare official MCP Registry, Glama, PulseMCP, Smithery, and Docker MCP Catalog when researching MCP candidates. Prefer candidates with corroborated identity, tool schemas, auth requirements, lifecycle status, provenance, and isolation metadata.

### Agent Skill Sources

Use skills.sh API for search, details, tree, and audit metadata. Use `npx skills add <source> --list` as source-list truth before installing or auditing external skills. Route third-party adoption through `external-skill-auditor` and `config/external-skills.md`.

### Package And Extension Registries

Use npm, PyPI, Open VSX, Docker Hub/OCI, and OSV to verify package identity, install surface, release recency, maintainers, downloads, versions, vulnerabilities, image provenance, and extension availability.

### Community And Papers

Use community and academic/security sources for investigation priority, risk models, and failure reports. They cannot promote adoption without official, local, registry, package, or security corroboration.

## Degraded Source Handling

When a source is degraded:

1. Keep the source in the plan with blocked evidence listed.
2. Lower confidence for fields that source would have provided.
3. Do not fail the whole report unless all primary sources for the question are unavailable.
4. Prefer `inspect`, `docs-only`, or `quarantine` over `adopt` when important evidence is blocked.
