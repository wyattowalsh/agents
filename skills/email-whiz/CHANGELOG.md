# Changelog

All notable changes to email-whiz are documented here.

---

## [3.0.0] - 2026-02-26

### Added
- `inbox-zero` mode: daily/weekly routines, progress tracking, streak counter, bankruptcy detection
- `auto-rules` mode: behavioral analysis → auto-create Gmail filters from templates with confidence scoring
- `analytics` mode: volume trends, response times, sender frequency, time-of-day patterns
- `references/inbox-zero-system.md`: daily/weekly protocols, progress JSON schema, bankruptcy recovery options
- `references/analytics-guide.md`: full analytics methodology, report formats, performance notes
- `references/tool-reference.md`: all 19 Gmail MCP tool signatures, system limits, tool selection guide
- `evals/` directory with dispatch routing evals
- State management: `~/.claude/email-whiz/inbox-zero-progress.json` for streak persistence
- Canonical vocabulary section to SKILL.md
- `argument-hint`, `model`, `license`, and `metadata` frontmatter fields

### Changed
- Migrated from `~/.claude/skills/email-whiz/` (installed) to `skills/email-whiz/` (project repo)
- Expanded `allowed-tools` from 10 to 19 Gmail tools plus `Read`, `Grep`, `Write`
- Added `gmail_batch_modify_emails`, `gmail_batch_delete_emails`, `gmail_create_filter_from_template`, `gmail_get_or_create_label`, `gmail_update_label`, `gmail_delete_label`, `gmail_delete_filter`, `gmail_get_filter`
- Enhanced `references/triage-framework.md`: 5D+N clarification, inbox-zero integration, `gmail_batch_modify_emails` wave protocol
- Enhanced `references/filter-patterns.md`: auto-rule algorithms, `create_filter_from_template` patterns, learning loop protocol
- Enhanced `references/workflows.md`: batch operations guide, label hierarchy best practices, expanded analytics queries
- Enhanced `references/templates.md`: inbox-zero progress, analytics report, auto-rules report, batch operation confirmation templates
- SKILL.md restructured with dispatch classification gate, hybrid mode protocol expanded for batch ops

### Fixed
- Scope boundary: removed `gmail_draft_email` from allowed-tools (contradicted "NOT for composing emails")
- Removed `gmail_download_attachment` from allowed-tools (attachment metadata available via `gmail_read_email`)
- `allowed-tools` uses inline space-delimited format per frontmatter-spec golden example

---

## [2.0.0] - 2025-01-28

### Changed (Breaking)
- Restructured reference files to `references/` subdirectory
- Fixed frontmatter: added `disable-model-invocation`, removed invalid `auto_invoke`
- Rewrote description with trigger keywords and NOT-for exclusions
- Added `allowed-tools` restriction and `context: fork`
- Trimmed SKILL.md from 414 to 300 lines for token efficiency
- Added anti-patterns, error handling, and "When to Use" sections

### Added
- CHANGELOG.md
- `scripts/validate-skill.sh`

---

## [1.0.0] - 2025-01-28

### Added
- Initial release with 9 dispatch modes: triage, filters, newsletters, labels, search, senders, digest, cleanup, audit
- Hybrid read/write confirmation protocol
- 4 reference files: triage-framework, filter-patterns, workflows, templates
