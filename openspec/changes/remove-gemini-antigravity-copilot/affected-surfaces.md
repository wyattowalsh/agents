# Affected Surfaces

| Surface | Action |
| --- | --- |
| `wagents/site_model.py` | Drop three from SUPPORTED_AGENTS; extend drop_agents |
| `wagents/external_skills.py` | Remove all three target ids and reject them in authored rows |
| `scripts/sync_agent_stack.py` | Remove Gemini/Antigravity/Copilot writers; Crush-shaped MCP |
| `config/mcp-registry.json` | Strip clients; Crush→repo_mcp; preserve candidates |
| Hook registries / `hooks/wagents-hook.py` / research_hook | Drop harness maps |
| AGENTS.md / instructions / hand docs | Endorsement removal + §2.4 |
| Authoring MDX / catalog | Strip targets + remap install_command |
| Active source fixtures and test data | Remove retired managed IDs and the Gemini CLI repository URL unless explicitly classified historical evidence |
| Gemini / Antigravity / Copilot projections | Delete after writers stopped |
| Managed-home receipts | Remove only repo-owned paths for the three harnesses |
| Smoke matrix | Drop github-copilot + gemini-cli |
| OpenSpec `copilot-harness` | Retire; slim opencode-gemini-harness |
| Candidate corpus manifests | Strip target/binding rows and regenerate counts |
| `wagents/site_model.py` and generated homepage/README data | Preserve exactly six managed harnesses and five Skills CLI-native targets; report MCP-only/hybrid surfaces separately |
| `tests/test_sync_agent_stack.py` | Regress Crush-filtered Gemini-shaped `type: stdio` output for AITK |
| `tests/test_retire_harness_targets.py` | Regress bounded source/generated retirement cleanup |
| `.apm/` and `apm.lock.yaml` | Refresh only after all generation, then require `uv run wagents apm refresh-lock --check` |
