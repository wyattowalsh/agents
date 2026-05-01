# Nerdbot LLM-Wiki Overhaul Pack

This pack contains the implementation plan and Codex prompt for turning `skills/nerdbot` into a CLI-first, local-first, Obsidian-compatible, LLM-wiki-inspired knowledge orchestration system.

The plan is intentionally **feature-integrative, not dependency-integrative**: Nerdbot should internalize the useful logic and workflows from the OSS LLM-wiki ecosystem, not call those tools directly. The only external document-ingestion engines explicitly allowed as first-class adapters are **Docling** and **OpenDataLoader PDF**; MarkItDown is treated as a lightweight optional fallback only if the implementation team chooses to keep it behind an ingestion adapter.

## Files

1. [`01_ULTIMATE_NERDBOT_OVERHAUL_PLAN.md`](01_ULTIMATE_NERDBOT_OVERHAUL_PLAN.md) — progressive-disclosure architecture and implementation blueprint.
2. [`02_PARALLEL_SUBAGENT_TASK_GRAPH.md`](02_PARALLEL_SUBAGENT_TASK_GRAPH.md) — subagent teams, dependency graph, milestones, acceptance gates, and test matrix.
3. [`03_CODEX_PROMPT.md`](03_CODEX_PROMPT.md) — full Codex implementation prompt.
4. [`04_SUPPORTING_DOCS_AND_EVALS_PLAN.md`](04_SUPPORTING_DOCS_AND_EVALS_PLAN.md) — documentation, skill, reference, asset, and eval updates.

## High-level recommendation

Build Nerdbot as a **native Python package plus agent-skill suite**:

- `nerdbot` Typer CLI as the primary operator interface.
- Multiple coordinated skill modules under the single Nerdbot plugin umbrella.
- Pydantic v2 schema contracts for every durable artifact.
- Docling-first ingestion, OpenDataLoader PDF fallback/specialist path.
- Native compiler, retrieval, graph, review queue, autoresearch, watch mode, and vault-lint logic.
- Optional REST/MCP wrappers only after the CLI and core service layer are stable.

## Current uploaded Nerdbot baseline

The uploaded `nerdbot.zip` currently contains:

- `SKILL.md` with a strong layered KB/vault operating contract.
- `references/` for architecture, operations, audit, migration, Obsidian vaults, and page templates.
- `assets/` with starter templates.
- `scripts/kb_bootstrap.py`, `scripts/kb_inventory.py`, and `scripts/kb_lint.py`.
- `evals/` covering create, ingest, enrich, audit, query, migrate, negative controls, and headless/no-confirmation behavior.

The overhaul should preserve that discipline while moving from “skill plus scripts” to a package-quality, schema-driven CLI/compiler system.
