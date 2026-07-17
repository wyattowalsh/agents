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
CLI selectors into installable curated-external catalog authoring rows.
Source-level catalog integration is reconciled separately: existing stable rows
own 127 targets, and 162 stable non-candidate reference rows own the remaining
targets. Credentialed MCP/plugin/tool services remain disabled by default.

After explicit maintainer authorization, a separate runtime overlay may install
audited, pinned distributions. That overlay is not intake: it records package
manager provenance, safe version/help probes, executable paths normalized to
`~`, MCP registration, plugin activation state, optional auth variable names,
and one terminal runtime disposition per normalized target. It never treats a
skill-only, collection, library, quarantine, or policy-conflict row as a missing
binary.

## Stable Public Identity Reconciliation

The final 289-target partition is exhaustive and mutually exclusive:

| Classification | Count | Public ownership |
| --- | ---: | --- |
| Existing installable owner | 121 | Existing stable curated catalog row |
| Existing inspection-required owner | 6 | Existing stable row with install metadata, excluded from sync until trust review |
| Generated stable reference | 158 | New source-derived, non-candidate reference id |
| Generated stable hard-quarantine reference | 4 | New source-derived id bound to the central quarantine register |

The last two classes produce exactly 162 stable reference rows. Stable ids are
derived from source identity rather than raw corpus sequence numbers. All
`candidate-corpus-*` authoring rows and generated detail pages are removed only
after the 289-target ownership assertion passes. Raw indexes, normalized URLs,
dedupe groups, and historical candidate ids remain in planning manifests for
traceability, not as public catalog identities.

Installable selector rows remain an orthogonal overlay. A target may have both a
stable source-level reference and one or more reviewed installable selectors,
but the reference uses `sync_kind: none` and publishes no command.

## Data Flow

1. `raw-urls.txt` is the human-readable corpus source.
2. `normalized-urls.json` maps raw entries to normalized targets.
3. `records/*.json` stores per-raw-candidate research, audit, docs impact, and
   decision packets.
4. `docs/src/authoring/skills/*.mdx` stores stable reviewed installable rows and
   162 stable, non-candidate, non-syncing source references.
5. `wagents docs generate --no-installed` emits generated catalog pages and the
   machine-readable catalog index from the authoring rows.
6. Matrix files aggregate records by concern.
7. Promotion overlay artifacts record installed selectors and local install
   evidence.
8. `non-skill-install-assurance.json` accounts for all 289 normalized targets
   and records verified CLI, MCP, plugin, library, collection, skill-only, and
   quarantine dispositions.
9. Reports summarize decisions, docs-steward surfaces, validation, and final
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
- Intake and deep-source audit never execute candidate code. The separately
  authorized runtime overlay permits only audited installers and bounded,
  non-mutating smoke probes.
- Credentials are represented only as placeholder review flags.
- Docs/catalog generated surfaces stay source-of-truth driven.
- Terminal reference rows publish no install commands and do not participate in
  `wagents skills sync`.
- Stable hard-quarantine references retain attribution only. They use
  `sync_kind: none`, publish no install command, and cannot be projected into a
  default runtime surface.
- Central quarantine validation permits those explicit docs-only hard-block
  references but fails closed on installable, executable, or default-enabled
  occurrences of the four blocked sources.
- Promotion is intentionally separated from intake and limited to reviewed
  selectors.
- Promotion packet generation must keep live install eligibility at zero until
  exact reviewed install/apply commands are recorded.
- Candidate MCP entries remain disabled and outside default groups. Plugins with
  broad lifecycle hooks remain installed-disabled; optional provider auth is
  recorded by environment-variable name only.
- Exact native activation state is authoritative in
  `config/plugin-extension-registry.json` and
  `non-skill-install-assurance.json`: lower-risk reviewed Designer and
  Prompt-to-Asset plugins may be enabled, while Axiom and HyperFrames remain
  installed-disabled because of broad lifecycle hooks.
- MCPHub 1.0.24 is launched through a repo-owned process-local HTTP bind shim
  because upstream omits a listen host. The shim permits loopback hosts only,
  is removed from child-process `NODE_OPTIONS`, and is enforced by doctor and
  hermetic tests.
- Unsafe probes that start servers or mutate projects are forbidden even when
  their executable accepts `--help`; assurance uses package inventory instead.

## Alternatives Rejected

- Directly adding every candidate as installable or promoted skills: rejected
  because many are MCP servers, plugins, tools, broad collections, duplicates,
  risky, or already covered.
- Live installs during intake: rejected because source-list evidence and
  trust-gate review must happen before install. Explicitly authorized, audited
  installs occur only in the later runtime overlay and do not imply activation.
- Storing only a human report: rejected because coverage needs machine-readable
  checks over every raw and normalized target.
- Keeping `candidate-corpus-*` as permanent public ids: rejected because intake
  sequence numbers are not durable product identities and obscure existing-row
  ownership.
- Treating every stable reference as installable: rejected because integration,
  license clearance, safety approval, and runtime enablement are distinct gates.
