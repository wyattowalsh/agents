---
title: Activity Log
tags:
  - kb
  - activity
aliases:
  - KB activity log
kind: index
status: active
updated: 2026-06-24
source_count: 1
---

# Activity Log

### [2026-06-25] Wave 25 — catalog schema and sync transaction registry

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave25-pass4-2026-06-25.md`
- `raw`: added 2 captures (`catalog-schema-registry-capture-w25`, `sync-transaction-registry-capture-w25`).
- Metrics: **net-new raw sources: 2**; lint pass before commit.

### [2026-06-25] Wave 24 — config registry crosswalk and quarantine

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave24-pass4-2026-06-25.md`
- `raw`: added 3 captures (`config-registry-crosswalk-capture-w24`, `security-quarantine-register-capture-w24`, `harness-surface-refresh-capture-w24`).
- Metrics: **net-new raw sources: 3**; lint pass before commit.

### [2026-06-25] Wave 23 — harness fixture support and bundle snapshot

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave23-pass4-2026-06-25.md`
- `raw`: added 4 captures (`harness-fixture-support-capture-w23`, `support-tier-registry-capture-w23`, `docs-artifact-registry-capture-w23`, `agent-bundle-snapshot-capture-w23`).
- Metrics: **net-new raw sources: 4**; lint pass before commit.

### [2026-06-25] Wave 22 — antigravity and crush harness policy

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave22-pass3-2026-06-25.md`
- `raw`: added 2 captures (`antigravity-harness-policy-capture-w22`, `crush-harness-policy-capture-w22`).
- `wiki`: new [[antigravity-harness-policy]], [[crush-harness-policy]]; refreshed [[wiki/index]].
- Metrics: **net-new raw sources: 2**; lint pass before commit; waves 21–22 consecutive `<3`.

### [2026-06-25] Wave 21 — gemini, cursor, and copilot harness policy

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave21-pass3-2026-06-25.md`
- `raw`: added 3 captures (`gemini-harness-policy-capture-w21`, `cursor-harness-policy-capture-w21`, `copilot-harness-policy-capture-w21`).
- `wiki`: new [[gemini-harness-policy]], [[cursor-harness-policy]], [[copilot-harness-policy]].
- Metrics: **net-new raw sources: 3**; lint pass before commit.

### [2026-06-25] Wave 20 — hook registry and wagents typer map

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave20-pass3-2026-06-25.md`
- `raw`: added 2 captures (`hook-registry-capture-w20`, `wagents-typer-map-capture-w20`).
- Metrics: **net-new raw sources: 2**; lint pass before commit.

### [2026-06-25] Wave 19 — instructions layer and skill authoring refresh

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave19-pass3-2026-06-25.md`
- `raw`: added 4 captures (`instructions-layer-capture-w19`, `skill-creator-scripts-capture-w19`, `agent-frontmatter-refresh-capture-w19`, `instruction-overlay-matrix-capture-w19`).
- `wiki`: refreshed [[skill-authoring-and-validation]], [[agent-frontmatter-dialects]].
- Metrics: **net-new raw sources: 4**; lint pass before commit.

### [2026-05-01 14:45] Create agents repository KB

- Mode: create + ingest + enrich
- Summary: Created a new Obsidian-native Nerdbot KB under `kb/` for repository operating knowledge, with raw source notes, wiki synthesis pages, schema/config contracts, indexes, and activity logging.
- `raw`: added source notes for `AGENTS.md`, `README.md`, `pyproject.toml`/`Makefile`, bundle/sync/OpenCode config, Nerdbot contract, OpenSpec config, code surface inventory, local inventory capture, developer commands extract, and raw assets intake README.
- `wiki`: added `wiki/index.md` and topic pages for repository overview, agent asset model, skill authoring and validation, harness/platform sync, Nerdbot maintenance, OpenSpec workflow, developer commands, and known risks/open gaps.
- `indexes`: added `indexes/source-map.md`, `indexes/coverage.md`, `indexes/repo-map.md`, and `indexes/glossary.md`.
- `schema`: added `schema/page-types.md` and `schema/provenance-contract.md`.
- `config`: added `config/obsidian-vault.md`.
- `canonical material`: unchanged; all repo files outside `kb/` were treated as evidence and not edited.
- `provenance`: wiki pages include evidence tables linked to raw source notes or canonical repo paths; no external sources were used.
- `derived output`: none.
- `vault`: added Markdown-only shared template and snippet documentation under `.obsidian/`; no CSS or volatile workspace state added.
- `path map`: none; no migration, move, rename, or deletion occurred.
- `link/backlink impact`: new KB pages are linked with Obsidian double-bracket links; no existing repo links changed.
- Risks / rollback: delete `kb/` to remove this additive KB batch if needed; do not delete without explicit user approval. Dirty worktree existed before this batch.
- Follow-up:
  - Run Nerdbot inventory and lint after file creation.
  - Add deeper source notes for `wagents/` and `config/` internals if future work targets those areas.
  - Reconcile `agent-bundle.json` wording about `agents/` with actual tracked agent definitions.

### [2026-05-01 14:55] Fix Nerdbot lint findings

- Mode: enrich
- Summary: Fixed first-pass Nerdbot lint findings by replacing two literal `wikilinks` examples that the linter parsed as broken local links and adding the expected shared template filenames.
- `raw`: unchanged.
- `wiki`: unchanged.
- `indexes`: unchanged.
- `schema`: unchanged.
- `config`: updated `config/obsidian-vault.md` wording.
- `canonical material`: unchanged.
- `provenance`: unchanged; fix was navigational/template hygiene.
- `derived output`: none.
- `vault`: added `.obsidian/templates/wiki-note-template.md` and `.obsidian/templates/source-note-template.md`.
- `path map`: none.
- `link/backlink impact`: removed two accidental broken local link targets and added expected template note files.
- Risks / rollback: additive Markdown-only fix; no source repo files outside `kb/` changed.
- Follow-up:
  - Re-run Nerdbot inventory and lint.

### [2026-05-01 15:00] Verify KB structure

- Mode: audit
- Summary: Ran Nerdbot inventory and lint after the Markdown-only fix batch.
- `raw`: unchanged.
- `wiki`: unchanged.
- `indexes`: unchanged.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged.
- `provenance`: lint reported zero issues after the fix batch.
- `derived output`: none.
- `vault`: inventory detected an Obsidian-native vault with shared `.obsidian/snippets` and `.obsidian/templates` surfaces.
- `path map`: none.
- `link/backlink impact`: inventory reported 111 Obsidian links and lint reported no broken local links.
- Risks / rollback: inventory flags shared `.obsidian/` surfaces as review-worthy by design; no blocking lint issues remain.
- Follow-up:
  - Keep future KB batches additive and rerun `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` after changes.

### [2026-05-01 15:35] Enrich repo KB source coverage

- Mode: ingest + enrich
- Summary: Refreshed the KB after adding source notes and wiki pages for `wagents`, validation/tests, docs generation, MCP, OpenCode policy, canonical/generated surfaces, sync safety, harness fixtures, and external primary docs context.
- `raw`: added source notes for `wagents` internals, asset validation coverage, config registries/sync, OpenCode runtime policy, MCP surfaces, docs site architecture, Nerdbot runtime contracts, instruction hierarchy, tests/validation, agent definitions inventory, and four external-doc pointer summaries.
- `wiki`: added synthesis pages for `wagents` automation, validation/test coverage, agent frontmatter dialects, MCP safety, docs generation, OpenCode runtime policy, canonical/generated surfaces, sync transaction safety, plugin/MCP ownership, harness fixture gaps, and external primary sources; refreshed existing overview pages with links to the new synthesis.
- `indexes`: updated `source-map`, `coverage`, `repo-map`, and `glossary` to include the new raw and wiki coverage.
- `schema`: clarified external source-note authority in `page-types` and `provenance-contract`.
- `config`: clarified `source_count` meaning and external source-note rules in `obsidian-vault`.
- `canonical material`: unchanged; all repo files outside `kb/` were treated as evidence and not edited.
- `provenance`: new and refreshed wiki/index claims point to repo-local raw notes or contextual external source notes.
- `derived output`: none.
- `vault`: Markdown-only Obsidian pages updated; no volatile workspace state or non-Markdown vault assets added.
- `path map`: none; no migration, move, rename, or deletion occurred.
- `link/backlink impact`: new local links now connect the expanded topic pages from the root index, coverage index, repo map, and related-page sections.
- Risks / rollback: additive Markdown-only batch under `kb/`; rollback is to revert this batch's KB edits only, preserving unrelated dirty worktree changes.
- Follow-up:
  - Run Nerdbot inventory and lint after the enrichment edits.
  - Keep external source notes contextual unless a future task explicitly promotes an upstream rule into repo policy.

### [2026-05-01 15:45] Verify enriched KB

- Mode: audit
- Summary: Ran Nerdbot lint and inventory after the enrichment batch.
- `raw`: unchanged by verification; inventory reports 23 raw source notes and one raw extract.
- `wiki`: unchanged by verification; inventory reports 20 wiki files.
- `indexes`: unchanged by verification; lint reported no source-map, coverage, link, alias, provenance, or activity-log issues.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged.
- `provenance`: lint reported zero issues across 56 checked Markdown files.
- `derived output`: none.
- `vault`: inventory detected an Obsidian-native vault with shared `.obsidian/templates` and `.obsidian/snippets`, 290 Obsidian links, and zero Markdown links or embeds.
- `path map`: none.
- `link/backlink impact`: all checked local Obsidian links resolved.
- Risks / rollback: shared `.obsidian/` surfaces remain warning-level review paths by design; no blocking lint issues remain.
- Follow-up:
  - Keep future KB batches additive and rerun `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` after changes.

### [2026-05-01 16:05] Resume KB enrichment with subagent audit

- Mode: audit + ingest + enrich
- Summary: Used read-only subagents to identify KB consistency issues and next additive gaps, then fixed `source_count`/coverage row mismatches and added planning corpus coverage for sync inventory, drift ledgers, and harness fixture support.
- `raw`: added `raw/sources/planning-corpus-drift-source.md` as a pointer summary for planning manifests and overhaul planning docs.
- `wiki`: added [[planning-corpus-and-drift-ledgers]] and refreshed sync safety, harness fixture gaps, known risks, and root index links.
- `indexes`: updated `source-map`, `coverage`, `repo-map`, and `glossary` for the planning source and corrected source-count semantics to count distinct backing sources per page or index.
- `schema`: corrected `source_count` metadata on schema pages to match cited source notes; content contracts unchanged.
- `config`: unchanged.
- `canonical material`: unchanged; planning files outside `kb/` were read as evidence only.
- `provenance`: new claims cite repo-local planning source notes; no external docs were promoted to repo authority.
- `derived output`: none.
- `vault`: renamed the raw planning note to avoid an ambiguous Obsidian basename collision with the wiki topic page.
- `path map`: raw planning source note path is `raw/sources/planning-corpus-drift-source.md`; wiki topic path is `wiki/topics/planning-corpus-and-drift-ledgers.md`.
- `link/backlink impact`: root, source, coverage, repo, glossary, sync, fixture, and risk pages now link the planning corpus without ambiguous wiki targets.
- Risks / rollback: additive Markdown-only batch under `kb/`; rollback should remove the planning source/wiki page and revert the touched KB indexes/topic metadata only.
- Follow-up:
  - Re-run Nerdbot lint and inventory after this batch.
  - Consider a separate hooks/evals source and wiki page if more KB enrichment is requested.

### [2026-05-01 17:20] Apply autoresearch KB enrichment

- Mode: research + ingest + enrich + cleanup
- Summary: Used read-only research subagents to extend the KB with hooks/evals, OpenSpec archive status, agent publication drift, skill risk/eval coverage, and docs artifact freshness coverage.
- `raw`: added pointer summaries for hooks/evals control plane, OpenSpec change archive status, agent publication drift, skill catalog risk/eval coverage, and docs artifact freshness.
- `wiki`: added [[hooks-evals-control-plane]], [[openspec-change-archive-status]], [[agent-publication-and-drift-coverage]], and [[skill-catalog-risk-and-eval-coverage]]; enriched docs generation, OpenSpec workflow, agent dialects, skill authoring, validation coverage, wagents automation, and known risks pages.
- `indexes`: updated `source-map`, `coverage`, `repo-map`, `glossary`, and root wiki navigation for the new source and topic coverage.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged; repo files outside `kb/` were read as evidence only.
- `provenance`: new and refreshed claims cite repo-local raw pointer summaries or existing KB sources; no external source was promoted to repo authority.
- `derived output`: none.
- `vault`: cleanup removed editor metadata from the KB root; no shared template or snippet behavior changed.
- `path map`: none; no migration, move, or canonical-material rewrite occurred.
- `link/backlink impact`: root, coverage, source, repo, glossary, and related-page links now expose the new topics without introducing intentional aliases that collide with raw notes.
- Risks / rollback: additive Markdown-only batch under `kb/` plus removal of `kb/.DS_Store`; rollback should remove the five raw source notes, four wiki pages, and revert touched indexes/topic pages.
- Follow-up:
  - Run Nerdbot lint and inventory after this batch.
  - Consider actual code/docs fixes for agent publication drift, OpenSpec archive readiness, missing risk-adjusted evals, and docs freshness only as separate non-KB tasks.

### [2026-05-01 17:30] Verify autoresearch enrichment

- Mode: audit + cleanup
- Summary: Ran Nerdbot lint and inventory after the autoresearch enrichment and fixed ambiguous Obsidian link targets by renaming two raw source notes away from their wiki page basenames.
- `raw`: renamed the hooks/evals raw note to `raw/sources/hooks-evals-control-source.md` and the OpenSpec archive raw note to `raw/sources/openspec-change-archive-source.md`; source IDs stayed stable.
- `wiki`: unchanged after ambiguity fixes except evidence paths now cite the renamed raw notes.
- `indexes`: updated source-map, coverage, repo-map, glossary, and evidence references to the renamed raw note paths.
- `schema`: unchanged.
- `config`: corrected `config/obsidian-vault.md` `source_count` to match cited backing sources.
- `canonical material`: unchanged.
- `provenance`: lint reported zero issues after the ambiguity and metadata fixes.
- `derived output`: none.
- `vault`: inventory reported an Obsidian-native vault with no volatile `.DS_Store` metadata under the KB root.
- `path map`: `raw/sources/hooks-evals-control-source.md` backs [[hooks-evals-control-plane]]; `raw/sources/openspec-change-archive-source.md` backs [[openspec-change-archive-status]].
- `link/backlink impact`: ambiguous links for hooks/evals and OpenSpec archive pages were resolved by raw-note renames.
- Risks / rollback: additive Markdown-only verification/fix batch under `kb/`; rollback should preserve the raw/wiki basename separation if the pages remain.
- Follow-up:
  - Keep future raw source basenames distinct from wiki page basenames to avoid ambiguous Obsidian links.

### [2026-06-23] Maximal KB enrichment batch

- Mode: research + ingest + enrich + audit
- Summary: Completed exhaustive-tier parallel research and additive KB enrichment for catalog authoring, MCPHub, platform adapters, CI/scripts, OpenSpec lifecycle, and refreshed partial wiki pages with Phase 4 fix-candidate queue.
- `raw`: added six source notes (`skills-catalog-authoring-lifecycle-source`, `mcphub-control-plane-source`, `wagents-platform-adapters-source`, `ci-release-workflows-source`, `scripts-validation-tooling-source`, `openspec-active-lifecycle-source`); refreshed `raw/captures/local-inventory-summary.md`.
- `wiki`: added [[obsidian-vault-conventions]], [[curated-catalog-authoring]], [[mcphub-control-plane]], [[wagents-platform-adapters]], [[ci-and-release-workflows]], [[scripts-and-validation-tooling]]; deep-enriched [[docs-generation-and-site]], [[sync-transaction-safety]], [[openspec-change-archive-status]], [[agent-publication-and-drift-coverage]], [[harness-fixture-gaps]], [[skill-catalog-risk-and-eval-coverage]], [[known-risks-and-open-gaps]]; refreshed [[wiki/index]].
- `indexes`: updated `source-map`, `coverage`, `repo-map`, and `glossary` for new sources, topics, paths, and glossary terms.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged; repo files outside `kb/` were read as evidence only.
- `provenance`: wiki claims cite `kb/raw/sources/*` and `kb/raw/captures/local-inventory-summary.md`; no secrets captured.
- `derived output`: none.
- `vault`: removed `kb/.DS_Store`; Markdown-only mutations under `kb/`.
- `path map`: none.
- `link/backlink impact`: resolved missing obsidian-vault wiki target as [[obsidian-vault-conventions]]; new topics linked from root index and coverage index.
- Risks / rollback: additive `kb/` batch only; Phase 4 repo fixes documented in [[known-risks-and-open-gaps]] for separate commits.
- Follow-up:
  - Run Nerdbot lint and inventory with `--fail-on warning`.
  - Execute Phase 4 fix candidates outside `kb/` when maintainer requests repo fixes.

## 2026-06-24 — Phase 4 shipped + catalog hardening follow-up

- `raw`: unchanged.
- `wiki`: refreshed [[known-risks-and-open-gaps]] and [[agent-publication-and-drift-coverage]] to mark Phase 4 items shipped.
- `indexes`: unchanged.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: repo commits `69e2d6e` through `85a5589` shipped compose parity, Copilot agent corpus reconciliation, catalog audit CLI, docs browser, and CI docs gates.
- `provenance`: status updates cite shipped commits and existing tests; no live installs.
- `derived output`: none under `kb/`.
- `vault`: unchanged.
- `path map`: none.
- `link/backlink impact`: none.
- Risks / rollback: KB-only status refresh; repo fixes already on `main`.
- Follow-up:
  - Expand skill eval coverage for R3/R4 workflows.
  - Promote harness rollback fixtures from `planned` to executable.

## 2026-06-24 — Eval coverage, rollback fixtures, OpenSpec archive (subagent batch)

- `raw`: unchanged.
- `wiki`: refreshed [[skill-catalog-risk-and-eval-coverage]], [[harness-fixture-gaps]], [[known-risks-and-open-gaps]] for 56/56 eval manifests, rollback fixture tests, and archived OpenSpec changes.
- `canonical material`: repo commits `13d90e66` (27 eval manifests), `4415258` (rollback fixtures), `8172c4f` (OpenSpec archives), `903489f9` (prior KB archive note).
- `provenance`: counts from eval inventory + harness-fixture-support.json + openspec validate output.
- Follow-up: live E4 eval runs for highest-risk skills; promote plan-only harness fixtures.

### [2026-06-24] OpenSpec archive hygiene for completed changes

- Mode: archive + kb status sync (additive)
- Summary: Archived two completed OpenSpec changes (tasks.md all [x], shipped on main) using `wagents openspec archive` (dry-run then --apply --yes). Updated KB wiki and this log minimally.
  - `harden-skill-catalog-quality` → `openspec/changes/archive/2026-06-24-harden-skill-catalog-quality/`
  - `add-grok-delegate-skill` → `openspec/changes/archive/2026-06-24-add-grok-delegate-skill/`
- Pre-archive: `uv run wagents openspec validate` (passed, 58 items), `uv run wagents validate` (passed).
- Post-archive: `uv run wagents openspec validate` (passed, 56 items), `uv run wagents validate` (passed). Archive command updated specs as side-effect (downstream-tooling, etc.).
- `wiki`: noted archived changes in [[openspec-change-archive-status]].
- `activity`: this entry (short hygiene batch record).
- `canonical material`: archive moves performed by OpenSpec CLI (tracked in git); no manual file edits outside kb/.
- Risks / rollback: KB edits are additive only. Archive dirs are the authoritative moved artifacts.
- Follow-up: none (lint run post-edit per requirements).

### [2026-06-24] OpenSpec archive of 23 READY completed changes (bulk)
- Mode: archive + kb status sync (additive)
- Summary: Archived 23 active OpenSpec changes whose tasks.md had ZERO unchecked items (READY list verified by grep count + spot reads). All followed process: quick sanity read tasks.md (0 opens), dry-run `--format json`, then `--apply --yes` (12 used extra `--skip-specs` to bypass stale delta header matches on specs that were already current; archive move still succeeded). No hard failures. All 23 moved to dated `2026-06-24-*` dirs.
  - Full list: add-audited-external-skills, add-first-class-cursor-support, add-harness-safe-mcphub-group, add-opencode-plugins-golang-skills, add-ossinsight-supathings-mcps, avoid-default-legacy-migration-logic, complete-nerdbot-implementation, docs-copy-reduction, enhance-docs-skill-indexes, enrich-curated-catalog-pages, enrich-harness-master-ecosystem-research, expose-mcphub-chatgpt-tunnel, global-wagents-cli, improve-instruction-corpus, integrate-chrome-devtools-skills, integrate-opencode-plugins, integrate-opencode-rules-ocx-terminal-progress, make-opencode-model-picker-owned, modernize-ty-ruff-tooling, oss-friendly-codebase-standardization, overhaul-codex-hooks, stabilize-mcphub-opencode-runtime, stabilize-opencode-gpt55-tui.
- Pre-archive: confirmed 0 `- [ ]`, ran validates.
- Post-archive: `uv run wagents openspec validate` (passed, 33/33), `uv run wagents validate` (passed).
- `wiki`: batch summary + evidence row added to [[openspec-change-archive-status]].
- `activity`: this entry.
- `canonical material`: archive performed exclusively via `uv run wagents openspec archive` (no manual edits to non-kb); some spec.md updates applied as side-effect for non-skipped.
- Risks / rollback: KB edits additive only.
- Follow-up: run kb lint.

### [2026-06-24] Push batch 2 + eval adequacy + grok fixture promotion

- Mode: ship + fix (additive KB)
- Summary: Pushed 17 local commits (`d3c4063b..a6eaf259`) covering bulk OpenSpec archive, `wagents eval adequacy`, plan fixture tests (Copilot merge + Gemini MCP), and docs fixes. Post-push validation: `wagents validate`, `wagents openspec validate` (33/33), targeted pytest green.
- `canonical material`: `f9496f22` eval adequacy CLI; `7cd67b6a` plan fixtures; `a6eaf259` bulk archive; follow-up fix strips NOT-for exclusions from risk-tier inference (`agent-conventions`, `shell-scripter` no longer false R3); `grok-build` promoted to `fixture-executable` with `test_grok_platform.py` + grok rollback tests.
- `wiki`: refresh [[harness-fixture-gaps]] and [[skill-catalog-risk-and-eval-coverage]] if stale after promotion.
- Risks / rollback: KB-only delta; repo changes are additive tests + manifest rows.
- Follow-up: remaining plan-only harnesses (claude-desktop, cherry-studio); active OpenSpec waves (`compose-harness-catalog-pages`).

### [2026-06-25] Wave 18 — pass 2 stop: OpenCode harness policy topic

- Journal: `~/.grok/research/kb-wave18-pass2-stop-2026-06-25.md`
- Mode: research + ingest + enrich + audit
- Summary: New [[opencode-harness-policy]] topic; **pass 2 stop** — waves 17–18 consecutive `<3` net-new.
- `raw`: added 1 capture (`opencode-harness-policy-capture-w18`).
- `wiki`: new topic + [[wiki/index]] link; alias deduped vs [[opencode-runtime-policy]].
- Metrics: **net-new raw sources: 1**; pages enriched: 2; lint: pass (exit 0).
- **Pass 2 gap sweep complete** (waves 15–18).
- Note: waves 17–18 landed in one commit `77721170` (batched deviation).

### [2026-06-25] Wave 17 — pass 2: Nerdbot scripts and sync manifest

- Journal: `~/.grok/research/kb-wave17-pass2-2026-06-25.md`
- Mode: research + ingest + enrich + audit
- Summary: Five nerdbot KB scripts enumerated; sync-manifest 90 managed records anchor.
- `raw`: added 2 captures (`nerdbot-kb-scripts-capture-w17`, `sync-manifest-snapshot-capture-w17`).
- `wiki`: enriched [[nerdbot]], [[canonical-generated-surfaces]].
- Metrics: **net-new raw sources: 2**; pages enriched: 2; lint: pass (exit 0).

### [2026-06-25] Wave 16 — pass 2: Antigravity/Crush, agents, OpenSpec validate

- Journal: `~/.grok/research/kb-wave16-pass2-2026-06-25.md`
- Mode: research + ingest + enrich + audit
- Summary: Antigravity/Crush/Gemini bridge pointer; eight-agent inventory; OpenSpec validate exit-0 snapshot.
- `raw`: added 3 sources (`antigravity-crush-harness-capture-w16`, `agent-definitions-inventory-capture-w16`, `openspec-validate-snapshot-capture-w16`).
- `wiki`: enriched [[agent-asset-model]], [[harness-and-platform-sync]], [[openspec-workflow]].
- Metrics: **net-new raw sources: 3**; pages enriched: 3; lint: pass (exit 0).

### [2026-06-25] Wave 15 — pass 2: Grok/Codex policy topics and inventory

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave15-pass2-2026-06-25.md`
- Summary: Pass 2 restart — new [[grok-harness-policy]] and [[codex-harness-policy]] wiki topics; release-skills workflow + repo inventory captures.
- `raw`: added 4 captures (`grok-harness-policy-capture-w15`, `codex-harness-policy-capture-w15`, `release-skills-workflow-capture-w15`, `repository-inventory-capture-w15`).
- `wiki`: new topics + enriched [[repository-overview]], [[ci-and-release-workflows]], [[harness-and-platform-sync]], [[wiki/index]].
- Metrics: **net-new raw sources: 4**; pages enriched: 6; lint: pass (exit 0).
- Pass 2 stop rule: not yet (need two consecutive `<3`).

### [2026-06-25] Wave 14 — pre-commit hooks (diminishing returns stop)

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave14-gap-sweep-2026-06-25.md`
- Summary: Final gap-sweep capture — ten path-filtered pre-commit local hooks. **Stop condition met:** waves 13–14 added 2 and 1 net-new sources (two consecutive `<3` post wave 10).
- `raw`: added 1 capture (`pre-commit-hooks-capture-w14`).
- `wiki`: enriched [[ci-and-release-workflows]].
- Metrics: **net-new raw sources: 1**; pages enriched: 1; lint: pass.
- **Goal gap sweep complete** (waves 01–14; 11+ diminishing-returns exit).

### [2026-06-25] Wave 13 — Gemini harness and Makefile targets

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave13-gap-sweep-2026-06-25.md`
- Summary: Gemini CLI external pointer + Makefile install/dev target matrix.
- `raw`: added 2 sources (`gemini-harness-docs-capture-w13`, `makefile-dev-targets-capture-w13`).
- `wiki`: enriched [[harness-and-platform-sync]], [[developer-commands]], [[external-primary-source-map]].
- Metrics: **net-new raw sources: 2**; pages enriched: 3; lint: pass (exit 0).
- Stop rule: wave 12 = 3; wave 13 = 2 → consecutive `<3` with wave 14.

### [2026-06-25] Wave 12 — scripts collectors and harness policy templates

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave12-gap-sweep-2026-06-25.md`
- Summary: Explicit-path captures for validate collectors (7 modules), Grok/Codex policy templates, and Starlight astro.config plugin stack.
- `raw`: added 3 captures (`scripts-validate-collectors-capture-w12`, `harness-policy-templates-capture-w12`, `starlight-astro-config-capture-w12`).
- `wiki`: enriched [[scripts-and-validation-tooling]], [[harness-and-platform-sync]], [[docs-generation-and-site]].
- `indexes`: updated `source-map`, `coverage` (78 sources).
- Metrics: **net-new raw sources: 3**; pages enriched: 3; lint: pass (exit 0).
- Stop rule: wave 11 = 4, wave 12 = 3 → not two consecutive `<3`; sweep may continue.
- Risks / rollback: KB-only additive batch.

### [2026-06-25] Wave 11 — tooling docs and thin page refresh

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave11-gap-sweep-2026-06-25.md`
- Summary: Gap sweep deepened uv/ruff/ty tooling evidence, Obsidian properties pointers, and fresh CI job capture; refreshed repo-map evidence for waves 03–10.
- `raw`: added 4 sources (`uv-llms-index-extract-w11`, `pyproject-tooling-capture-w11`, `ci-workflow-jobs-capture-w11`, `obsidian-properties-capture-w11`).
- `wiki`: enriched [[external-primary-source-map]], [[validation-and-test-coverage]], [[ci-and-release-workflows]], [[obsidian-vault-conventions]].
- `indexes`: updated `source-map`, `coverage` (75 sources), `repo-map` evidence.
- Metrics: **net-new raw sources: 4**; pages enriched: 5; lint: pass (exit 0).
- Stop rule: waves 09–10 were 3 each; wave 11 = 4 → gap sweep continues.
- Risks / rollback: KB-only additive batch.

### [2026-06-25] Wave 10 — external harness doc pointers

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave10-harness-docs-2026-06-25.md`
- Summary: Full-capture pointers for OpenCode, Cursor, and GitHub Copilot harness docs (explicit URLs; no globs).
- `raw`: added 3 sources (`opencode-docs-capture-w10`, `cursor-docs-capture-w10`, `copilot-harness-docs-capture-w10`).
- `wiki`: enriched [[external-primary-source-map]], [[harness-and-platform-sync]].
- Metrics: **net-new raw sources: 3**; pages enriched: 2; lint: pass.

### [2026-06-25] Wave 09 — external Agent Skills and MCP spec indexes

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave09-external-specs-2026-06-25.md`
- Summary: Fetched `agentskills.io/llms.txt` and `modelcontextprotocol.io/llms.txt`; stub + extract for portable skills spec index.
- `raw`: added 2 sources + 1 extract (`agentskills-spec-capture-w09`, `mcp-spec-index-capture-w09`, `agentskills-llms-index-extract-w09`).
- `wiki`: enriched [[external-primary-source-map]], [[skill-authoring-and-validation]].
- Metrics: **net-new raw sources: 3**; pages enriched: 2; lint: pass.

### [2026-06-25] Wave 08 — platforms, instructions, harness config templates

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave08-platforms-2026-06-25.md`
- Summary: Read-only ingest of `instructions/*`, `wagents/platforms/*`, and harness config templates (`config/grok-config.toml`, `config/codex-config.toml`, `opencode.json` metadata; no secrets).
- `raw`: added 4 captures (`instructions-hierarchy-capture-w08`, `platform-adapters-fleet-capture-w08`, `harness-config-templates-capture-w08`, `opencode-platform-adapter-capture-w08`).
- `wiki`: enriched [[wagents-platform-adapters]], [[opencode-runtime-policy]], [[harness-fixture-gaps]].
- `indexes`: updated `source-map`, `coverage` (62 sources).
- Metrics: **net-new raw sources: 4**; pages enriched: 3; lint: pass (0 issues).
- Canonical material: unchanged; repo paths read as evidence only.
- Risks / rollback: KB-only additive batch; codex MCP block names only, no credential values captured.

### [2026-06-25] Wave 07 — MCPHub scripts and launch fleet

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave07-mcphub-2026-06-25.md`
- Summary: Read-only ingest of `mcp/mcphub/`, `scripts/mcphub/` (13 scripts + 11 wrappers), LaunchAgent template, and registry `mcphub` block into lifecycle, tunnel, and validation captures.
- `raw`: added 3 captures (`mcphub-scripts-lifecycle-capture-w07`, `mcphub-launch-tunnel-capture-w07`, `mcphub-settings-validation-capture-w07`).
- `wiki`: enriched [[mcphub-control-plane]] and [[mcp-configuration-and-safety]] with operational safety and launch detail.
- `indexes`: updated `source-map`, `coverage` (55 sources), `glossary`.
- Metrics: **net-new raw sources: 3**; wiki pages enriched: 2; lint: pass (exit 0, 0 issues).
- `canonical material`: unchanged; repo paths read as evidence only.
- Risks / rollback: KB-only additive batch; no `.env.mcphub` or tunnel secrets ingested.
- Follow-up:
  - Document or automate LaunchAgent plist path substitution before install.
  - Trace in-tree registry→`mcp_settings.json` generator if one exists outside manual workflow.

### [2026-06-25] Wave 06 — docs authoring and catalog index

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave06-docs-authoring-2026-06-25.md`
- Summary: Explicit-path inventory of Bucket A authoring MDX (363) and committed catalog index bundle (363 rows); no repo-wide globs.
- `raw`: added 3 captures (`catalog-authoring-mdx-capture-w06`, `skills-catalog-index-capture-w06`, `docs-generate-check-capture-w06`).
- `wiki`: enriched [[curated-catalog-authoring]], [[docs-generation-and-site]].
- `indexes`: updated `source-map`, `coverage` (65 sources).
- Metrics: **net-new raw sources: 3**; pages enriched: 2; lint: pass.
- Risks / rollback: KB-only additive batch.

### [2026-06-25] Wave 05 — hooks runtime, test clusters, eval files

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave05-hooks-tests-2026-06-25.md`
- Summary: Read-only inventory of `hooks/` (11 files, 16 `wagents-hook.py` policies), hook/eval pytest cluster (106 core / 108 extended tests), and `skills/*/evals/` layout (56/56 manifests, 602 manifest cases + 189 legacy JSON → CLI count 791).
- `raw`: added 3 captures (`hooks-runtime-inventory-capture-w05`, `hooks-tests-cluster-capture-w05`, `skill-eval-files-capture-w05`).
- `wiki`: enriched [[hooks-evals-control-plane]], [[validation-and-test-coverage]], [[skill-catalog-risk-and-eval-coverage]] with additive 2026-06-25 rows.
- `indexes`: updated `source-map`, `coverage` (58 sources; +3 net-new w05 captures).
- Metrics: **net-new raw sources: 3**; wiki pages enriched: 3; lint: pass (exit 0).
- `canonical material`: unchanged; repo paths read as evidence only.
- Risks / rollback: KB-only additive batch.
- Follow-up:
  - Consolidate or deprecate 189 legacy eval JSON files to align CLI counts with manifest-only semantics.
  - Deepen thin manifests (`skill-router`, `i18n-localization`) if risk tier warrants E3 depth.

### [2026-06-25] Wave 04 — planning manifests and OpenSpec active inventory

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave04-planning-2026-06-25.md`
- Summary: Read-only inventory of `openspec/changes/*` (8 actives, 53 archived) and `planning/manifests/*` (90-row sync/drift parity, harness fixture tiers, external-repo ledgers).
- `raw`: added 3 captures (`openspec-active-changes-capture-w04`, `planning-sync-inventory-capture-w04`, `drift-ledger-capture-w04`).
- `wiki`: enriched [[planning-corpus-and-drift-ledgers]] and [[openspec-change-archive-status]] with additive 2026-06-25 rows.
- `indexes`: updated `source-map`, `coverage` (52 sources).
- Metrics: **net-new raw sources: 3**; wiki pages enriched: 2; lint: pass (exit 0).
- `canonical material`: unchanged; repo paths read as evidence only.
- Risks / rollback: KB-only additive batch; corrected active change count from 9→8 vs Wave 01 capture.
- Follow-up:
  - Archive 4 task-complete actives after maintainer validation (`add-new-project-skill`, `consolidate-review-skill`, `enhance-skill-creator-lifecycle`, `upgrade-design-skill`).
  - Execute in-flight waves with open tasks (APM, MCPHub, catalog compose, public-release-prod-readiness).

### [2026-06-25] Wave 03 — config registry fleet

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave03-config-2026-06-25.md`
- Summary: Read-only ingest of five `config/*-registry.json` files into four captures; enriched MCPHub, harness sync, and MCP/plugin ownership wiki pages with 2026-06-25 registry counts.
- `raw`: added 4 captures (`mcp-registry-capture-w03`, `harness-surface-registry-capture-w03`, `config-transaction-registry-capture-w03`, `hook-surface-registry-capture-w03`).
- `wiki`: enriched [[mcphub-control-plane]], [[harness-and-platform-sync]], [[plugin-and-mcp-ownership]].
- `indexes`: updated `source-map`, `coverage` (45 sources).
- Metrics: **net-new raw sources: 4**; pages enriched: 3; lint: pass (0 issues).
- Risks / rollback: KB-only additive batch; no canonical config edits.

### [2026-06-25] Wave 02 — wagents automation fleet

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave02-wagents-2026-06-25.md`
- Summary: Command-backed captures for wagents CLI surface, validate delegation, docs subcommands, and eval/hooks control-plane metrics.
- `raw`: added 4 captures (`wagents-cli-surface-capture-w02`, `wagents-validate-capture-w02`, `wagents-docs-cli-capture-w02`, `wagents-eval-cli-capture-w02`).
- `wiki`: enriched [[wagents-cli-and-automation]], [[hooks-evals-control-plane]].
- `indexes`: updated `source-map`, `coverage` (49 sources).
- Metrics: **net-new raw sources: 4**; pages enriched: 2; lint: pass.
- Risks / rollback: KB-only additive batch.

### [2026-06-25] Wave 01 — partial topics refresh

- Mode: research + ingest + enrich + audit
- Journal: `~/.grok/research/kb-wave01-partials-2026-06-25.md`
- Summary: Fresh command captures for six formerly-partial wiki topics; coverage index now zero `partial` rows for those pages.
- `raw`: added 6 captures (`skill-eval-inventory-capture-w01`, `docs-freshness-capture-w01`, `sync-rollback-capture-w01`, `openspec-lifecycle-capture-w01`, `agent-pub-drift-capture-w01`, `harness-fixture-capture-w01`).
- `wiki`: max-enriched six partial topics + [[known-risks-and-open-gaps]].
- `indexes`: updated `source-map`, `coverage` (41 sources).
- Metrics: **net-new raw sources: 6**; pages enriched: 7; lint: pass (exit 0).
- Risks / rollback: KB-only additive batch.

### [2026-06-24] Cursor harness review remediation (RV-001–RV-007)

- Mode: fix + docs + kb enrich (additive)
- Summary: Closed session review findings RV-001–RV-007 after promoting Cursor surfaces: docs intro no longer contradicts validated rows; `cursor-bugbot` downgraded to `repo-present-validation-required` with `rollback: planned`; manifest `notes[]` drives executable-list copy; ACP fixture renamed `project-config-fixture`; eval adequacy narrows backtick stripping to field-doc bullets; cloud/ACP tests exercise adapter render paths.
- `canonical material`: `wagents/docs.py`, `wagents/eval_adequacy.py`, `config/harness-surface-registry.json`, `planning/manifests/harness-fixture-support.json`, targeted tests, regenerated `docs/src/content/docs/harness-support.mdx`.
- `wiki`: refreshed [[harness-fixture-gaps]] and [[skill-catalog-risk-and-eval-coverage]].
- Risks / rollback: tier downgrade is honesty-only; no runtime behavior change.
- Follow-up: add cursor-specific rollback fixtures before re-promoting `cursor-bugbot` to validated.

### [2026-06-24] Harness review remediation RV-008–RV-014

- Mode: fix + docs + kb (additive)
- Summary: Synced `hook-surface-registry.json` Cursor tiers with harness registry; added `cursor_rollback` and `grok_rollback` tests in `test_harness_rollback_fixtures.py`; G3/G4 gates for validated rollback commands and pytest `-k` collect-only; deepened ACP render compare and stable cloud hook matcher lookup; docs intro documents rollback bar; `cursor-acp` rollback set to `planned`.
- `canonical material`: hook/harness registries, harness-fixture-support manifest, rollback/plan/validation-command tests, `wagents/docs.py`, regenerated harness-support page.
- `wiki`: [[harness-fixture-gaps]] rollback model corrected (merge-preservation + drop-guard, not only `.bak`).
- Risks / rollback: honesty/tests only; no sync behavior change.

### [2026-05-01 14:45] Create agents repository KB

- Mode: create + ingest + enrich
- Summary: Created a new Obsidian-native Nerdbot KB under `kb/` for repository operating knowledge, with raw source notes, wiki synthesis pages, schema/config contracts, indexes, and activity logging.
- `raw`: added source notes for `AGENTS.md`, `README.md`, `pyproject.toml`/`Makefile`, bundle/sync/OpenCode config, Nerdbot contract, OpenSpec config, code surface inventory, local inventory capture, developer commands extract, and raw assets intake README.
- `wiki`: added `wiki/index.md` and topic pages for repository overview, agent asset model, skill authoring and validation, harness/platform sync, Nerdbot maintenance, OpenSpec workflow, developer commands, and known risks/open gaps.
- `indexes`: added `indexes/source-map.md`, `indexes/coverage.md`, `indexes/repo-map.md`, and `indexes/glossary.md`.
- `schema`: added `schema/page-types.md` and `schema/provenance-contract.md`.
- `config`: added `config/obsidian-vault.md`.
- `canonical material`: unchanged; all repo files outside `kb/` were treated as evidence and not edited.
- `provenance`: wiki pages include evidence tables linked to raw source notes or canonical repo paths; no external sources were used.
- `derived output`: none.
- `vault`: added Markdown-only shared template and snippet documentation under `.obsidian/`; no CSS or volatile workspace state added.
- `path map`: none; no migration, move, rename, or deletion occurred.
- `link/backlink impact`: new KB pages are linked with Obsidian double-bracket links; no existing repo links changed.
- Risks / rollback: delete `kb/` to remove this additive KB batch if needed; do not delete without explicit user approval. Dirty worktree existed before this batch.
- Follow-up:
  - Run Nerdbot inventory and lint after file creation.
  - Add deeper source notes for `wagents/` and `config/` internals if future work targets those areas.
  - Reconcile `agent-bundle.json` wording about `agents/` with actual tracked agent definitions.

### [2026-05-01 14:55] Fix Nerdbot lint findings

- Mode: enrich
- Summary: Fixed first-pass Nerdbot lint findings by replacing two literal `wikilinks` examples that the linter parsed as broken local links and adding the expected shared template filenames.
- `raw`: unchanged.
- `wiki`: unchanged.
- `indexes`: unchanged.
- `schema`: unchanged.
- `config`: updated `config/obsidian-vault.md` wording.
- `canonical material`: unchanged.
- `provenance`: unchanged; fix was navigational/template hygiene.
- `derived output`: none.
- `vault`: added `.obsidian/templates/wiki-note-template.md` and `.obsidian/templates/source-note-template.md`.
- `path map`: none.
- `link/backlink impact`: removed two accidental broken local link targets and added expected template note files.
- Risks / rollback: additive Markdown-only fix; no source repo files outside `kb/` changed.
- Follow-up:
  - Re-run Nerdbot inventory and lint.

### [2026-05-01 15:00] Verify KB structure

- Mode: audit
- Summary: Ran Nerdbot inventory and lint after the Markdown-only fix batch.
- `raw`: unchanged.
- `wiki`: unchanged.
- `indexes`: unchanged.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged.
- `provenance`: lint reported zero issues after the fix batch.
- `derived output`: none.
- `vault`: inventory detected an Obsidian-native vault with shared `.obsidian/snippets` and `.obsidian/templates` surfaces.
- `path map`: none.
- `link/backlink impact`: inventory reported 111 Obsidian links and lint reported no broken local links.
- Risks / rollback: inventory flags shared `.obsidian/` surfaces as review-worthy by design; no blocking lint issues remain.
- Follow-up:
  - Keep future KB batches additive and rerun `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` after changes.

### [2026-05-01 15:35] Enrich repo KB source coverage

- Mode: ingest + enrich
- Summary: Refreshed the KB after adding source notes and wiki pages for `wagents`, validation/tests, docs generation, MCP, OpenCode policy, canonical/generated surfaces, sync safety, harness fixtures, and external primary docs context.
- `raw`: added source notes for `wagents` internals, asset validation coverage, config registries/sync, OpenCode runtime policy, MCP surfaces, docs site architecture, Nerdbot runtime contracts, instruction hierarchy, tests/validation, agent definitions inventory, and four external-doc pointer summaries.
- `wiki`: added synthesis pages for `wagents` automation, validation/test coverage, agent frontmatter dialects, MCP safety, docs generation, OpenCode runtime policy, canonical/generated surfaces, sync transaction safety, plugin/MCP ownership, harness fixture gaps, and external primary sources; refreshed existing overview pages with links to the new synthesis.
- `indexes`: updated `source-map`, `coverage`, `repo-map`, and `glossary` to include the new raw and wiki coverage.
- `schema`: clarified external source-note authority in `page-types` and `provenance-contract`.
- `config`: clarified `source_count` meaning and external source-note rules in `obsidian-vault`.
- `canonical material`: unchanged; all repo files outside `kb/` were treated as evidence and not edited.
- `provenance`: new and refreshed wiki/index claims point to repo-local raw notes or contextual external source notes.
- `derived output`: none.
- `vault`: Markdown-only Obsidian pages updated; no volatile workspace state or non-Markdown vault assets added.
- `path map`: none; no migration, move, rename, or deletion occurred.
- `link/backlink impact`: new local links now connect the expanded topic pages from the root index, coverage index, repo map, and related-page sections.
- Risks / rollback: additive Markdown-only batch under `kb/`; rollback is to revert this batch's KB edits only, preserving unrelated dirty worktree changes.
- Follow-up:
  - Run Nerdbot inventory and lint after the enrichment edits.
  - Keep external source notes contextual unless a future task explicitly promotes an upstream rule into repo policy.

### [2026-05-01 15:45] Verify enriched KB

- Mode: audit
- Summary: Ran Nerdbot lint and inventory after the enrichment batch.
- `raw`: unchanged by verification; inventory reports 23 raw source notes and one raw extract.
- `wiki`: unchanged by verification; inventory reports 20 wiki files.
- `indexes`: unchanged by verification; lint reported no source-map, coverage, link, alias, provenance, or activity-log issues.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged.
- `provenance`: lint reported zero issues across 56 checked Markdown files.
- `derived output`: none.
- `vault`: inventory detected an Obsidian-native vault with shared `.obsidian/templates` and `.obsidian/snippets`, 290 Obsidian links, and zero Markdown links or embeds.
- `path map`: none.
- `link/backlink impact`: all checked local Obsidian links resolved.
- Risks / rollback: shared `.obsidian/` surfaces remain warning-level review paths by design; no blocking lint issues remain.
- Follow-up:
  - Keep future KB batches additive and rerun `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered` after changes.

### [2026-05-01 16:05] Resume KB enrichment with subagent audit

- Mode: audit + ingest + enrich
- Summary: Used read-only subagents to identify KB consistency issues and next additive gaps, then fixed `source_count`/coverage row mismatches and added planning corpus coverage for sync inventory, drift ledgers, and harness fixture support.
- `raw`: added `raw/sources/planning-corpus-drift-source.md` as a pointer summary for planning manifests and overhaul planning docs.
- `wiki`: added [[planning-corpus-and-drift-ledgers]] and refreshed sync safety, harness fixture gaps, known risks, and root index links.
- `indexes`: updated `source-map`, `coverage`, `repo-map`, and `glossary` for the planning source and corrected source-count semantics to count distinct backing sources per page or index.
- `schema`: corrected `source_count` metadata on schema pages to match cited source notes; content contracts unchanged.
- `config`: unchanged.
- `canonical material`: unchanged; planning files outside `kb/` were read as evidence only.
- `provenance`: new claims cite repo-local planning source notes; no external docs were promoted to repo authority.
- `derived output`: none.
- `vault`: renamed the raw planning note to avoid an ambiguous Obsidian basename collision with the wiki topic page.
- `path map`: raw planning source note path is `raw/sources/planning-corpus-drift-source.md`; wiki topic path is `wiki/topics/planning-corpus-and-drift-ledgers.md`.
- `link/backlink impact`: root, source, coverage, repo, glossary, sync, fixture, and risk pages now link the planning corpus without ambiguous wiki targets.
- Risks / rollback: additive Markdown-only batch under `kb/`; rollback should remove the planning source/wiki page and revert the touched KB indexes/topic metadata only.
- Follow-up:
  - Re-run Nerdbot lint and inventory after this batch.
  - Consider a separate hooks/evals source and wiki page if more KB enrichment is requested.

### [2026-05-01 17:20] Apply autoresearch KB enrichment

- Mode: research + ingest + enrich + cleanup
- Summary: Used read-only research subagents to extend the KB with hooks/evals, OpenSpec archive status, agent publication drift, skill risk/eval coverage, and docs artifact freshness coverage.
- `raw`: added pointer summaries for hooks/evals control plane, OpenSpec change archive status, agent publication drift, skill catalog risk/eval coverage, and docs artifact freshness.
- `wiki`: added [[hooks-evals-control-plane]], [[openspec-change-archive-status]], [[agent-publication-and-drift-coverage]], and [[skill-catalog-risk-and-eval-coverage]]; enriched docs generation, OpenSpec workflow, agent dialects, skill authoring, validation coverage, wagents automation, and known risks pages.
- `indexes`: updated `source-map`, `coverage`, `repo-map`, `glossary`, and root wiki navigation for the new source and topic coverage.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged; repo files outside `kb/` were read as evidence only.
- `provenance`: new and refreshed claims cite repo-local raw pointer summaries or existing KB sources; no external source was promoted to repo authority.
- `derived output`: none.
- `vault`: cleanup removed editor metadata from the KB root; no shared template or snippet behavior changed.
- `path map`: none; no migration, move, or canonical-material rewrite occurred.
- `link/backlink impact`: root, coverage, source, repo, glossary, and related-page links now expose the new topics without introducing intentional aliases that collide with raw notes.
- Risks / rollback: additive Markdown-only batch under `kb/` plus removal of `kb/.DS_Store`; rollback should remove the five raw source notes, four wiki pages, and revert touched indexes/topic pages.
- Follow-up:
  - Run Nerdbot lint and inventory after this batch.
  - Consider actual code/docs fixes for agent publication drift, OpenSpec archive readiness, missing risk-adjusted evals, and docs freshness only as separate non-KB tasks.

### [2026-05-01 17:30] Verify autoresearch enrichment

- Mode: audit + cleanup
- Summary: Ran Nerdbot lint and inventory after the autoresearch enrichment and fixed ambiguous Obsidian link targets by renaming two raw source notes away from their wiki page basenames.
- `raw`: renamed the hooks/evals raw note to `raw/sources/hooks-evals-control-source.md` and the OpenSpec archive raw note to `raw/sources/openspec-change-archive-source.md`; source IDs stayed stable.
- `wiki`: unchanged after ambiguity fixes except evidence paths now cite the renamed raw notes.
- `indexes`: updated source-map, coverage, repo-map, glossary, and evidence references to the renamed raw note paths.
- `schema`: unchanged.
- `config`: corrected `config/obsidian-vault.md` `source_count` to match cited backing sources.
- `canonical material`: unchanged.
- `provenance`: lint reported zero issues after the ambiguity and metadata fixes.
- `derived output`: none.
- `vault`: inventory reported an Obsidian-native vault with no volatile `.DS_Store` metadata under the KB root.
- `path map`: `raw/sources/hooks-evals-control-source.md` backs [[hooks-evals-control-plane]]; `raw/sources/openspec-change-archive-source.md` backs [[openspec-change-archive-status]].
- `link/backlink impact`: ambiguous links for hooks/evals and OpenSpec archive pages were resolved by raw-note renames.
- Risks / rollback: additive Markdown-only verification/fix batch under `kb/`; rollback should preserve the raw/wiki basename separation if the pages remain.
- Follow-up:
  - Keep future raw source basenames distinct from wiki page basenames to avoid ambiguous Obsidian links.

### [2026-06-23] Maximal KB enrichment batch

- Mode: research + ingest + enrich + audit
- Summary: Completed exhaustive-tier parallel research and additive KB enrichment for catalog authoring, MCPHub, platform adapters, CI/scripts, OpenSpec lifecycle, and refreshed partial wiki pages with Phase 4 fix-candidate queue.
- `raw`: added six source notes (`skills-catalog-authoring-lifecycle-source`, `mcphub-control-plane-source`, `wagents-platform-adapters-source`, `ci-release-workflows-source`, `scripts-validation-tooling-source`, `openspec-active-lifecycle-source`); refreshed `raw/captures/local-inventory-summary.md`.
- `wiki`: added [[obsidian-vault-conventions]], [[curated-catalog-authoring]], [[mcphub-control-plane]], [[wagents-platform-adapters]], [[ci-and-release-workflows]], [[scripts-and-validation-tooling]]; deep-enriched [[docs-generation-and-site]], [[sync-transaction-safety]], [[openspec-change-archive-status]], [[agent-publication-and-drift-coverage]], [[harness-fixture-gaps]], [[skill-catalog-risk-and-eval-coverage]], [[known-risks-and-open-gaps]]; refreshed [[wiki/index]].
- `indexes`: updated `source-map`, `coverage`, `repo-map`, and `glossary` for new sources, topics, paths, and glossary terms.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: unchanged; repo files outside `kb/` were read as evidence only.
- `provenance`: wiki claims cite `kb/raw/sources/*` and `kb/raw/captures/local-inventory-summary.md`; no secrets captured.
- `derived output`: none.
- `vault`: removed `kb/.DS_Store`; Markdown-only mutations under `kb/`.
- `path map`: none.
- `link/backlink impact`: resolved missing obsidian-vault wiki target as [[obsidian-vault-conventions]]; new topics linked from root index and coverage index.
- Risks / rollback: additive `kb/` batch only; Phase 4 repo fixes documented in [[known-risks-and-open-gaps]] for separate commits.
- Follow-up:
  - Run Nerdbot lint and inventory with `--fail-on warning`.
  - Execute Phase 4 fix candidates outside `kb/` when maintainer requests repo fixes.

## 2026-06-24 — Phase 4 shipped + catalog hardening follow-up

- `raw`: unchanged.
- `wiki`: refreshed [[known-risks-and-open-gaps]] and [[agent-publication-and-drift-coverage]] to mark Phase 4 items shipped.
- `indexes`: unchanged.
- `schema`: unchanged.
- `config`: unchanged.
- `canonical material`: repo commits `69e2d6e` through `85a5589` shipped compose parity, Copilot agent corpus reconciliation, catalog audit CLI, docs browser, and CI docs gates.
- `provenance`: status updates cite shipped commits and existing tests; no live installs.
- `derived output`: none under `kb/`.
- `vault`: unchanged.
- `path map`: none.
- `link/backlink impact`: none.
- Risks / rollback: KB-only status refresh; repo fixes already on `main`.
- Follow-up:
  - Expand skill eval coverage for R3/R4 workflows.
  - Promote harness rollback fixtures from `planned` to executable.

## 2026-06-24 — Eval coverage, rollback fixtures, OpenSpec archive (subagent batch)

- `raw`: unchanged.
- `wiki`: refreshed [[skill-catalog-risk-and-eval-coverage]], [[harness-fixture-gaps]], [[known-risks-and-open-gaps]] for 56/56 eval manifests, rollback fixture tests, and archived OpenSpec changes.
- `canonical material`: repo commits `13d90e66` (27 eval manifests), `4415258` (rollback fixtures), `8172c4f` (OpenSpec archives), `903489f9` (prior KB archive note).
- `provenance`: counts from eval inventory + harness-fixture-support.json + openspec validate output.
- Follow-up: live E4 eval runs for highest-risk skills; promote plan-only harness fixtures.

### [2026-06-24] OpenSpec archive hygiene for completed changes

- Mode: archive + kb status sync (additive)
- Summary: Archived two completed OpenSpec changes (tasks.md all [x], shipped on main) using `wagents openspec archive` (dry-run then --apply --yes). Updated KB wiki and this log minimally.
  - `harden-skill-catalog-quality` → `openspec/changes/archive/2026-06-24-harden-skill-catalog-quality/`
  - `add-grok-delegate-skill` → `openspec/changes/archive/2026-06-24-add-grok-delegate-skill/`
- Pre-archive: `uv run wagents openspec validate` (passed, 58 items), `uv run wagents validate` (passed).
- Post-archive: `uv run wagents openspec validate` (passed, 56 items), `uv run wagents validate` (passed). Archive command updated specs as side-effect (downstream-tooling, etc.).
- `wiki`: noted archived changes in [[openspec-change-archive-status]].
- `activity`: this entry (short hygiene batch record).
- `canonical material`: archive moves performed by OpenSpec CLI (tracked in git); no manual file edits outside kb/.
- Risks / rollback: KB edits are additive only. Archive dirs are the authoritative moved artifacts.
- Follow-up: none (lint run post-edit per requirements).

### [2026-06-24] OpenSpec archive of 23 READY completed changes (bulk)
- Mode: archive + kb status sync (additive)
- Summary: Archived 23 active OpenSpec changes whose tasks.md had ZERO unchecked items (READY list verified by grep count + spot reads). All followed process: quick sanity read tasks.md (0 opens), dry-run `--format json`, then `--apply --yes` (12 used extra `--skip-specs` to bypass stale delta header matches on specs that were already current; archive move still succeeded). No hard failures. All 23 moved to dated `2026-06-24-*` dirs.
  - Full list: add-audited-external-skills, add-first-class-cursor-support, add-harness-safe-mcphub-group, add-opencode-plugins-golang-skills, add-ossinsight-supathings-mcps, avoid-default-legacy-migration-logic, complete-nerdbot-implementation, docs-copy-reduction, enhance-docs-skill-indexes, enrich-curated-catalog-pages, enrich-harness-master-ecosystem-research, expose-mcphub-chatgpt-tunnel, global-wagents-cli, improve-instruction-corpus, integrate-chrome-devtools-skills, integrate-opencode-plugins, integrate-opencode-rules-ocx-terminal-progress, make-opencode-model-picker-owned, modernize-ty-ruff-tooling, oss-friendly-codebase-standardization, overhaul-codex-hooks, stabilize-mcphub-opencode-runtime, stabilize-opencode-gpt55-tui.
- Pre-archive: confirmed 0 `- [ ]`, ran validates.
- Post-archive: `uv run wagents openspec validate` (passed, 33/33), `uv run wagents validate` (passed).
- `wiki`: batch summary + evidence row added to [[openspec-change-archive-status]].
- `activity`: this entry.
- `canonical material`: archive performed exclusively via `uv run wagents openspec archive` (no manual edits to non-kb); some spec.md updates applied as side-effect for non-skipped.
- Risks / rollback: KB edits additive only.
- Follow-up: run kb lint.

### [2026-06-24] Push batch 2 + eval adequacy + grok fixture promotion

- Mode: ship + fix (additive KB)
- Summary: Pushed 17 local commits (`d3c4063b..a6eaf259`) covering bulk OpenSpec archive, `wagents eval adequacy`, plan fixture tests (Copilot merge + Gemini MCP), and docs fixes. Post-push validation: `wagents validate`, `wagents openspec validate` (33/33), targeted pytest green.
- `canonical material`: `f9496f22` eval adequacy CLI; `7cd67b6a` plan fixtures; `a6eaf259` bulk archive; follow-up fix strips NOT-for exclusions from risk-tier inference (`agent-conventions`, `shell-scripter` no longer false R3); `grok-build` promoted to `fixture-executable` with `test_grok_platform.py` + grok rollback tests.
- `wiki`: refresh [[harness-fixture-gaps]] and [[skill-catalog-risk-and-eval-coverage]] if stale after promotion.
- Risks / rollback: KB-only delta; repo changes are additive tests + manifest rows.
- Follow-up: remaining plan-only harnesses (claude-desktop, cherry-studio); active OpenSpec waves (`compose-harness-catalog-pages`).

### [2026-06-24] Cursor harness review remediation (RV-001–RV-007)

- Mode: fix + docs + kb enrich (additive)
- Summary: Closed session review findings RV-001–RV-007 after promoting Cursor surfaces: docs intro no longer contradicts validated rows; `cursor-bugbot` downgraded to `repo-present-validation-required` with `rollback: planned`; manifest `notes[]` drives executable-list copy; ACP fixture renamed `project-config-fixture`; eval adequacy narrows backtick stripping to field-doc bullets; cloud/ACP tests exercise adapter render paths.
- `canonical material`: `wagents/docs.py`, `wagents/eval_adequacy.py`, `config/harness-surface-registry.json`, `planning/manifests/harness-fixture-support.json`, targeted tests, regenerated `docs/src/content/docs/harness-support.mdx`.
- `wiki`: refreshed [[harness-fixture-gaps]] and [[skill-catalog-risk-and-eval-coverage]].
- Risks / rollback: tier downgrade is honesty-only; no runtime behavior change.
- Follow-up: add cursor-specific rollback fixtures before re-promoting `cursor-bugbot` to validated.

### [2026-06-24] Harness review remediation RV-008–RV-014

- Mode: fix + docs + kb (additive)
- Summary: Synced `hook-surface-registry.json` Cursor tiers with harness registry; added `cursor_rollback` and `grok_rollback` tests in `test_harness_rollback_fixtures.py`; G3/G4 gates for validated rollback commands and pytest `-k` collect-only; deepened ACP render compare and stable cloud hook matcher lookup; docs intro documents rollback bar; `cursor-acp` rollback set to `planned`.
- `canonical material`: hook/harness registries, harness-fixture-support manifest, rollback/plan/validation-command tests, `wagents/docs.py`, regenerated harness-support page.
- `wiki`: [[harness-fixture-gaps]] rollback model corrected (merge-preservation + drop-guard, not only `.bak`).
- Risks / rollback: honesty/tests only; no sync behavior change.
