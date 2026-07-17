# Design: LM Studio full-surface harness

## Decisions

1. **Harness id:** `lm-studio` (kebab-case). Provider policy key stays `lmstudio`.
2. **Compatible surfaces:** MCP, instructions (presets), agents (presets), optional skills (home tree). **Not** hooks / Skills CLI native agent.
3. **Home path:** pointer file `~/.lmstudio-home-pointer` then `~/.lmstudio`.
4. **MCP projection default:** MCPHub `remote-stdio` (absolute script path; env placeholders).
5. **Instructions/agents:** managed `config-presets/wagents-*.preset.json` only (user presets preserved). Instruction bodies must not embed absolute repo paths. Payloads are legacy-shaped; live compatibility with the current LM Studio schema/UI remains unverified and blocks promotion beyond `repo-present-validation-required`.
6. **Skills:** optional symlink of repo `skills/` into `{home}/skills` for separately installed compatible community plugins. Global skills are not mirrored.
   - Modes: `none` | `allowlist` | `all`
   - **Default: `none`** (MCP + presets only)
   - Env: `WAGENTS_LM_STUDIO_SKILLS` (`none` / `all` / `allowlist:a,b` / `a,b`)
   - `mode=none` purges prior managed repo-pointing skill symlinks; never deletes non-symlink dirs
   - Path ownership checks use `Path.is_relative_to`
7. **Support tier:** `repo-present-validation-required`.

## Research lock

LM Studio MCP since 0.3.17; presets for system prompts; skills via community plugins, not first-party Skills CLI.
