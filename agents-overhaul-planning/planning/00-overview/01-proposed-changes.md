# Proposed Changes and Refinements

## 1. Repo synchronization and truth model

### Change

Add a repo-sync step that inventories the live repository before every planning or implementation wave.

### Refined behavior

- Scan top-level folders, harness-specific folders, `skills/`, `mcp/`, `config/`, `instructions/`, `wagents/`, `tests/`, `docs/`, `.github/`, and OpenSpec assets.
- Detect generated-vs-source docs.
- Detect raw README and rendered README drift.
- Detect harness support claims that do not have corresponding config, docs, tests, or validation gates.

### Acceptance criteria

- `planning/00-overview/05-repo-sync-analysis.md` is regenerated from current repo state.
- `planning/manifests/repo-sync-inventory.json` exists.
- Every planning claim about a repo path is backed by the inventory.

## 2. Skills-first extension model

### Change

Promote Agent Skills to the default reusable capability mechanism.

### Refinement

Skills are preferred when the capability is:

- static or semi-static knowledge;
- documentation, instruction, or prompt workflow;
- CLI-backed and deterministic;
- executable locally with explicit arguments;
- testable in CI without long-lived network services;
- portable across multiple harnesses.

### Acceptance criteria

- Every existing skill package passes Agent Skills metadata validation.
- Every external candidate is classified as `adopt`, `adapt`, `watch`, `reject`, or `replace-mcp`.
- Each skill has CLI conformance tests when it uses executable scripts.

## 3. MCP as live-systems layer

### Change

Reclassify MCP servers as a secondary layer for live external state.

### Refinement

MCP remains appropriate for:

- browser runtime automation;
- authenticated SaaS APIs;
- live GitHub/issue/CI/cloud state;
- current documentation/search;
- databases/vector stores/search indexes;
- observability/telemetry streams.

MCP is not preferred for static docs, reusable prompts, local scripts, coding playbooks, checklists, or deterministic transformations.

### Acceptance criteria

- Every MCP candidate has domain, auth model, transport, trust tier, install command, sandbox requirements, and replacement-by-skill assessment.
- MCP index entries are treated as discovery leads only, never as safety endorsement.

## 4. Canonical harness registry

### Change

Create a single registry that models harness support tiers, install paths, config scopes, extension surfaces, and validation gates.

### Refinement

Support statuses:

- `validated`: implemented and tested.
- `repo-present-validation-required`: repo artifact exists but end-to-end support still needs tests.
- `planned-research-backed`: official docs exist but repo projection is not complete.
- `experimental`: preview or unstable surface.
- `unverified`: repo artifact or community signal exists, but authoritative contract is missing.
- `unsupported`: intentionally not handled.

### Acceptance criteria

- `planning/manifests/harness-registry.yaml` is the source of truth.
- `planning/20-harness-registry/00-capability-matrix.md` is generated from that manifest.
- No doc claims full support unless the registry says `validated`.

## 5. Adapter layer

### Change

Add an adapter architecture that projects canonical capabilities into harness-specific surfaces.

### Refinement

Adapters should be pure renderers where possible:

- Input: canonical registry + selected overlays + environment facts.
- Output: proposed file writes/config updates + tests.
- Side effects only through transaction engine.

Adapter lanes:

- Skill adapter.
- Plugin adapter.
- MCP adapter.
- OpenAPI/function-calling adapter.
- CLI adapter.
- Instruction/rules adapter.
- OpenSpec adapter.

### Acceptance criteria

- Each adapter has schema tests, golden fixtures, and merge-safe output paths.

## 6. Transaction-safe config UX

### Change

Implement config operations as transactions.

### Flow

1. Detect harnesses and installed state.
2. Resolve desired state from registry and overlays.
3. Render candidate changes.
4. Show diff/preview.
5. Backup current files.
6. Apply atomically.
7. Validate.
8. Roll back automatically on failure.
9. Emit audit log.

### Acceptance criteria

- `wagents sync --preview` never writes.
- `wagents sync --apply` writes only through transaction engine.
- `wagents rollback` restores the latest known-good snapshot.

## 7. UI/UX simplification

### Change

Design the CLI and optional dashboard around a small set of clear verbs.

### UX verbs

- `doctor`: inspect state.
- `catalog`: browse skills, MCPs, plugins, and harness support.
- `install-skill`: install/pin/verify skill.
- `sync`: preview/apply harness configs.
- `rollback`: undo last transaction.
- `audit`: scan skills/MCP/security/docs drift.
- `openspec`: manage governed changes.

### Acceptance criteria

- Every command supports machine-readable output where useful.
- Dangerous commands have preview and confirmation paths.
- Missing prerequisites are surfaced with guided remediation.

## 8. Documentation and AI instruction generation

### Change

Treat README, docs, AI instructions, support matrices, and setup guides as first-class artifacts.

### Acceptance criteria

- README quickstart commands are canonicalized.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Copilot instructions, Cursor rules, OpenCode instructions, and harness setup docs are checked for consistency.
- Docs CI fails when generated matrices drift from manifests.

## 9. OpenSpec governance

### Change

Use OpenSpec to govern major behavior changes.

### Acceptance criteria

- Existing OpenSpec artifacts are inventoried and preserved.
- Active overhaul change includes proposal/design/tasks/spec deltas.
- P0/P1 tasks map to OpenSpec tasks.
- Archive flow exists after implementation.
