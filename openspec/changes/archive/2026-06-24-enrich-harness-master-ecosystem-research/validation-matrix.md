# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec | `uv run wagents openspec validate` | Change and repo specs validate | Confirms proposal/tasks/spec shape |
| Skill metadata | `uv run wagents validate` | Skill metadata and assets validate | Covers script portability checks |
| Evals | `uv run wagents eval validate` | Eval manifest and fixtures validate | Includes new research fixtures |
| Skill audit | `uv run python skills/skill-creator/scripts/audit.py skills/harness-master --format json` | Audit completes without high-severity blockers | Baseline score expected to improve |
| Package | `uv run wagents package harness-master --dry-run` | Package dry-run succeeds | Ensures data/scripts/references are portable |
| Source probe | `uv run python skills/harness-master/scripts/source_probe.py --list-sources --json` | Emits source registry JSON | No network or credentials required |
| Source category filter | `uv run python skills/harness-master/scripts/source_probe.py --list-sources --category mcp --json` | Emits only MCP source entries | Covers `sources [category]` dispatch |
| GraphQL dry-run | `uv run python skills/harness-master/scripts/source_probe.py --harness opencode --source github-graphql --query "opencode plugin" --dry-run --json` | Emits planned GraphQL access and `GITHUB_TOKEN` status | Missing token is degraded, not fatal |
| Candidate score | `uv run python skills/harness-master/scripts/candidate_score.py --help` | CLI help renders | Confirms parser import works |
| Surfaces | `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness claude-code --harness claude-desktop --harness chatgpt --harness codex --harness github-copilot-web --harness github-copilot-cli --harness cursor --harness gemini-cli --harness antigravity --harness opencode --harness perplexity-desktop --harness cherry-studio` | JSON output includes all canonical harnesses | Existing smoke retained |

## Blockers

- None expected. Credentialed APIs are optional enrichments and should not block validation.

## Deferred Checks

- Live source execution against credentialed APIs.
- Public docs generation, unless a validator reports generated docs drift.
