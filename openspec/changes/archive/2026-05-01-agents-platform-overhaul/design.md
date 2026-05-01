# Design: Agents Platform Overhaul

## Architecture Layers

1. Repo inventory and OpenSpec reconciliation.
2. Canonical registry layer for harnesses, skills, MCP servers, plugins/extensions, docs artifacts, and external repo evaluations.
3. Skills-first extension decision tree.
4. MCP live-systems layer with explicit transport, auth, secrets, sandbox, and smoke-fixture requirements.
5. Native plugin and harness projection layer.
6. Transaction-safe config preview/apply/rollback layer.
7. CI, eval, observability, and run-graph layer.
8. Generated docs and AI instruction truth layer.

## Skills-First Decision Tree

Use an Agent Skill when the capability can be represented as instructions, deterministic scripts, references, templates, static analysis, local CLI automation, eval/checklist, or docs workflow.

Use MCP only when the capability requires live external state, browser/runtime state, authenticated SaaS, current search/docs, database/cloud/vector state, telemetry streams, or interactive external systems.

Use a native plugin only to project canonical repo assets into harness-specific packaging, UX, or runtime hooks.

## Support Tiers

- `validated`: implemented with conformance fixtures and validation commands.
- `repo-present-validation-required`: files exist in repo but require validation before support claims.
- `planned-research-backed`: backed by planning docs and source ledger but not implemented.
- `experimental`: present or planned for trial use with caveats.
- `unverified`: discovered but not reviewed.
- `unsupported`: explicitly not supported.
- `quarantine`: blocked from default install or promotion due auth, proxy, credential, offensive, or supply-chain risk.

## Dispatch Model

Parent OpenSpec change `agents-platform-overhaul` owns broad orchestration, source-of-truth vocabulary, wave sequencing, and conflict controls.

Child changes own lane-specific artifacts. Child teams update only their child folders, assigned manifests/fragments, fixtures, and implementation paths.

## External Repository Intake

External repositories remain discovery inputs until pinned source, license compatibility, security/provenance review, maintenance review, and conformance fixtures are complete. No external repository is installed or promoted by default.
