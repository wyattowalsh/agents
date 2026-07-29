# Validation Matrix

| ID | Check | Gate |
| --- | --- | --- |
| V1 / RV-005 | `SUPPORTED_TARGET_AGENTS` and active target schemas reject all three | G2/G8 |
| V2 | Crush MCP render `type: stdio` + managed names | G2.SMK / W8.C.1 |
| V3 | Cherry/LM/Claude-desktop/ChatGPT still project | W8.C.2 |
| V4 | `wagents validate` | W8.V.1 |
| V5 | `hooks validate --harness all` | W8.V.2 |
| V6 | hook-discovery parity + bridge consistency | W8.V.3 |
| V7 | focused + full pytest | W8.V.4 |
| V8 | ruff + ty | W8.V.5 |
| V9 | Semantic final rg; unrelated Gemini API/GitHub content, candidate wrappers, and workflows intact | W8.V.6 |
| V10 | Managed-home removal receipt proves only repo-owned paths changed | W8.V.7 |
| V11 | No commits unless requested | All |
| V12 | Taxonomy assertions over site/docs source and generated homepage/README data | Exactly six managed harnesses (`claude-code`, `codex`, `crush`, `cursor`, `grok`, `opencode`), exactly five Skills CLI-native targets (managed set minus `grok`), and separately labeled MCP-only/hybrid surfaces |
| V13 / RV-007 | `uv run pytest -q tests/test_sync_agent_stack.py -k 'crush or aitk'` | Emitted AITK MCP entries are Crush-filtered flat entries with `type: stdio`; no client renderer regression |
| V14 / RV-005 / RV-013 | `uv run pytest -q tests/test_retire_harness_targets.py` plus the bounded source/generated semantic scan | Active surfaces reject the three retired managed IDs and `https://github.com/google/gemini-cli`; explicit historical/change-control allowlist and unrelated keep-set remain |
| V15 / RV-008 | `uv run wagents apm refresh-lock --check` after all generation | `apm.lock.yaml` and deployed-file hashes are converged; this is the final gate, not an implementation task |
| V16 / RV-006 | `npx -y @fission-ai/openspec@latest validate remove-gemini-antigravity-copilot --type change --strict --json --no-interactive` | Change is strict-valid with the base requirement removal aligned by exact heading and scenario |

## Rollback

Restore source definitions + re-run W6. Restore only receipt-backed managed
home paths; never perform a broad home-directory wipe.
