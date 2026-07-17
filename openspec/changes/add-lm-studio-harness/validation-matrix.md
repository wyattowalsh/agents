# Validation matrix: add-lm-studio-harness

| Check | Command | Expected |
| --- | --- | --- |
| Unit | `uv run pytest tests/test_lm_studio_platform.py -q` | pass |
| Registry | `uv run pytest tests/test_distribution_metadata.py -q -k harness` | `lm-studio` present |
| Sync dry default | `uv run python scripts/sync_agent_stack.py --targets home --platforms lm-studio --check` | mcp/presets notes; **not** ~69 skill symlink lines |
| Sync dry all | `WAGENTS_LM_STUDIO_SKILLS=all uv run python scripts/sync_agent_stack.py --targets home --platforms lm-studio --check` | skill symlink notes when home exists |
| Discover | `uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level both --harness lm-studio` | global mcp surfaces |
| Validate | `uv run wagents validate` | no new failures from registries |
| Abs path | unit: instruction `pre_prompt` has no absolute repo path | pass |
| Skill purge | unit: prior managed links removed under mode=none | pass |
| Current schema/UI | Manual verification in the current LM Studio app | pending; required before support-tier promotion |
