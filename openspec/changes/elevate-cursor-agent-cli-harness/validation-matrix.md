# Validation matrix: elevate-cursor-agent-cli-harness

| Check | Command | Expected |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate --change elevate-cursor-agent-cli-harness --format json` | valid |
| Classify agent | `uv run python skills/harness-master/scripts/discovery/classify_intent.py --args "agent both" --json` | harnesses `["cursor-cli"]` |
| Classify editor | `uv run python skills/harness-master/scripts/discovery/classify_intent.py --args "cursor both" --json` | harnesses `["cursor"]` |
| Discover | `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness cursor --harness cursor-cli` | both keys present |
| Usage | `uv run python skills/harness-master/scripts/usage_probe.py --repo-root . --harness cursor-cli --level both --days 14 --json` | no email/transcripts |
| Skill check | `uv run python skills/harness-master/scripts/check.py` | pass |
| Validate | `uv run wagents validate` | no new registry failures |
| Classify tests | `uv run pytest tests/test_discovery_classify_intent.py -q` | pass |
| Metadata | `uv run pytest tests/test_distribution_metadata.py -q` | `cursor-cli` surfaces + Skills CLI still `cursor` |
| Doctor unit | `uv run pytest tests/test_cursor_cli_doctor.py -q` | pass; no email in output |
| Editor regression | `uv run pytest tests/test_sync_agent_stack.py tests/test_harness_plan_fixtures.py tests/test_validate_repo.py -q -k cursor` | pass |
| Doctor CLI | `uv run wagents cursor-cli doctor --format json` | redacted JSON |
| Generate | `uv run wagents web generate --no-installed` | harness-support reflects elevated `cursor-cli` |
