@/Users/ww/dev/projects/agents/instructions/global.md

# Gemini CLI

Gemini-specific extension only. Keep shared cross-platform instructions in `global.md`.

## Context & Tool Efficiency
- Be strategic in your use of available tools to minimize unnecessary context usage.
- Prefer `grep_search` and `glob` to identify points of interest instead of reading large files individually.
- Call read/search tools in parallel whenever possible to combine conversational turns.
- Specify tight scopes via `start_line` and `end_line` for file reads, and precise `pattern` along with limited `total_max_matches` for searches.
- **Explain Before Acting:** Never call tools in silence. Provide a concise, one-sentence explanation of your intent or strategy immediately before executing tool calls.

## Safety & System Integrity
- Explain modifying commands (e.g., `run_shell_command`) briefly before executing them. 
- Never log, print, or commit secrets, API keys, or credentials. Rigorously protect environment files.
- Prefer non-interactive shell commands unless a persistent process is required.

## Task Execution
- Operate using a **Research -> Strategy -> Execution** lifecycle.
- When planning, use the `enter_plan_mode` tool for complex, multi-file changes or deep structural research.
- Maximize independent subagent dispatch (e.g., `generalist`, `codebase_investigator`) to keep the primary session context clean and agile.
- Always add/run relevant tests and project-specific validation tools after modifying code.