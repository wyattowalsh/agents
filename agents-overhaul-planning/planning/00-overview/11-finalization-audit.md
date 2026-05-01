# Finalization Audit and Refinement Pass

Generated: `2026-05-01T10:44:04.042207+00:00`

## Scope

This pass reviewed and refined the previously generated planning corpus against:

- the current public `wyattowalsh/agents` repository shape;
- the repo's skill/MCP/instruction standards;
- Agent Skills as the preferred packaging model;
- MCP as a secondary live-systems layer;
- OpenSpec as the change-governance system;
- the full user-provided external repository universe;
- MCP indexes and curated awesome lists as discovery inputs only.

## Repo Alignment Findings

The planning corpus is now aligned around current public repo facts:

- The repo is positioned as AI agent artifacts, configs, skills, tools, and more.
- Its quickstart uses `npx -y skills add wyattowalsh/agents --all -g`.
- It supports `wagents` commands for skill creation, validation, README regeneration, packaging, install, docs generation, and OpenSpec doctor workflows.
- `AGENTS.md` defines repo-local asset standards for `skills/<name>/SKILL.md`, `agents/<name>.md`, MCP conventions, memory, progressive disclosure, supported agents, and workflow commands.
- `pyproject.toml` defines `wagents` as a Python >=3.13 CLI.
- `mcp.json` includes `npx`, `uvx`, and local absolute-path MCP definitions; local paths are portability risks requiring audit.

## Refinements Applied

1. Added a first-class external repo evaluation ledger for all user-supplied repos.
2. Added final source ledger and machine-readable evaluation manifest.
3. Expanded the task graph with external-repo intake, skill promotion, MCP replacement, UX extraction, and docs/instruction sync tasks.
4. Added a Codex master orchestration prompt optimized for OpenSpec and parallel Codex subagents.
5. Added child dispatch prompts and forbidden-file / merge-conflict controls.
6. Tightened the skills-over-MCP rule: MCP remains valid only when live/dynamic external state is required.
7. Added quarantine rules for auth-bridging, proxying, credential-sharing, and offensive-security assets.
8. Added a UX extraction lane for dashboards, kanban, terminal boards, session replay, run graphs, and skill browsers.
9. Added final OpenSpec mapping and release/readiness checks.

## Remaining Non-Negotiables Before Implementation

- Re-inventory the local working tree because unpublished/private changes may differ from public GitHub.
- Validate every external repo at a pinned commit before using code or content.
- Do not install external skills/MCPs by default.
- Promote through OpenSpec tasks, not ad hoc docs edits.
- Generate global docs from manifests/fragments after schema freeze.
