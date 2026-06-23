# Planning Note: APM Overlap Comments for sync-manifest.json (Preferred: Note File, No JSON Edit)

**Decision (Wave 5)**: Do **not** edit `config/sync-manifest.json` to add comments. Reason: JSON comments are non-standard (would break strict parsers, tests that `json.load`, pre-commit, or snapshot tests). Prefer standalone planning note + the shrink-candidates.md.

**If in future a safe edit is approved** (e.g. after relaxing to JSONC or adding a parallel "notes" field), these are the 5 key APM-overlapping entries + suggested mode note text (comments only, zero behavior change).

## Key 5 (selected for remote/external overlap potential)

1. `010: ${REPO_ROOT}/config/external-skills.md | generated`
   Suggested note:
   ```jsonc
   {
     "path": "${REPO_ROOT}/config/external-skills.md",
     "mode": "generated"
     // APM-OVERLAP: Human provenance for curated npx skills add (with --skill subsets).
     // Future EXT bridge may generate parallel apm.yml example or apmDep metadata.
     // This file + catalog remain; do not delete. Remote-only APM installs may reduce
     // frequency of npx rows for overlapping harnesses (Copilot/Claude/etc).
   }
   ```

2. `032: ${REPO_ROOT}/mcp.json | generated`
   Suggested note:
   ```jsonc
   {
     "path": "${REPO_ROOT}/mcp.json",
     "mode": "generated"
     // APM-OVERLAP: This bundle's MCP (via mcp-registry + MCPHub). APM dependencies.mcp
     // (standard servers) are separate; when present they would be installed by `apm install`
     // into detected harnesses. This projection + custom MCPHub logic (remote-stdio, bearer)
     // must remain under sync. Do not shrink.
   }
   ```

3. `068: ~/.config/opencode/opencode.json | merged`
   (representative of many opencode home merges: 068-076)
   Suggested note:
   ```jsonc
   {
     "path": "~/.config/opencode/opencode.json",
     "mode": "merged"
     // APM-OVERLAP: OpenCode is a supported APM target (-t opencode / compile).
     // However this merge includes *repo custom* TUI plugins, providers, DCP/ensemble/quota
     // fragments + MCP (MCPHub-aware). APM can manage remote dep primitives for opencode;
     // custom runtime plugins and policy stay wagents-controlled. See platforms/opencode/plugins.
   }
   ```

4. `080: ~/.config/crush/crush.json | merged`
   Suggested note:
   ```jsonc
   {
     "path": "~/.config/crush/crush.json",
     "mode": "merged"
     // APM-OVERLAP: Crush has no first-class entry in APM harness matrix (as of 2026-06).
     // Current merge only injects MCP servers (MCPHub or registry). Keep under sync for
     // Crush + Grok-adjacent users. No APM path for Crush config yet.
   }
   ```

5. `056: ~/.grok/config.toml | merged`  (or 031 repo .grok)
   Suggested note:
   ```jsonc
   {
     "path": "~/.grok/config.toml",
     "mode": "merged"
     // APM-OVERLAP: Grok is not a first-class APM target. Grok skills path uses claude-code
     // adapter + explicit ~/.grok/skills mirroring + repo .grok/config. All Grok surfaces
     // (config/grok-*, instructions/grok-global) stay wagents. APM remotes may be usable for
     // overlapping harnesses but Grok projection remains custom.
   }
   ```

## Additional Candidate (for completeness)
- `041: ${REPO_ROOT}/.cursor/skills/repo | symlinked-entries`
  Note would mention: Cursor is APM-supported; this symlink is for *repo local* skills (not remotes). Remote APM-installed skills would land via APM Cursor target; do not mix.

## Why Note File Only (Current)
- `json.load` in Python (sync script, tests, wagents, harness-master discover, validate collectors) would fail on `//` or `/* */` comments.
- `tests/test_distribution_metadata.py`, `tests/test_path_portability.py`, `test_sync_*` load the manifest directly.
- `scripts/validate/collectors/paths.py`, compose tools expect clean schema.
- Future-safe path: either (a) add an adjacent `sync-manifest-notes.json` sidecar, or (b) switch manifest to JSONC + update all loaders (larger change, out of scope for Wave 5 partial).

## Action
- This note + `sync-shrink-candidates.md` + `external-deps-bridge.md` satisfy Wave 5 analysis + partial impl.
- Do not apply comments to JSON in this change.
- Reference in any future OpenSpec tasks or PRs touching catalog / external / apm facade.

**Date**: 2026-06-23 (analysis session)
