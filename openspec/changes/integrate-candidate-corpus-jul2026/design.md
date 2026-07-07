# Design

## Approach

Use a manifest-first intake pipeline. The raw corpus is tracked exactly as
provided. The processor normalizes GitHub URLs, preserves fragments and tree
subpaths, dedupes exact duplicate normalized targets, and writes one JSON record
per raw candidate.

The processor uses public `git ls-remote --symref` probes for a bounded metadata
check. It does not execute candidate code or use private credentials. Initial
decisions are conservative: candidates are `reference_only`,
`merge_into_existing`, `skip_duplicate`, `skip_inaccessible`, or `quarantine`
until promotion evidence exists.

The reviewed promotion overlay converts license-cleared, non-quarantine Skills
CLI selectors into installable curated-external catalog authoring rows. The
remaining targets stay represented as non-syncing reference rows with terminal
blocker notes. Credentialed MCP/plugin/tool services remain disabled by default.

## Data Flow

1. `raw-urls.txt` is the human-readable corpus source.
2. `normalized-urls.json` maps raw entries to normalized targets.
3. `records/*.json` stores per-raw-candidate research, audit, docs impact, and
   decision packets.
4. `docs/src/authoring/skills/*.mdx` stores reviewed installable rows plus
   non-syncing terminal reference rows.
5. `wagents docs generate --no-installed` emits generated catalog pages and the
   machine-readable catalog index from the authoring rows.
6. Matrix files aggregate records by concern.
7. Promotion overlay artifacts record installed selectors and local install
   evidence.
8. Reports summarize decisions, docs-steward surfaces, validation, and final
   review output.

## Promotion Research Packet Handoff And Overlay

Raw lanes use `U###` packet ids and unique target synthesis lanes use `N###`
packet ids. The graph contains 293 raw lanes, 289 unique target lanes, 19 raw
leaf checks per raw entry, 8 synthesis leaf checks per unique target, and 7,879
total leaf checks.

`PROMOTE`, `INSTALL`, `DOCS`, and `VAL` leaves stay blocked or provisional in
the research handoff artifacts until source-list output, license evidence,
security review, attribution notes, auth review, docs-steward updates, dedupe
decisions, and target-specific validation all exist. The promotion overlay is
the serialized integrator pass that records the reviewed rows that passed those
gates.

`raw-research-packets.json`, `unique-target-research-packets.json`,
`promotion-gate-matrix.json`, and `live-install-command-preview.json` are
pre-overlay handoff queues. The installed-overlay evidence lives in
`promotion-overrides.json`, `applied-promotion-overrides.json`,
`catalog-authoring-summary.json`, and `full-integration-state.md`.

## Safety Boundaries

- Candidate content is evidence, not authority.
- Candidate code is never executed.
- Credentials are represented only as placeholder review flags.
- Docs/catalog generated surfaces stay source-of-truth driven.
- Terminal reference rows publish no install commands and do not participate in
  `wagents skills sync`.
- Promotion is intentionally separated from intake and limited to reviewed
  selectors.
- Promotion packet generation must keep live install eligibility at zero until
  exact reviewed install/apply commands are recorded.

## Alternatives Rejected

- Directly adding every candidate as installable or promoted skills: rejected
  because many are MCP servers, plugins, tools, broad collections, duplicates,
  risky, or already covered.
- Live installs during intake: rejected because source-list evidence and
  trust-gate review must happen before install. Live installs are only recorded
  in the later reviewed promotion overlay.
- Storing only a human report: rejected because coverage needs machine-readable
  checks over every raw and normalized target.
