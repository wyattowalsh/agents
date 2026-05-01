---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Glossary

| Term | Definition |
|---|---|
| Agent Skill | A directory containing `SKILL.md` plus optional scripts, references, and assets. |
| OpenSpec | Lightweight spec-driven development workflow using repo-local specs, proposals, designs, tasks, deltas, and archives. |
| MCP | Model Context Protocol; a JSON-RPC protocol for connecting agent clients to tools/data/resources. |
| Harness | An AI tool/runtime/client such as Claude Code, Codex, Cursor, OpenCode, Gemini CLI, ChatGPT, or Copilot. |
| Adapter | Code that projects canonical registry data into harness-specific files/configs. |
| Registry | Canonical metadata source for skills, plugins, MCPs, harnesses, and support tiers. |
| Conformance test | A test proving registry-rendered artifacts match harness expectations. |
| Golden fixture | Expected output for a renderer or installer under fixed input. |
| Transactional config update | Diff, backup, apply, verify, rollback sequence for harness config writes. |
| Live-state layer | MCP or plugin access to external systems whose data changes after the repo was committed. |
| Progressive disclosure | Load only minimal metadata first; load detailed context only on demand. |
| Support tier | `first_class`, `validated`, `curated_review`, `experimental`, `watchlist`, or `unsupported`. |
