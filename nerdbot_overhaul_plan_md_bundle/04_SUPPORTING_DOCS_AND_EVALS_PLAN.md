# Nerdbot Supporting Docs, Assets, and Evals Update Plan

> This document focuses on the “update every supporting doc/etc.” part of the overhaul.

## 1. Top-level skill redesign

<details open>
<summary><strong>Rewrite `SKILL.md` as router/orchestrator</strong></summary>

The current `SKILL.md` is strong but monolithic. After the overhaul, it should become a router that dispatches to internal skill modules and the Typer CLI.

Recommended sections:

1. `# Nerdbot`
2. Purpose and non-goals.
3. Dispatch table with expanded modes:
   - `init/create`
   - `ingest`
   - `compile`
   - `query`
   - `search/context`
   - `graph`
   - `research`
   - `review`
   - `audit/lint`
   - `vault normalize`
   - `migrate`
   - `watch`
   - optional `serve`
4. CLI-first rule.
5. Native implementation rule: integrate features/logics, not external LLM-wiki tools.
6. OSS-only rule.
7. Obsidian compatibility rules.
8. Safety and confirmation rules.
9. Internal skill index.
10. Reference index.
11. Examples.
12. Critical rules.

The top-level skill should no longer need to carry every operational detail inline. It should point to `skills/*/SKILL.md` and `references/*.md`.

</details>

<details>
<summary><strong>Internal skill modules</strong></summary>

Add these internal skill files under `skills/nerdbot/skills/`:

```text
skills/nerdbot/skills/ingest/SKILL.md
skills/nerdbot/skills/compile/SKILL.md
skills/nerdbot/skills/query/SKILL.md
skills/nerdbot/skills/graph/SKILL.md
skills/nerdbot/skills/research/SKILL.md
skills/nerdbot/skills/review/SKILL.md
skills/nerdbot/skills/vault/SKILL.md
skills/nerdbot/skills/audit/SKILL.md
```

Each should define:

- When to use.
- CLI commands.
- Required inputs.
- Safety gates.
- Expected artifacts.
- Exit checklist.
- Common failure modes.

</details>

## 2. Reference documents to update

<details open>
<summary><strong>Existing reference updates</strong></summary>

### `references/kb-architecture.md`

Add:

- Skill package vs managed vault vs generated state distinction.
- Expanded managed KB/vault layout.
- Pydantic schema layer.
- Machine-readable operation log.
- Review queue and patch manifests.
- Graph and retrieval layers.
- `purpose.md`, `hot.md`, `claims/`, `review/`, `graph/`.

### `references/kb-operations.md`

Add:

- CLI-first command mapping.
- Ingestion adapter workflow.
- Compile phases.
- Review queue workflow.
- Hybrid retrieval and context bundle workflow.
- Graph build/render/inspect workflow.
- Autoresearch workflow.
- Watch mode.
- Optional REST/MCP as wrappers only.

### `references/audit-checklist.md`

Add checks for:

- Extraction artifacts and source hashes.
- Citation anchors.
- Claim provenance.
- Graph schema/dangling edges/community report.
- Retrieval index freshness.
- Review queue integrity.
- Operation-log/activity-log consistency.
- Template placeholder suppression.
- Autoresearch source quality and no-paid-API policy.

### `references/obsidian-vaults.md`

Add:

- Expanded frontmatter contract.
- `hot.md` and dashboards.
- Safe `.obsidian` write policy.
- Attachment placement.
- Canvas generation from graph.
- Alias and path-stability strategy.
- Dataview/Bases optionality.

### `references/page-templates.md`

Add templates for:

- `purpose.md`
- `hot.md`
- Source summary
- Concept
- Entity
- Claim
- Synthesis
- Question
- Comparison
- Workflow
- Graph report
- Review item report
- Research report
- Coverage dashboard

### `references/migration-playbooks.md`

Add:

- Script-to-package migration.
- Legacy vault to managed vault migration.
- Search index rebuild migration.
- Schema version migration.
- Graph state migration.
- Review queue recovery.
- Rollback from failed compile.

</details>

<details>
<summary><strong>New reference documents</strong></summary>

Add:

```text
references/schema-contracts.md
references/cli.md
references/ingestion-adapters.md
references/retrieval.md
references/graph.md
references/review-queue.md
references/autoresearch.md
references/watch-mode.md
references/testing.md
references/oss-dependencies.md
references/security.md
references/interfaces-rest-mcp.md
```

Minimum content:

- `schema-contracts.md`: Pydantic models, JSON schemas, versioning, migration expectations.
- `cli.md`: command tree, options, examples, JSON output conventions.
- `ingestion-adapters.md`: Docling/OpenDataLoader/default selection matrix, fragment/citation contracts.
- `retrieval.md`: lane definitions, RRF fusion, intent classification, context bundles.
- `graph.md`: node/edge schema, extraction passes, exports, reports.
- `review-queue.md`: patch manifests, risk levels, approve/reject/apply, rollback.
- `autoresearch.md`: free/OSS source acquisition, quality scoring, source review, no paid APIs.
- `watch-mode.md`: debouncing, file locks, queueing, safe compile.
- `testing.md`: unit/golden/e2e/eval/CI matrix.
- `oss-dependencies.md`: dependency allowlist, licenses, optional extras, prohibited dependencies.
- `security.md`: path guards, symlink refusal, prompt injection handling, credentials, robots/terms, destructive writes.
- `interfaces-rest-mcp.md`: optional wrapper policy.

</details>

## 3. Asset/template updates

<details open>
<summary><strong>Template inventory</strong></summary>

Update existing templates and add new ones:

```text
assets/kb-bootstrap-template.md
assets/activity-log-template.md
assets/overview-page-template.md
assets/source-summary-template.md
assets/concept-page-template.md
assets/entity-page-template.md
assets/comparison-page-template.md
assets/purpose-page-template.md
assets/hot-cache-template.md
assets/claim-page-template.md
assets/synthesis-page-template.md
assets/question-page-template.md
assets/workflow-page-template.md
assets/graph-report-template.md
assets/research-report-template.md
assets/review-item-template.md
assets/dashboard-template.md
assets/obsidian/wiki-note-template.md
assets/obsidian/source-note-template.md
assets/obsidian/synthesis-note-template.md
```

Template syntax should avoid fake live wikilinks unless intentionally marked as placeholders. Otherwise the linter will report broken links. Use one of these patterns:

- `{{wikilink:Page Title}}` for placeholder links.
- `[[Actual Fixture Page]]` only in fixtures.
- Add `template_placeholder: true` frontmatter for templates.

</details>

## 4. Eval update plan

<details open>
<summary><strong>Preserve existing eval intent</strong></summary>

Keep and update the existing eval families:

- `empty-args-headless.json`
- `explicit-invocation.json`
- `implicit-trigger.json`
- `negative-control.json`
- `generic-notes-negative-control.json`
- `obsidian-workspace-negative-control.json`
- `no-confirmation-plan-only.json`
- `create/obsidian-create`
- `ingest`
- `enrich/improve`
- `audit`
- `query`
- `derive`
- `migrate-safety`

Map older terms into new CLI/skill behavior but do not erase the safety expectations.

</details>

<details>
<summary><strong>New evals to add</strong></summary>

Add evals for:

```text
evals/cli-init.json
evals/cli-ingest-docling.json
evals/cli-ingest-opendataloader-pdf.json
evals/compile-patch-manifest.json
evals/review-queue-contradiction.json
evals/query-read-only-grounded.json
evals/search-explain-hybrid.json
evals/graph-build-render.json
evals/autoresearch-no-paid-api.json
evals/watch-mode-safe-queue.json
evals/obsidian-template-placeholder-lint.json
evals/rest-mcp-optional-not-required.json
evals/wagents-separation.json
evals/destructive-change-requires-approval.json
evals/raw-append-only.json
evals/citation-anchor-required.json
```

Each eval should specify:

- Trigger utterance.
- Expected mode.
- Must-call or must-not-call tool behavior where applicable.
- Required safety stance.
- Expected artifacts or plan outputs.
- Negative assertions.

</details>

## 5. Test fixtures

<details open>
<summary><strong>Fixture directories</strong></summary>

Add:

```text
tests/fixtures/minimal-vault/
tests/fixtures/mixed-vault/
tests/fixtures/search-vault/
tests/fixtures/graph-vault/
tests/fixtures/review-vault/
tests/fixtures/research-vault/
tests/fixtures/sources/markdown/
tests/fixtures/sources/html/
tests/fixtures/sources/pdf/
tests/fixtures/sources/docx/
```

Use small, license-safe fixture files. Do not include large binaries unless absolutely necessary. For binary fixtures, use tiny synthetic PDFs or generated test documents.

</details>

## 6. Documentation acceptance checklist

<details open>
<summary><strong>Docs done means</strong></summary>

- Every CLI command in docs exists or is explicitly marked planned.
- Every generated file in docs has a template or schema.
- Every safety rule is reflected in CLI behavior/tests.
- Existing examples are updated from script-only commands to `nerdbot` CLI commands.
- No doc tells users to install or call external LLM-wiki tools.
- Docs clearly say Docling/OpenDataLoader are ingestion adapters only.
- Docs clearly say REST/MCP are optional wrappers, not required.
- Docs clearly separate WAgents from Nerdbot.
- Obsidian docs distinguish shared `.obsidian` config from volatile workspace state.
- Template placeholder links no longer fail production link lint.

</details>
