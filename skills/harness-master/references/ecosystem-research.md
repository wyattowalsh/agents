# Ecosystem Research (legacy notes)

> **Dispatch:** use `references/discovery-pipeline.md` for mode, depth, and W0–W4 orchestration. Legacy CLI tokens (`research`, `candidate`, `compare`, `sources`) map to unified **Discover** via `scripts/discovery/classify_intent.py`.

Use this reference for W2 source-family detail when planning read-only scouts. Comparison and ranking still use `candidate_score.py` inside Discover W2b.

## Legacy CLI aliases (→ Discover depth)

- `research …` → focused
- `candidate …` → candidate
- `compare …` → compare
- `sources [category]` → sources catalog from `data/research-sources.json`

## Wave 0: Normalize And Plan

1. Normalize harness aliases and research category.
2. Run `discover_surfaces.py` for selected harnesses when local fit or overlap matters.
3. Load local registries:
   - `config/harness-surface-registry.json`
   - `config/plugin-extension-registry.json`
   - `config/mcp-registry.json`
   - `config/external-skills.md`
4. Build a source plan:
   ```bash
   uv run python skills/harness-master/scripts/source_probe.py --harness <harness|all> --source <source-id> --query "<query>" --dry-run --json
   ```
   Use `--list-sources --category <category> --json` when the user asks for `sources [category]`.
5. Treat missing optional credentials as degraded source status.

## Wave 1: Parallel Source Scouts

Split scouts by source family when runtime supports subagents or teams:

- official docs and `llms.txt`
- local repo registries and observed surfaces
- GitHub REST/search, repo APIs, issues, discussions, releases, and GraphQL enrichment
- MCP registries: official MCP Registry, Glama, PulseMCP, Smithery, Docker MCP Catalog
- Agent Skill hubs: skills.sh and `npx skills add <source> --list`
- package and security registries: npm, PyPI, Open VSX, Docker Hub/OCI, OSV, optional Socket/Snyk
- community feedback: Reddit, HN, blogs, vendor forums, and papers

Every dispatched scout must be resolved or explicitly skipped before Wave 4 synthesis.

## Wave 2: Deep-Dive Top Candidates

For each top candidate, collect:

- repository/package identity and canonical home
- install and config shape
- auth requirements and credential storage
- tool permissions and destructive capability
- update history, releases, changelog, and maintainer activity
- compatibility notes for each target harness
- known failures from issues, discussions, release notes, or docs
- validation path and rollback path

Use GitHub REST/search for broad discovery and code/file lookup. Use GitHub GraphQL after discovery to batch structured enrichment for known repositories: stars, forks, releases, topics, license, activity, issue/PR counts, and maintainer signals.

## Wave 3: Risk And Adoption Review

Review candidates against:

- support-tier policy
- one-owner-per-MCP rules
- duplicate/overlapping local registry entries
- credential exposure and auth bridging
- sandboxing and network/process isolation
- install friction and update channel
- rollback path
- fixture and eval readiness

Quarantine candidates that require credential proxying, auth bridging, offensive behavior, broad destructive tools, or broad filesystem/network permissions until isolation and validation are explicit.

## Wave 4: Synthesize

Produce an `Ecosystem Research Report` with:

- source plan
- candidate table
- per-candidate evidence dossier
- programmatic access status
- compatibility matrix by harness
- security and credential review
- recommended canonical home
- validation and rollback plan
- confidence and blocked evidence

Show patch previews only when they are backed by file and docs evidence. Do not apply them from research mode.

## Orchestration Semantics

- Use Pattern F semantics for explore -> score -> synthesize.
- Use Pattern E or nested waves when the runtime supports teams.
- In Plan Mode, scouts are read-only: no edits, installs, generated docs, or config mutation.
- Track every dispatched scout. Mark it resolved, skipped, or blocked before synthesis.
- If subagents are unavailable, maximize parallel read-only tool calls and keep source-family accounting in the report.

## Blocked Apply Rule

Research mode never authorizes implementation. If the user asks to apply research findings:

1. State that research is advisory.
2. Produce or rerun a matching dry-run audit for the exact harness, level, and candidate change.
3. Apply only after explicit approval of that dry-run audit.
