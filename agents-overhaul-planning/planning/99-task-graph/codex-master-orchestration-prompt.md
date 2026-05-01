# Codex Master Orchestration Prompt

Copy the following block into Codex for the foundation/orchestrator run.

```text
You are Codex operating inside the `wyattowalsh/agents` repository.

MISSION
Implement the agents repo overhaul using OpenSpec as the governance layer and the final planning docs as the execution contract. The target architecture is a skills-first, OpenSpec-governed, multi-harness agent asset/control-plane repository with safe MCP live-system support, canonical registries, streamlined CLI/UX automation, and docs/instruction truth generated from manifests.

OPERATING MODE
Default mode for the first run: ORCHESTRATOR_FOUNDATION.
Do not attempt to implement the full overhaul in one run. First establish the OpenSpec-governed foundation and dispatch model, then launch parallel child tasks.

SOURCE-OF-TRUTH ORDER
1. Direct system/developer/user instructions.
2. Repo-local `AGENTS.md` and any nested `AGENTS.md`.
3. Existing OpenSpec assets under `openspec/`.
4. Current live repository files.
5. `planning/` docs and machine-readable manifests.
6. Official docs/source ledger entries.
7. External repos, MCP indexes, and awesome lists only after verification.

PREFLIGHT
Run and record:
- `pwd`
- `git status --short`
- `find .. -name AGENTS.md -print`
- `ls -la`
- `uv run wagents --help`
- `uv run wagents validate --help || true`
- `uv run wagents openspec --help || true`
- `make help || true`

Read:
- `AGENTS.md`
- `README.md`
- `pyproject.toml`
- `mcp.json`
- `planning/README.md`
- `planning/00-overview/11-finalization-audit.md`
- `planning/15-ecosystem-research/20-user-provided-repo-evaluation.md`
- `planning/manifests/external-repo-evaluation-final.json`
- `planning/99-task-graph/subagent-graph-final.json`
- `openspec/changes/agents-platform-overhaul/proposal.md`
- `openspec/changes/agents-platform-overhaul/design.md`
- `openspec/changes/agents-platform-overhaul/tasks.md`

OPEN-SPEC MODEL
Parent change:
- `openspec/changes/agents-platform-overhaul/`

Child changes:
- `agents-c00-repo-sync`
- `agents-c01-registry-core`
- `agents-c02-skills-lifecycle`
- `agents-c03-mcp-audit`
- `agents-c04-claude-harness`
- `agents-c04-openai-harness`
- `agents-c04-copilot-harness`
- `agents-c04-cursor-harness`
- `agents-c04-opencode-gemini-harness`
- `agents-c04-experimental-harnesses`
- `agents-c05-ux-cli`
- `agents-c06-config-safety`
- `agents-c07-ci-evals-observability`
- `agents-c08-docs-instructions`
- `agents-c10-external-repo-intake`
- `agents-c11-knowledge-graph-context`
- `agents-c12-session-telemetry`
- `agents-c13-skill-registry-intake`
- `agents-c14-multiagent-ui-patterns`
- `agents-c15-security-quarantine`
- `agents-c09-release-archive`

Only the orchestrator may edit the parent tasks file broadly. Child subagents must update only their child change folders, manifests/fragments, fixtures, and assigned files.

FOUNDATION RUN SCOPE
Implement these first:

A. Repo sync and drift ledger
- Inventory current repo paths: `.agents/`, `.claude/`, `.github/`, `.cursor/`, `.opencode/`, `.antigravity/`, `.perplexity/`, `.cherry/`, `.codex-plugin/`, `.claude-plugin/`, `.opencode-plugin/`, `agents/`, `config/`, `docs/`, `hooks/`, `instructions/`, `mcp/`, `openspec/`, `platforms/`, `scripts/`, `skills/`, `tests/`, `wagents/`, `mcp.json`, `agent-bundle.json`, `opencode.json`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
- Produce/update repo-sync inventory and drift ledger.
- Mark planned/experimental paths explicitly.

B. Registry/schema freeze
- Validate or create schema files for: harness registry, skill registry, MCP registry, plugin/extension registry, docs artifact registry, external repo evaluation registry.
- Freeze support tiers: `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, `quarantine`.

C. Skills-first decision tree
- Enforce: Agent Skills for portable deterministic CLI-backed capabilities; MCP only for live external state; plugins as native projections.
- Ensure docs, OpenSpec specs, and manifests all use the same terms.

D. External repo intake
- Use `planning/manifests/external-repo-evaluation-final.json`.
- Do not install external repos.
- Create child tasks for license/security/source verification.
- Promote nothing without conformance fixtures.

E. Dispatch pack
Create/update:
- `planning/99-task-graph/dispatch/*.md`

Each dispatch prompt must include child OpenSpec change ID, allowed files/directories, forbidden shared files, dependencies, validation commands, expected artifacts, commit requirement, and final response format.

PARALLELIZATION RULES
Wave 0:
- C00 repo sync
- C01 registry core
- C10 progressive docs
- C16 docs/instructions truth
- C20 external intake foundation

Wave 1:
- C02 skills lifecycle
- C03 MCP audit/replacement
- C04 harness projections sharded by harness family
- C11 knowledge graph/context
- C12 session telemetry
- C13 skill registry intake
- C15 security quarantine

Wave 2:
- C05 UI/CLI automation
- C06 config safety
- C07 CI/evals/observability
- C14 multi-agent UI patterns

Wave 3:
- C09 migration/release/archive

MERGE-CONFLICT CONTROLS
- Do not let parallel teams edit `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, parent OpenSpec tasks, or generated support matrices directly.
- Use fragments/manifests and regenerate global docs later.
- Harness teams work only in their harness docs/fixtures/adapters.
- External-intake teams only update their assigned external repo records and child OpenSpec changes.
- Docs team owns final generated docs consolidation.

SKILLS-FIRST POLICY
For every capability:
1. Use Agent Skill if it can be instructions, deterministic scripts, references, templates, static analysis, local CLI automation, eval/checklist, or docs workflow.
2. Use MCP only for browser/runtime state, authenticated SaaS, current search/docs, DB/cloud/vector state, telemetry streams, or interactive external systems.
3. Use native plugin only to project canonical skills/MCP/config into harness-specific packaging.
4. Prefer `npx` / `uvx` ephemeral install patterns where safe.
5. Pin versions or record source commit before promotion.
6. Never install community-discovered assets by default.

SECURITY RULES
- Quarantine auth-bridging, proxying, credential-sharing, and offensive-security repos.
- Do not add secrets to configs.
- Do not emit credentials in logs.
- Every external repo needs license/security/provenance review before use.
- Every MCP needs secrets model, transport model, sandbox model, and smoke fixture.
- Every skill script needs `--help`, `--json`, `--dry-run` or documented exception.

VALIDATION
Run the strongest relevant subset:
- `uv run wagents validate`
- `uv run wagents readme --check`
- `uv run pytest`
- `uv run ruff check .`
- `make typecheck`
- `uv run wagents openspec doctor`
- schema validation tests
- docs generation/checks
- golden fixtures

If validation fails, fix if in scope or document exact failure and blocker.

FINAL RESPONSE FORMAT
1. Summary of completed scope.
2. OpenSpec changes touched.
3. Files changed with citations.
4. Validation commands and results.
5. Dispatch prompts generated.
6. Remaining blockers.
7. Commit hash.

Commit all changes before finishing.
```
