# Delta: LM Studio harness

## ADDED Requirements

### Requirement: LM Studio receives managed MCP projection

The system SHALL project managed MCP configuration into the resolved LM Studio
home `mcp.json` using Cursor-compatible `mcpServers` notation.

#### Scenario: Home path resolution

- **WHEN** `~/.lmstudio-home-pointer` names an existing directory
- **THEN** that directory SHALL be used as the LM Studio home for `mcp.json`

#### Scenario: Default MCPHub projection is remote-stdio

- **WHEN** MCPHub is enabled and `lm-studio` is synced
- **THEN** managed servers SHALL use `scripts/mcphub/remote-stdio.sh` stdio bridge
  unless an explicit projection adapter sets `http`

#### Scenario: User-owned servers preserved

- **WHEN** home `mcp.json` already contains unmanaged server entries
- **THEN** sync SHALL preserve those entries while updating managed names

#### Scenario: Missing home is a no-op

- **WHEN** neither the pointer nor `~/.lmstudio` exists
- **THEN** sync SHALL not create LM Studio directories

### Requirement: Instructions and agents via managed presets

The system SHALL project legacy-shaped managed LM Studio config presets for repo
instructions and portable agents into `{home}/config-presets/` using the
`wagents-` filename prefix, preserving user presets without that prefix. Live
compatibility with the current LM Studio schema/UI remains unverified and SHALL
remain a blocker to promotion beyond `repo-present-validation-required`.

#### Scenario: Instruction preset written

- **WHEN** home sync runs and LM Studio home exists
- **THEN** `wagents-repo.preset.json` SHALL be written with a legacy-shaped
  system/`pre_prompt` body for fixture validation
- **AND** fixture validation SHALL NOT be treated as live current-schema/UI proof

#### Scenario: Instruction preset has no absolute path

- **WHEN** the instruction preset body is rendered
- **THEN** it SHALL NOT embed absolute filesystem paths to the repo clone

#### Scenario: Agent presets written

- **WHEN** portable `agents/*.md` files exist
- **THEN** each SHALL produce a managed `wagents-agent-<name>.preset.json`

### Requirement: Optional skills mirror without Skills CLI claim

The system SHALL support optional symlinking of repo-owned skills for separately
installed compatible community plugins, with modes `none`, `allowlist`, and `all`
into `{home}/skills/`, defaulting to `none`, and SHALL NOT claim a native Skills
CLI `lm-studio` adapter or a global skill mirror.

#### Scenario: Default skill mirror is none

- **WHEN** home sync runs without `WAGENTS_LM_STUDIO_SKILLS` (or with `none`)
- **THEN** sync SHALL NOT create skill symlinks for the full repo skills tree

#### Scenario: Mode none purges prior managed skill links

- **WHEN** mode is `none` and `{home}/skills` contains managed symlinks pointing
  into the repo `skills/` tree
- **THEN** sync SHALL remove those managed skill symlinks
- **AND** SHALL NOT delete non-symlink user directories under `{home}/skills`

#### Scenario: Mode all mirrors skills

- **WHEN** `WAGENTS_LM_STUDIO_SKILLS=all` and home sync runs
- **THEN** repo-owned skills with `SKILL.md` SHALL be mirrored into `{home}/skills/`

#### Scenario: Allowlist mirrors only named skills

- **WHEN** `WAGENTS_LM_STUDIO_SKILLS` is an allowlist of skill names
- **THEN** only those skill directories SHALL be mirrored

#### Scenario: No Skills CLI adapter claim

- **WHEN** generated install inventory is produced
- **THEN** it SHALL NOT report LM Studio as a Skills CLI adapter

### Requirement: Hooks unsupported

LM Studio support SHALL NOT claim hooks projection.

#### Scenario: Hooks are omitted from LM Studio sync

- **WHEN** hook projection sync runs for all harnesses
- **THEN** LM Studio SHALL NOT receive hook configuration files
- **AND** docs SHALL describe hooks as unsupported for LM Studio
