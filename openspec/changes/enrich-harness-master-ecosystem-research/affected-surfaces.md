# Affected Surfaces

## Source Of Truth

- `skills/harness-master/SKILL.md`
- `skills/harness-master/references/workflow.md`
- `skills/harness-master/references/output-format.md`
- `skills/harness-master/references/ecosystem-research.md`
- `skills/harness-master/references/source-profiles.md`
- `skills/harness-master/data/research-sources.json`
- `skills/harness-master/scripts/source_probe.py`
- `skills/harness-master/scripts/candidate_score.py`
- `skills/harness-master/evals/*.json`

## Generated Outputs

- None expected. Generated public docs are not part of this implementation unless validation reports drift.

## Downstream Agent Artifacts

- `harness-master` skill packaging outputs.
- Eval metadata consumed by `wagents eval validate`.

## Tests

- New eval fixtures for ecosystem research routing and safeguards.
- Existing harness surface discovery smoke remains the runtime compatibility check for canonical harness IDs.

## Validation Commands

- `uv run wagents openspec validate`
- `uv run wagents validate`
- `uv run wagents eval validate`
- `uv run python skills/skill-creator/scripts/audit.py skills/harness-master --format json`
- `uv run wagents package harness-master --dry-run`
- `uv run python skills/harness-master/scripts/source_probe.py --list-sources --json`
- `uv run python skills/harness-master/scripts/source_probe.py --list-sources --category mcp --json`
- `uv run python skills/harness-master/scripts/source_probe.py --harness opencode --source github-graphql --query "opencode plugin" --dry-run --json`
- `uv run python skills/harness-master/scripts/candidate_score.py --help`
- `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness claude-code --harness claude-desktop --harness chatgpt --harness codex --harness github-copilot-web --harness github-copilot-cli --harness cursor --harness gemini-cli --harness antigravity --harness opencode --harness perplexity-desktop --harness cherry-studio`
