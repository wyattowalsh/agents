# Changelog

All notable changes to email-whiz are documented here.

---

## [4.0.1] - 2026-03-15

### Fixed
- `gmail_batch_delete_emails` safety: all delete paths now require Destructive Warning template (TYPE "DELETE")
- Missing `gmail_get_or_create_label` precondition in SKILL.md triage Pass 2
- `unread_count` now saved in session cache (schema-implementation alignment)
- ORANGE bankruptcy alert level (50-100% above baseline) restored to SKILL.md summary
- Quick mode scope explicitly restricted to search and digest; evals corrected
- Security gate expanded with 6 new keywords; bare `verify` → `verify your`
- noreply@ temporal catch-all changed from 2d to 7d (login notifications have no expiry)
- JSON error handling in inbox_snapshot.py (`save_cache`, `load_cache`)
- Cache invalidation trigger list aligned across 3 files (6 tools)
- "4D+N" misnomer replaced with "5-bucket" throughout SKILL.md
- Labels mode query guidance corrected (removed false "minimal queries" claim)
- Per-entity query batching guidance added for senders/audit/newsletters modes
- `compute_trend()` zero-baseline bug: first=0 no longer produces false "stable"

### Added
- Test coverage for inbox_snapshot.py (18 tests: trend, cache, baseline)
- Session cache and bankruptcy alert level eval test cases
- "7+ snapshots" baseline establishment condition in SKILL.md

---

## [4.0.0] - 2026-03-15

### Added
- Fast-lane triage: sender/subject-only classification resolving 60-80% without content reads
- Security gate: subject-keyword scan of NOISE before archiving (catches 2FA, password resets)
- Session cache: 1h TTL local cache of Phase 0 results with write-through invalidation
- Inbox tier system: Small/Medium/Large/Massive with adaptive maxResults (100-200)
- Parallelization rules: 9 mandatory rules for tool call bundling
- Phase 0 + mode fusion: discovery AND mode queries in single message
- Mega-wave pattern: 10-15 queries in one message for analytics/audit (~65-70% reduction)
- Quick mode: `quick <mode>` prefix skips Phase 0 for search/digest
- Combo mode: `<mode> + <mode>` chains modes with shared state
- Relative bankruptcy: 30-day baseline with YELLOW/ORANGE/RED levels
- `references/efficiency-guide.md`: parallelization bible with MCP constraints, tier system, rate limits
- `scripts/inbox_snapshot.py`: cache save/load/clear subcommands, baseline computation
- 8 new canonical vocabulary terms (fast-lane, security gate, session cache, tier, quick, combo, mega-wave, baseline)
- Date-range splitting as only pagination (MCP server has no pageToken)
- Dispatch routing evals for quick mode, combo mode, tier detection, fast-lane, security gate

### Changed
- Phase 0 rewritten: parallel discovery + mode fusion, session cache check, tier assessment
- Triage rewritten: 3-pass system (fast-lane → security gate → content inspection)
- All modes updated with parallelization (tool calls bundled per efficiency-guide.md)
- maxResults capped at 100-200 (was up to 500) due to MCP N+1 fetch pattern
- Bankruptcy detection: relative to 30-day baseline (was absolute 500)
- Tier assessment uses INBOX label messagesTotal (not unreliable resultSizeEstimate)
- All reference files updated with parallelization notes and MCP constraints
- SKILL.md compressed from 415 to ~307 lines while adding new features

### Fixed
- `allowed-tools`: removed phantom `gmail_list_emails`, fixed `gmail_get_email` → `gmail_read_email`, `gmail_get_labels` → `gmail_list_email_labels`, `gmail_get_filters` → `gmail_list_filters`
- Tool name consistency: all body references now match actual MCP tool names
- Duplicate `gmail_search_emails` in read operations list

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
