# Wave 1 Target Spikes: APM Integration

**Date:** 2026-06-23  
**CLI:** apm-cli==0.21.0 (via `uv run --with apm-cli==0.21.0 apm`)  
**Method:** For each target, created temp scaffold under `audit/temp-<target>/` (audit-folder only), added sample dep `microsoft/apm-sample-package` (which transitively pulls `github/awesome-copilot/skills/review-and-refactor`), ran `apm install -t <target>` (actual, for observable writes) + `apm install --dry-run -t <target>` as requested.  
**Sample package primitives:** instructions, prompts, agents, commands, skills.  
**Observed via:** install logs (integration lines), `find` of deployed paths, APM source (`apm_cli/integration/targets.py`, mcp_integrator.py, target_detection.py), and comparison to repo files.

**Note on --dry-run limitations:** `--dry-run` reports high-level "would install" and some stale removes, but does **not** enumerate the per-primitive file write targets or exact paths. Actual installs in isolated temps were used to discover mappings; dry-run outputs also captured below for fidelity to request.

**Cleanup:** temp-* dirs were created only in audit/ and removed after data extraction.

## Targets Summary

Targets tested: copilot, claude, cursor, codex, gemini, antigravity (agy), opencode.

### copilot

- Command run (per task): `apm install --dry-run -t copilot`
- Install command used for discovery: `apm install -t copilot` (in temp)
- Deploy paths written (from install log + source):
  - 2 prompts -> `.github/prompts/`
  - 1 agents -> `.github/agents/`
  - 1 instruction(s) -> `.github/instructions/`
  - 1 skill(s) -> `.agents/skills/`
  - Transitive skill -> `.agents/skills/`
- Generated / other: `apm_modules/`, `apm.lock.yaml`, append to `.gitignore` (`apm_modules/`)
- Files written in spike (example):
  ```
  .github/prompts/accessibility-audit.prompt.md
  .github/prompts/design-review.prompt.md
  .github/agents/design-reviewer.agent.md
  .github/instructions/design-standards.instructions.md
  .agents/skills/style-checker/SKILL.md
  .agents/skills/review-and-refactor/SKILL.md
  ```
- Conflicts with existing repo files:
  - Repo already has: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (many, e.g. python-quality, skill-*, docs-*, agent-*), `.github/prompts/opsx-*.prompt.md`, `.github/agents/*.agent.md`, `.github/hooks/policy.json`, `.github/skills/...`
  - APM writes under same dirs (`.github/instructions/`, `.github/prompts/`, `.github/agents/`). Name collisions possible (e.g. if package brings "design-review" etc.). Existing content is "own" (hand-authored or wagents-managed).
  - `.agents/skills/` also pre-exists heavily in repo (many skills); APM deploys here for skills (shared with cursor/opencode/codex/gemini).
  - Potential for APM to overwrite or require merge strategy.
- Skip lines / notes from run: frontmatter not relevant for copilot; no warnings in spike for this target. Dry-run mentioned "Files that would be removed (packages no longer...)" for stale.
- MCP paths (inferred + from mcp_integrator + sync-manifest):
  - Project: `mcp.json`, `.vscode/mcp.json`
  - User: `~/.copilot/mcp-config.json`, `~/.config/.copilot/mcp-config.json`
  - Also touches generated `.github/...` but MCP mainly external/user.
  - From repo sync-manifest: `~./copilot/mcp-config.json` (merged), `~/.copilot/settings.json` (merged).
- Dry-run output excerpt:
  ```
  [i] Dry run mode - showing what would be installed:
  [i] APM dependencies (1):
    - microsoft/apm-sample-package#main -> install
  [i] Files that would be removed (packages no longer in apm.yml): 2
    - .agents/skills/review-and-refactor
    ...
  ```

### claude

- Command: `apm install --dry-run -t claude`
- Deploy paths:
  - 1 agents -> `.claude/agents/`
  - 2 commands -> `.claude/commands/`
  - 1 rule(s) -> `.claude/rules/`
  - 1 skill(s) -> `.claude/skills/`
  - Transitive -> `.claude/skills/`
- Files (spike):
  ```
  .claude/agents/design-reviewer.md
  .claude/commands/accessibility-audit.md
  .claude/commands/design-review.md
  .claude/rules/design-standards.md
  .claude/skills/style-checker/SKILL.md
  .claude/skills/review-and-refactor/SKILL.md
  ```
- Conflicts:
  - Repo has rich `.claude/` : `.claude/settings.json`, `.claude/settings.local.json`, `.claude/rules/*.md` (many quality, skill-*, openspec-*), `.claude/skills/*` (docs-steward, openspec-*, ...), `.claude/commands/opsx/*`
  - Overlap in `.claude/rules/`, `.claude/skills/`, `.claude/commands/`. Existing mostly canonical/own.
  - Skills here are per-client (unlike copilot's .agents).
  - Note in run: frontmatter keys dropped for commands (`mode` not supported for claude; kept allowed-tools etc.)
- MCP paths:
  - Project: `.mcp.json` (Claude project config)
  - User: `~/.claude.json`, `~/Library/Application Support/Claude/claude_desktop_config.json` (from sync-manifest)
  - Repo sync: `~/.claude/settings.json` (merged), `~/.claude/settings.local.json` (merged)
- Dry-run: similar high-level.
- Other: `apm_modules/`, `.gitignore` update.

### cursor

- Command: `apm install --dry-run -t cursor`
- Deploy:
  - 1 agents adopted -> `.cursor/agents/`
  - 2 commands integrated -> `.cursor/commands/`
  - 1 rule(s) adopted -> `.cursor/rules/` (`.mdc` ext)
  - 1 skill(s) -> `.agents/skills/`
  - Transitive skill -> `.agents/skills/`
- Files:
  ```
  .cursor/agents/design-reviewer.md
  .cursor/commands/accessibility-audit.md
  .cursor/commands/design-review.md
  .cursor/rules/design-standards.mdc
  .agents/skills/... (shared)
  ```
- Conflicts:
  - Repo has extensive `.cursor/` : `.cursor/mcp.json`, `.cursor/cli.json`, `.cursor/hooks.json`, `.cursor/permissions.json`, `.cursor/BUGBOT.md`, `.cursor/agents/*.md` (many), `.cursor/rules/*.mdc`, `.cursor/skills/repo/*` (research, design, test-architect -- dozens of files/scripts/evals)
  - APM targets `.cursor/rules/*.mdc`, `.cursor/agents/`, `.cursor/commands/` -- direct overlap with existing generated/own content.
  - Skills go shared `.agents/skills/` (repo also populates heavily).
  - Note: "Cursor command files keep Claude-compatible frontmatter..."
- MCP: `.cursor/mcp.json` (merged), user `~/.cursor/mcp.json`
- From sync-manifest many `.cursor/*` generated.

### codex

- Deploy:
  - 1 agents -> `.codex/agents/` (`.toml`)
  - 1 skill(s) -> `.agents/skills/`
  - Transitive skill -> `.agents/skills/`
- Files:
  ```
  .codex/agents/design-reviewer.toml
  .agents/skills/...
  ```
- Conflicts:
  - Repo has `.codex-plugin/plugin.json` only at top. But sync-manifest manages `~/.codex/config.toml` (merged), `~/.codex/skills` (symlinked-entries), `~/.codex/hooks.json`
  - `.codex/` dir may be created; also `config/codex-config.toml` (generated) in repo root.
  - Low existing workspace `.codex/` content => lower conflict risk for agents dir.
- MCP: Codex uses `~/.codex/config.toml` (mcp_servers section), `~/.codex/hooks.json`
- Repo has `config/codex-config.toml`

### gemini

- Deploy:
  - 2 commands -> `.gemini/commands/` (`.toml`)
  - skills -> `.agents/skills/`
- Files:
  ```
  .gemini/commands/accessibility-audit.toml
  .gemini/commands/design-review.toml
  .agents/skills/...
  ```
- Conflicts:
  - Repo populates: `~/.gemini/settings.json` (merged), `~/.gemini/GEMINI.md` (generated), `~/.gemini/antigravity/...`, `~/.gemini/skills` (symlink entries)
  - Workspace `.gemini/` may not exist yet, but user configs and GEMINI.md referenced in sync-manifest.
  - Commands dir newish.
- MCP: `.gemini/settings.json` (merged in root scope?), antigravity mcp_config under gemini.
- Compile target for GEMINI.md

### antigravity (agy)

- Command attempts: `apm install -t agy` (and `antigravity`), init without targets key + flag.
- Result: Install "succeeded" (no error when flag used + no targets: in yml) but **no primitive integration observed**:
  - No `.agents/` dir created in workspace for this temp.
  - Only `apm_modules/` populated (cache of sources).
  - No "integrated ->" lines in output for primitives.
  - `apm compile -t agy --dry-run` fell back to "minimal" / AGENTS.md (auto-detect).
- Per source (targets.py): intended paths for explicit-only:
  - root_dir=".agents"
  - instructions -> `.agents/rules/*.md` (antigravity_rules, frontmatter stripped)
  - skills -> `.agents/skills/`
  - hooks -> `.agents/hooks.json`
  - Also mcp: `.agents/mcp_config.json`
  - User partial: `~/.gemini/antigravity-cli`
- Conflicts: Repo has `.agents/` heavily populated (skills/ many packages, AGENTS.md in subskills), `.antigravity/` dir at root, sync-manifest has `~/.gemini/antigravity/mcp_config.json` (merged), `~/.gemini/extensions/.../antigravity/...`
- Status: Antigravity appears **partially implemented / opt-in only** in 0.21.0; CLI accepts alias "agy" in some paths but integration did not materialize workspace files in spike. May require `apm compile`, experimental flags, or newer CLI. Not in `apm targets` auto list; EXPLICIT_ONLY.
- Dry-run / error when used in apm.yml `targets:`: triggers "Unknown target 'antigravity'" (because `CANONICAL_TARGETS` in apm_yml.py omits it; only in target_detection + integration).
- MCP paths: `.agents/mcp_config.json`, `~/.gemini/antigravity/mcp_config.json`

### opencode

- Deploy:
  - 1 agents -> `.opencode/agents/`
  - 2 commands -> `.opencode/commands/`
  - skills -> `.agents/skills/`
- Files:
  ```
  .opencode/agents/design-reviewer.md
  .opencode/commands/accessibility-audit.md
  .opencode/commands/design-review.md
  .agents/skills/...
  ```
- Conflicts:
  - Repo has: `.opencode/` (package.json, PLUGINS.md, ocx.jsonc, plugins/*.ts/*.mjs), `platforms/opencode/plugins/*`, `config/opencode-*.json` (many canonical), `~/.config/opencode/*` (merged/generated per sync), `opencode.json` (generated root), `.opencode-plugin/plugin.json`
  - APM would write `.opencode/agents/`, `.opencode/commands/` -- new subdirs vs existing top-level files => low direct file collision but dir usage overlap.
  - Skills shared `.agents/`
- MCP: `opencode.json` (servers under "mcp"), `~/.config/opencode/opencode.json`, `~/.config/opencode/dcp.jsonc` etc.
- Repo also has extensive opencode config surface.

## Common Observations Across Targets

- **Shared skill paths:** `.agents/skills/` used by: copilot, cursor, codex, gemini, opencode, antigravity (and agent-skills meta). Claude uses `.claude/skills/`.
- **apm_modules/ + lock + gitignore:** Always created/appended by `apm install`.
- **No MCP in sample:** Adding via `--mcp` only updated apm.yml in dry-run; actual MCP writes go to harness-specific configs (see per-target).
- **Primitive mapping varies:** Agents/prompts/instructions map differently (md vs toml, rules/ vs instructions/, commands vs workflows).
- **Frontmatter / transform:** Some dropped keys per target (claude/cursor commands); rules often strip frontmatter (antigravity).
- **Auto-create:** Some targets (copilot, antigravity via agent-skills) auto_create dirs; others require existing signal.
- **"skip lines":** Not directly observed; perhaps refers to skipped integration for unsupported primitives (e.g. no hooks for opencode in sample, unsupported_user_primitives).
- **Conflicts general:** Heavy overlap with repo's existing per-harness layouts (canonical/generated in sync-manifest). APM is "merge" candidate for many; existing wagents/sync manages many of the same files.
- **Repo root usage:** Not done (would pollute); all spikes confined to `audit/temp-*` .

## Files / Artifacts from Spikes

- `wave1-target-spikes.md` (this file)
- (temps removed)
- See also `sync-manifest-overlap.md`

## Recommendations / Next (Wave 2)

- Decide ownership: own (apm controls), merge (wagents + apm reconcile), wagents-only (ignore apm for this surface).
- Model apm.yml in repo (perhaps with `includes` or bundle pointer).
- Handle antigravity gating / CANONICAL update.
- MCP trust + policy integration.
- Audit existing files for "skip" or force-overwrite semantics via `--force`.
- Compare against `config/sync-manifest.json` (see overlap matrix).

**Raw spike temps (if retained for audit):** were under `audit/temp-*` (deleted post-capture).
