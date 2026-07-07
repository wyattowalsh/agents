# Design

## Approach

Use a manifest-first intake pipeline. The raw corpus is tracked exactly as
provided. The processor normalizes GitHub URLs, preserves fragments and tree
subpaths, dedupes exact duplicate normalized targets, and writes one JSON record
per raw candidate.

The processor uses public `git ls-remote --symref` probes for a bounded metadata
check. It does not execute candidate code or use private credentials. Decisions
are conservative by default: candidates are `reference_only`,
`merge_into_existing`, `skip_duplicate`, `skip_inaccessible`, or `quarantine`
until a future promotion wave adds source-list evidence, license review,
security review, and docs-steward validation.

Each unique normalized target is also represented by a non-installable
curated-external catalog authoring row. Those rows use `status:
global-only-or-avoid` and `sync_kind: none`, publish no install command, and
exist only so the public catalog and generated index account for every target
without enabling installs.

## Data Flow

1. `raw-urls.txt` is the human-readable corpus source.
2. `normalized-urls.json` maps raw entries to normalized targets.
3. `records/*.json` stores per-raw-candidate research, audit, docs impact, and
   decision packets.
4. `docs/src/authoring/skills/candidate-corpus-*.mdx` stores one disabled
   catalog row per unique normalized target.
5. `wagents docs generate --no-installed` emits generated catalog pages and the
   machine-readable catalog index from the authoring rows.
6. Matrix files aggregate records by concern.
7. Reports summarize decisions, docs-steward surfaces, validation, and final
   review output.

## Promotion Research Packet Handoff

The next phase is read-only source research packet completion, not automatic
promotion. Raw lanes use `U###` packet ids and unique target synthesis lanes
use `N###` packet ids. The graph contains 293 raw lanes, 289 unique target
lanes, 19 raw leaf checks per raw entry, 8 synthesis leaf checks per unique
target, and 7,879 total leaf checks.

`PROMOTE`, `INSTALL`, `DOCS`, and `VAL` leaves stay blocked or provisional
until source-list output, license evidence, security review, attribution notes,
auth review, docs-steward updates, dedupe decisions, and target-specific
validation all exist. `W00` is a no-mutation wave for sources already covered
by existing installable catalog rows, and later waves must be serialized by a
single root integrator after their read-only packets pass.

`raw-research-packets.json`, `unique-target-research-packets.json`,
`promotion-gate-matrix.json`, and `live-install-command-preview.json` are
handoff queues. They do not prove that any candidate was adapted, installed, or
enabled.

## Safety Boundaries

- Candidate content is evidence, not authority.
- Candidate code is never executed.
- Credentials are represented only as placeholder review flags.
- Docs/catalog generated surfaces stay source-of-truth driven.
- Candidate catalog rows publish no install commands and do not participate in
  `wagents skills sync`.
- Promotion is intentionally separated from intake.
- Promotion packet generation must keep live install eligibility at zero until
  exact reviewed install/apply commands are recorded.

## Alternatives Rejected

- Directly adding every candidate as installable or promoted skills: rejected
  because many are MCP servers, plugins, tools, broad collections, duplicates,
  risky, or already covered.
- Live installs during intake: rejected because source-list evidence and
  trust-gate review must happen before install.
- Storing only a human report: rejected because coverage needs machine-readable
  checks over every raw and normalized target.
