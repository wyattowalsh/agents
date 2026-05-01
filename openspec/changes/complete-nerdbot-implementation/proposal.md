# Proposal

## Problem

Nerdbot is positioned as a local-first, Obsidian-native knowledge-base toolkit, but the current implementation and public contract still contain gaps between advertised workflows and implemented behavior. Several surfaces are only helpers or planned lanes today: richer provenance, durable mutation journaling, rollback-aware operations, source ingestion adapters, stronger retrieval, graph analytics, watch/replay, and full documentation/test coverage. Without a tracked change, incremental fixes can leave public skill docs, generated docs, tests, package data, and CLI behavior inconsistent.

## Intent

Complete Nerdbot as a robust, local-first KB product with implemented public workflows, explicit safety boundaries, source-grounded retrieval and derivation, Obsidian-compatible templates, reproducible generated artifacts, and validation that prevents regressions.

## Scope

- Harden path, write, append-only, and journal primitives before expanding mutating workflows.
- Complete the `nerdbot` package CLI for all advertised mode families with consistent JSON and human-readable contracts.
- Preserve compatibility scripts while moving shared behavior into package modules.
- Add durable provenance, evidence, review, activity, operation, and replay records.
- Implement local source ingestion, enrichment, derivation, retrieval, graph, watch, replay, and audit workflows with safe defaults.
- Implement optional integrations as real extras with actionable missing-extra errors and smoke tests.
- Update tests, evals, generated docs, README/catalog surfaces, and validation matrices to match implemented behavior.

## Out Of Scope

- Network crawling or VLM processing without the corresponding optional extra installed and explicitly selected.
- Treating imported KB/raw content as trusted instructions for the coding agent.
- Mutating existing user vault content without dry-run output and an explicit apply/approval boundary.
- Committing local caches, generated indexes, virtual environments, packaged ZIP outputs, or user vault data.

## Affected Users And Tools

- Users invoking the `nerdbot` skill from supported agent harnesses.
- Maintainers validating and packaging `skills/nerdbot`.
- Obsidian users creating, repairing, querying, or migrating local Markdown vaults.
- Future automation consuming Nerdbot CLI JSON contracts, evals, generated docs, and package artifacts.

## Generated Surfaces To Refresh

- `README.md` from `uv run wagents readme` if skill description or catalog metadata changes.
- `docs/src/content/docs/skills/nerdbot.mdx` and generated site data from `uv run wagents docs generate` after public docs stabilize.
- Nerdbot generated KB artifacts only in test fixtures or temporary directories, not tracked user data.

## Risks

- The worktree already contains unrelated dirty files; implementation must avoid reverting or normalizing unrelated changes.
- Expanding CLI behavior can break compatibility scripts unless adapters remain stable.
- Path-safety changes must be portable across POSIX and Windows semantics without rejecting valid Obsidian vault paths.
- Retrieval and graph indexes must remain derived/rebuildable so generated artifacts do not become canonical KB state.
