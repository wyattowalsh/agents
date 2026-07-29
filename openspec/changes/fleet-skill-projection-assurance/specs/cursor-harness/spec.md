# Delta: cursor-harness — authoritative skill projection ensure

## ADDED Requirements

### Requirement: Cursor global skill projection assurance

The Cursor harness SHALL treat `~/.cursor/skills` as the authoritative global
skills projection root for fleet sync completion. Skills CLI remains the mutator
for net-new canonical store installs under `~/.agents/skills`. Fleet owns
additive same-realpath projection ensure for Cursor via
`ensure_cursor_authoritative_links` on the skills-sync apply path (post Skills
CLI batches), not via stack `sync_home`.

Frozen API signature:

```python
def ensure_cursor_authoritative_links(
    *,
    names: Sequence[str],
    home: Path | None = None,
    store_root: Path | None = None,
    projection_root: Path | None = None,
    dry_run: bool = True,
) -> CursorAuthoritativeLinksReport: ...
```

Defaults: `store_root = home / ".agents" / "skills"`,
`projection_root = home / ".cursor" / "skills"`. Report fields SHALL include
`created`, `repaired`, `already_correct`, `blocked`, `skipped_missing_store`.

#### Scenario: Missing projection creates same-realpath symlink

- **GIVEN** store body `~/.agents/skills/<name>/SKILL.md` is readable
- **AND** `~/.cursor/skills/<name>` is absent
- **WHEN** `ensure_cursor_authoritative_links` runs for that name with
  `dry_run=False` after explicit apply approval
- **THEN** it SHALL create a symlink
  `~/.cursor/skills/<name> →` store realpath
- **AND** it SHALL NOT modify project `.cursor/skills/repo/**`.

#### Scenario: Broken or wrong-target symlink is repaired

- **GIVEN** store body is valid
- **AND** `~/.cursor/skills/<name>` is a broken symlink or a symlink to a
  different target
- **WHEN** ensure runs
- **THEN** it SHALL replace only the symlink
- **AND** it SHALL NOT recursively remove directory trees.

#### Scenario: Divergent real directory is blocked

- **GIVEN** `~/.cursor/skills/<name>` is a real directory whose body diverges
  from the store
- **WHEN** ensure evaluates the name
- **THEN** the result SHALL record `blocked` with a divergent-body reason
- **AND** the directory contents SHALL remain untouched.

#### Scenario: Same-body real directory is preserved

- **GIVEN** `~/.cursor/skills/<name>` is a real directory with the same body as
  the store
- **WHEN** ensure evaluates the name
- **THEN** the result SHALL record `already_correct`
- **AND** the directory SHALL NOT be replaced by a symlink.

#### Scenario: Repo project skill sync remains separate

- **GIVEN** stack repo sync runs Cursor `_sync_skill_symlinks`
- **WHEN** home projection ensure is implemented
- **THEN** `_sync_skill_symlinks` behavior for `.cursor/skills/repo` SHALL remain
  unchanged
- **AND** home ensure SHALL NOT be invoked from stack `sync_home`.

#### Scenario: Ensure defaults to dry-run safety

- **GIVEN** callers invoke `ensure_cursor_authoritative_links` without an
  explicit apply intent
- **WHEN** `dry_run` is omitted
- **THEN** it SHALL default to `True`
- **AND** SHALL NOT write home symlinks until apply wiring passes
  `dry_run=False` behind the human apply gate.
