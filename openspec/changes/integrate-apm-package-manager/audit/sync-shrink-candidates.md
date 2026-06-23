# sync-manifest Shrink Candidates for APM Integration (Wave 5 / EXT)

**Purpose**: Identify which entries in `config/sync-manifest.json` describe surfaces that *can* be owned/managed by Microsoft APM (remote package installs via `apm install` + `apm.yml` `dependencies.apm`) versus surfaces that *must stay* under wagents + `scripts/sync_agent_stack.py` control.

**Architecture (per session memory & AGENTS.md)**:
- APM = optional companion CLI facade for **search / install / update / remove / sync of remote agent packages only**.
- Repo-owned skills/agents/MCP/instructions, custom harness projections, local plugins, and MCPHub stay on `wagents`, `npx skills add`, `wagents skills sync`, and this sync script.
- **Do not** route canonical `skills/`, core bundle, or Grok/Crush/MCPHub/OpenCode custom logic through `apm install`.
- APM supports: Copilot, Claude, Cursor, OpenCode, Codex, Gemini, Windsurf, Kiro. **Not first-class for Grok or Crush**.
- MCP via APM (`dependencies.mcp` + `apm-servers/`) is separate from repo `config/mcp-registry.json` + MCPHub.

**Basis**: Full inventory from `config/sync-manifest.json` (89 entries). Modes: canonical (SSOT), generated, merged, symlink, symlinked-entries.

## Must Stay wagents / sync-manifest Controlled (Core + Special Harnesses)

These cannot move without breaking local custom behavior, OSS bundle model, Grok/Crush support, MCPHub, or repo source-of-truth guarantees.

### Core Canonical Registries & Policies (always)
- `000: ${REPO_ROOT}/config/mcp-registry.json | canonical`
- `001: ${REPO_ROOT}/config/hook-registry.json | canonical`
- `003: ${REPO_ROOT}/config/tooling-policy.json | canonical`
- `004: ${REPO_ROOT}/config/support-tier-registry.json | canonical`
- `005: ${REPO_ROOT}/config/harness-surface-registry.json | canonical`
- `006: ${REPO_ROOT}/config/config-transaction-registry.json | canonical`
- `007: ${REPO_ROOT}/config/docs-artifact-registry.json | canonical`
- `008: ${REPO_ROOT}/config/skill-registry-policy.json | canonical`
- `011: ${REPO_ROOT}/config/plugin-extension-registry.json | canonical`
- `012: ${REPO_ROOT}/config/schemas | canonical`
- `013-015: planning/manifests/* | canonical`
- `025: ${REPO_ROOT}/config/sync-manifest.json | canonical` (self)

### Local Skills, Authoring, Instructions, Hooks (bundle SSOT)
- `009: ${REPO_ROOT}/docs/src/authoring/skills | canonical`
- `045: ${REPO_ROOT}/hooks | canonical`
- `026,048-050: instructions/* (copilot-global, codex-global, global, opencode-global) | canonical + symlink + generated`
- `042-044: .github/{copilot-instructions.md,instructions,hooks} | generated` (projections of repo instructions)

### Grok-specific (no first-class APM target)
- `031: ${REPO_ROOT}/.grok/config.toml | generated`
- `056: ~/.grok/config.toml | merged`
- `086-088: ${REPO_ROOT}/config/grok-config.toml , instructions/grok-global.md , config/grok-env.sh | canonical`
- Related skills handling: Grok reads via claude adapter + explicit `~/.grok/skills` mirroring in sync (see `sync_agent_stack.py` grok paths + wagents/platforms/grok.py).

### Crush (custom MCP merge, no APM first-class)
- `080: ~/.config/crush/crush.json | merged`
  - Uses `merge_server_root_config` for MCP (via render that prefers MCPHub when enabled).

### MCPHub / Custom MCP Projection Surfaces
- All mcp.json generations/projections (`032-034,052,061,064-067,079,...`) when `mcphub_enabled(registry)`:
  - Use custom `MCPHUB_PROJECTION_MODES`, `remote-stdio.sh`, bearer env, http vs stdio logic inside sync script.
- `000` mcp-registry stays canonical source (APM mcp deps are additive/optional, not replacement).
- Cherry studio managed, aitk, gemini extensions etc. that layer on custom MCP.

### OpenCode Custom Plugins, TUI, DCP, Local Runtime (repo-specific)
- `020: ${REPO_ROOT}/config/opencode-tui-plugins.json | canonical`
- `047: ${REPO_ROOT}/platforms/opencode/plugins | canonical` (local sources)
- `018-024,068-076: opencode-*.json (dcp, notifier, large-image, quota, token, ensemble, octto, opencode.json etc) | canonical + merged + generated`
- `077-078: ~/.config/opencode/plugins/{approval-notify,credential-guard}.ts | generated`
  - Deployed from `platforms/opencode/plugins` + `deploy_opencode_plugin`.
- `104: OPENCODE_PLUGIN_MANIFEST_*` and local plugin specs (OPENCODE_LOCAL_PLUGIN_SPECS, TUI_ONLY keys, disabled etc.)
- `028: instructions/opencode-global.md | generated`
- OpenCode config merges also drop unmanaged providers etc. (custom policy).

### Other Repo-Owned / Bundle Projections (stay)
- `016: planning/manifests/external-skills/chrome-devtools-mcp.json | canonical`
- `029-030,039-041,083-085: generated repo artifacts + symlinked-entries for skills (codex/copilot/gemini + .cursor/skills/repo)`
- `046,051: platforms/copilot/* | canonical + symlink`
- `010: config/external-skills.md | generated` (curated npx provenance + trust notes; APM may complement but does not replace catalog curation here)
- All `symlink` / `symlinked-entries` for repo instructions and skills (portability model).

**Rationale for "must stay"**:
- Grok/Crush lack native APM support matrix entries.
- MCPHub is repo control-plane (local URL, custom launchers) orthogonal to APM `dependencies.mcp`.
- Local OpenCode plugins (`.mjs`/`.ts` runtime plugins, TUI plugins) are not standard APM packages.
- Custom opencode config fragments (DCP, quota, ensemble, notifier...) and provider/model policy are repo-owned.
- Canonical sources + generated projections from them enforce the bundle's multi-harness + OSS portability invariants.
- sync tests, drift ledger, harness-fixture-support, validate collectors all key off manifest entries.

## Candidates for APM-Owned / Future Shrink (Remote Externals Only)

These surfaces are *not* candidates for *removal from manifest today* but *could see reduced scope or mode notes* once APM facade + catalog bridge exists for purely remote package content:

- `010: config/external-skills.md (generated)` + `016, planning/external-skills/*`
  - External install provenance today uses `npx skills add ... --skill ...`. With APM these become `apm install <source> --skill ...` (persisted as `skills:` list under dep).
  - Future: catalog-driven generation of an example `apm.yml` (or bridge) rather than (or in addition to) the md list. The generated md could remain for human + trust notes.
  - **Not a direct sync-manifest move** but related generation surface.

- Some **generated mcp projections** (if/when a catalog external contributes standard `dependencies.mcp` via APM):
  - e.g. subsets of `~/.cursor/mcp.json`, `~/.config/opencode/...`, `~/.gemini/...` etc.
  - **Caveat**: MCPHub projections and repo's own mcp-registry-managed servers MUST continue to be written by sync; APM mcp would be merged or separate. Keep manifest entries.

- Generated instruction/agent dirs (`.github/instructions`, `.cursor/agents`, `.cursor/rules`) **when populated by remote APM packages**:
  - Local repo projections (from this bundle's instructions) stay.
  - Pure remote APM installs land in `.agents/` or per-target dirs (gitignored apm_modules typically); do **not** add APM output dirs to sync-manifest.
  - Recommendation: add explicit "do-not-track" for `apm_modules/`, `.agents/` (if not already via .gitignore + policy) and avoid declaring them.

- Home skills symlinked-entries for *external curated skills* (if APM deploys skills for Grok/Crush/Cursor/Gemini targets via its install):
  - Current symlinks are primarily from *this repo's* `./skills`. External installs via npx land directly in harness user skill trees.
  - APM installs for supported targets would bypass some npx + manual sync for remotes. Grok mirroring logic stays.

- **No canonicals move**. Never move `docs/src/authoring/skills`, core configs, or `platforms/*`.

**Shrink impact estimate**: 0-4 entries might eventually have "APM-overlap" comments or conditional generation; manifest length unlikely to shrink significantly because this bundle's custom wiring is the differentiator. Primary "shrink" is scope of *external* onboarding docs + install commands, not the manifest itself.

## Recommended Next (non-breaking)
- Prefer planning note files over edits to sync-manifest.json (avoids test fragility on exact JSON + comments).
- In `wagents self doctor` (future) gate APM presence optionally and surface "use `apm install` for curated externals listed in external-skills.md".
- When adding APM catalog rows: update `docs/src/authoring/skills/*.mdx` installCommand examples to show APM equivalent (behind "or with APM").
- Do not add `apm.yml` or `apm.lock.yaml` or `.apm/` or `apm_modules/` to sync-manifest unless this repo itself begins shipping an APM package (separate decision).
- Keep MCP and Grok/Crush/OpenCode custom paths under sync.

## References
- `config/sync-manifest.json` (read 2026-06-23)
- `scripts/sync_agent_stack.py` (MCPHub logic, grok render, crush merge, opencode deploy, sync_* functions)
- `agent-bundle.json` (existing "apm" adapter stub)
- Memory: CLI facade decision; Grok/Crush not first-class; MCP separation.
- https://github.com/microsoft/apm (targets, apm.yml, --skill subsets for skill collections)

**Status**: Analysis complete for Wave 5 partial impl. No behavior changes.
