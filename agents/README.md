# Agents

System prompts and context definitions for AI agents in this repository.

Portable definitions live in `agents/*.md`. Harness projections may subset or extend the corpus; OpenCode runtime overlays live in `config/opencode-agents.json` with task delegation policy in `config/agent-delegation-policy.json`.

## Harness projection matrix

| Harness | Agent count | Source | Notes |
| ------- | ----------- | ------ | ----- |
| Portable SSOT | 20 | `agents/*.md` | Canonical names and prompts |
| OpenCode | 20 | `config/opencode-agents.json` → `.opencode/agents/` | Full corpus + `permission.task` delegation |
| Cursor | 20 | `config/cursor-agents.json` → `.cursor/agents/` | Full corpus + `readonly` overlay |
| Claude Code | 8 | `.claude/agents/` | Core subset: orchestration, review, research, docs, security, release, performance |
| GitHub Copilot | 25 | `platforms/copilot/agents/` | Canonical 20 + 5 documented extensions (see generated docs index) |

Claude intentionally ships the core eight agents to limit standing subagent context. Maintainer agents (`triage-lead`, `mcp-capability-mapper`, `skill-author`, etc.) remain in portable/OpenCode/Cursor/Copilot corpora.

| Name | Description | Model | Permission Mode |
| ---- | ----------- | ----- | --------------- |
| agent-change-recorder | Record agent definition changes with validation evidence for maintainer audit trails. | inherit | plan |
| agent-eval-runner | Run structural eval gates for skills and agents; report adequacy without live LLM runs. | inherit | default |
| agent-permission-simulator | Scaffold for simulating agent permission decisions against sample tool calls (planned). | inherit | plan |
| agent-registry-publisher | Scaffold for publishing agent catalog registry artifacts (planned). | inherit | plan |
| agent-transpiler | Scaffold for transpiling portable agent frontmatter across harness projections (planned). | inherit | plan |
| bridge-consistency-checker | Verify instruction bridge and discovery parity across harness sync projections. | inherit | plan |
| code-reviewer | Review changes for correctness, risk, and maintainability without editing code. | inherit | plan |
| docs-writer | Update or create technical documentation grounded in the current codebase. | inherit | default |
| mcp-capability-mapper | Map MCP server tools to harness registry entries and maintainer docs surfaces. | inherit | plan |
| mcp-template-maintainer | Maintain FastMCP v3 MCP scaffolds in mcp/; align templates with repo conventions. | inherit | acceptEdits |
| orchestrator | Coordinate multi-step work by decomposing, delegating, and synthesizing results. | inherit | default |
| performance-profiler | Investigate performance bottlenecks and recommend the highest-leverage fixes. | inherit | default |
| permission-policy-auditor | Audit agent permissionMode, tool allowlists, and OpenCode permission overlays for least privilege. | inherit | plan |
| planner | Create a codebase-grounded implementation plan before coding. | inherit | plan |
| prompt-optimizer | Scaffold for prompt/token optimization reviews on agent and skill bodies (planned). | inherit | plan |
| release-manager | Prepare release notes, versioning, and ship-readiness checks with cautious permissions. | inherit | default |
| researcher | Investigate a technical question deeply and return a concise evidence-backed summary. | inherit | plan |
| security-auditor | Audit code and configuration for security risks without making changes. | inherit | plan |
| skill-author | Read-only advisor for skill authoring, audits, and eval planning. Does not edit skill files. | inherit | plan |
| triage-lead | Classify incoming work by severity, harness surface, and ownership; route to specialist agents. | inherit | plan |
