# Dirty WIP map — remove-three-harnesses (W−1.PF.1)

**Branch:** `main` (ahead of origin by 23)
**Policy:** No commits unless user asks. Preserve candidate MCP WIP; strip removed harness IDs only.

## Surgical-edit surfaces (strip harness IDs only)

| Path | Dirty? | Policy |
| --- | --- | --- |
| `config/mcp-registry.json` | Yes (+candidate servers) | Strip `gemini-cli` / `antigravity` / `github-copilot*` clients & chrome ownership rows only; keep candidate-* servers/wrappers |
| `config/plugin-extension-registry.json` | Yes | Strip removed harness extension rows; keep candidate WIP |
| `mcp/mcphub/mcp_settings.json` | Yes | Regen after registry edit; do not hand-revert candidate servers |
| `scripts/mcphub/wrappers/candidate-node` | Untracked | **KEEP** |
| `scripts/mcphub/wrappers/candidate-uv-tool` | Untracked | **KEEP** |
| `scripts/mcphub/wrappers/{gemini,antigravity,copilot}` | Present | Delete in W4 (not candidate) |

## Unrelated dirty (do not revert for this change)

- Large `docs/src/authoring/skills/*.mdx` + generated catalog/index churn (candidate corpus / catalog work)
- `planning/manifests/candidate-corpus-jul2026/**`
- `config/sync-manifest.json`, `config/tooling-policy.json` (may need harness-ID strip in-place)

## Commit policy (W−1.PF.3)

**No git commits** for this change unless the user explicitly asks.
