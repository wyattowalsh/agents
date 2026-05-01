# Repo Sync Analysis

## Scope

This document records the planning assumptions synchronized against the latest public repository snapshot visible during this planning pass.

## Observed live repo shape

The public `wyattowalsh/agents` tree exposes top-level harness and capability directories including:

- `.agents/plugins`
- `.antigravity/rules`
- `.cherry/presets`
- `.claude-plugin`
- `.claude`
- `.codex-plugin`
- `.cursor/rules`
- `.github`
- `.opencode-plugin`
- `.opencode`
- `.perplexity/skills`
- `agents`
- `config`
- `docs`
- `hooks`
- `instructions`
- `mcp`
- `opencode-setup`
- `platforms`
- `scripts`
- `skills`
- `tests`
- `wagents`
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `agent-bundle.json`, `mcp.json`, `opencode.json`, `pyproject.toml`, `uv.lock`

## Observed CLI and build posture

The repo metadata identifies the project as `wagents`, requires Python `>=3.13`, and defines the console script `wagents = wagents.cli:app`. Runtime and dev dependencies indicate a Python CLI/tooling project with Typer, PyYAML, Loguru, Rich, FastAPI/Uvicorn, HTTPX, jsonschema, playwright, pytest, ruff, and ty.

## README drift to resolve

The rendered repository README and raw README show slightly different quickstart representations. The plan should include a canonical README-generation task that resolves:

- exact `npx skills add` repo specifier;
- `-y` usage;
- per-agent flags;
- fallback `wagents update` and `wagents skills sync` semantics;
- supported agent names and aliases.

## Repo-present does not mean validated

Several harness-specific paths are present, but this plan marks them as `repo-present-validation-required` unless there are explicit conformance tests and generated docs.

Examples:

- `.antigravity/rules` exists, but authoritative stable Antigravity extension contracts were not verified.
- `.perplexity/skills` exists, but Perplexity Desktop-specific skill/plugin contracts were not verified.
- `.cherry/presets` exists, and Cherry MCP/preset docs exist, but generated projection tests are still required.

## OpenSpec reconciliation

The user stated OpenSpec assets have already been added. Because the public tree visible in this pass did not expose a clearly validated top-level OpenSpec inventory, the implementation must start with:

1. inventory existing `openspec/` assets from the checked-out working tree;
2. preserve existing specs/changes;
3. reconcile this planning bundle's proposed OpenSpec change with existing content;
4. fail fast before overwriting any OpenSpec source.

## Required sync artifacts

- `planning/manifests/repo-sync-inventory.json`
- `planning/manifests/harness-registry.yaml`
- `planning/manifests/skill-inventory.json`
- `planning/manifests/mcp-inventory.json`
- `planning/manifests/docs-artifacts-manifest.yaml`
- `planning/99-task-graph/subagent-graph.json`
