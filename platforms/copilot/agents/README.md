# GitHub Copilot agent corpus

Repo-managed Copilot subagent definitions synced to `~/.copilot/agents/` via
`scripts/sync_agent_stack.py` (symlink from `platforms/copilot/agents/`).

## Canonical eight (portable parity)

These names align with `agents/*.md` and `.github/agents/*.agent.md`:

| Agent | File |
|-------|------|
| code-reviewer | `code-reviewer.agent.md` |
| docs-writer | `docs-writer.agent.md` |
| orchestrator | `orchestrator.agent.md` |
| performance-profiler | `performance-profiler.agent.md` |
| planner | `planner.agent.md` |
| release-manager | `release-manager.agent.md` |
| researcher | `researcher.agent.md` |
| security-auditor | `security-auditor.agent.md` |

Copilot files use the Copilot subagent dialect (`tools`, `disallowedTools`, `model`,
`maxTurns`, `memory`) with richer prompts than the portable `agents/` contracts.

## Copilot-only specialists

Additional agents tuned for Copilot workflows; not mirrored in `agents/`:

| Agent | File | Role |
|-------|------|------|
| codebase-oracle | `codebase-oracle.agent.md` | Fast "where is X?" lookups |
| dependency-checker | `dependency-checker.agent.md` | Dependency and supply-chain review |
| git-workflow | `git-workflow.agent.md` | Git operations and workflow guidance |
| spec-writer | `spec-writer.agent.md` | Spec and requirements drafting |
| test-writer | `test-writer.agent.md` | Test authoring and coverage gaps |

## Maintenance

- Edit files here; home sync mirrors via symlink.
- Renames must keep `name:` frontmatter aligned with the filename stem.
- Run `tests/test_copilot_agents.py` after corpus changes.