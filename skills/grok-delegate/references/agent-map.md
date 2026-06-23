# Repo agents → Grok `--agent`

Repo agents in `agents/*.md` sync to `~/.grok/agents/` via the repo Grok platform adapter. Invoke by frontmatter `name` (kebab-case).

| Repo agent | Grok `--agent` | Typical wave |
| --- | --- | --- |
| `researcher` | `researcher` | 0 scout |
| `planner` | `planner` | D plan |
| `code-reviewer` | `code-reviewer` | 2 verify |
| `security-auditor` | `security-auditor` | 2 verify |
| `docs-writer` | `docs-writer` | 1/2 |
| `performance-profiler` | `performance-profiler` | 0/2 |
| `release-manager` | `release-manager` | 2 release checks |

Do not delegate macro orchestration to `orchestrator` inside Grok when the parent already owns the graph.

Inline one-off subagents: `--agents '<json>'` per Grok CLI help (advanced; prefer repo agents).