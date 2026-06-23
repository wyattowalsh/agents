---
name: review
description: Use for session, scoped, PR, range, full audit, simplification, and source/provenance reviews with evidence-first findings. NOT for feature implementation or benchmarking.
argument-hint: "[--mode <mode[,mode]> | path | audit | PR# | simplify <target> | source <source-or-path>]"
license: MIT
user-invocable: true
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Review

Use `/review` as the canonical first-party review entrypoint. It covers code review, session diffs, scoped files, PRs, full audits, behavior-preserving simplification review, source/provenance review for external skills, specialist audit lenses, browser-grounded frontend/a11y/web-quality review, review history, delta reports, false-positive learnings, SARIF output, Conventional Comments output, and approval-gated fix passes.

`honest-review`, `simplify`, and `external-skill-auditor` are not separate skills. Their behavior lives here as `/review`, `/review simplify`, and `/review source`.

Default posture: read-only, evidence-first, and scoped. Do not perform feature work, broad rewrites, installs, or fixes until the user explicitly approves selected findings or invokes a mode that permits edits and passes its gates.

## Canonical Vocabulary

Use these canonical terms exactly.

| Term | Meaning |
| --- | --- |
| **review** | Evidence-first inspection of code, diffs, PRs, repositories, sources, or proposed simplifications |
| **scope** | The exact files, directories, PR, git range, source, or snippet under review |
| **triage** | First pass that classifies scope, risk, changed files, specialist lenses, and validation requirements |
| **finding** | A discrete issue with citation, reasoning, severity, confidence, evidence, and recommended action |
| **strength** | A positive review observation that explains what should be preserved |
| **confidence** | Score from 0.0 to 1.0; report >= 0.7, mark 0.3-0.7 unconfirmed, discard < 0.3 unless P0/S0 |
| **severity** | Priority/scope classification such as P0-P3 and S0-S3 |
| **citation anchor** | A verified `[file:start-end]` source location or source/provenance anchor |
| **reasoning chain** | Why the finding matters, written before the finding statement |
| **evidence** | Tool, source, test, docs, grep, dependency, or research proof that supports or rejects a finding |
| **lens** | Specialist perspective such as security, supply chain, CI, SQL, data, frontend, a11y, web quality, MCP, agentic, or docs |
| **simplification lens** | Behavior-preserving review of complexity, invariants, semantic-change risk, and clarity opportunities |
| **source/provenance lens** | Review of external skill/source trust, executable surfaces, owner, license, credentials, network behavior, and dedupe |
| **approval gate** | Mandatory pause before editing files or applying fixes |
| **learning** | Stored false-positive dismissal used to reduce repeated noise in future reviews |
| **mode** | Explicit or inferred review workflow such as session, scoped, PR, range, audit, simplify, source, history, delta, learnings, or fix |
| **shard map** | Wave 0 ownership plan for large parallel reviews, with lane IDs, shard IDs, file/source ownership, coverage expectations, and merge status |

## Dispatch

Classify `$ARGUMENTS` before reading widely.

| `$ARGUMENTS` | Mode | Action |
| --- | --- | --- |
| `--mode session|scoped|pr|range|audit|simplify|source|history|delta|learnings|fix` | explicit mode | Run only the selected mode against the provided or inferred target |
| repeated `--mode` or comma-separated `--mode scoped,source` | multi-mode | Run read-only modes as separate lanes and merge through Judge |
| empty + changed files in `git diff --name-only HEAD` | session | Review changed files only |
| empty + no changed files | menu | Show review modes; never start a full audit implicitly |
| file or directory path | scoped | Review that path |
| `audit` | full audit | Review the repository through triage, specialist lanes, and judge reconciliation |
| PR number or PR URL | PR | Review PR diff and stated intent |
| git range such as `HEAD~3..HEAD` | range | Review changes in that range |
| `simplify analyze <target>` | simplify analyze | Read-only simplification opportunity review |
| `simplify apply <target>` | simplify apply | Behavior-preserving edit only after the simplification gate passes |
| `simplify explain <target>` | simplify explain | Explain complexity and safer simpler shapes without editing |
| `source triage <source>` | source triage | Classify external source reputation, install syntax, and dedupe risk |
| `source inspect <path>` | source inspect | Review local source files, hooks, scripts, frontmatter, and commands |
| `source commands <path>` | source commands | Extract and classify executable surfaces |
| `source provenance <source>` | source provenance | Check owner, URL, license, commit/hash, registry/source-list consistency, and access date |
| `source decision <source-or-path>` | source decision | Recommend install-now, inspect, keep-global, build-local, or avoid |
| `source scan <path>` | source scan | Run static source audit helper and interpret JSON output |
| `--lens security|supply-chain|ci|sql|data|frontend|a11y|web-quality|mcp|agentic|docs` | specialist | Overlay an explicit specialist lens on the selected scope |
| `--format sarif` | output modifier | Emit SARIF v2.1 findings in addition to or instead of text |
| `--format conventional` | output modifier | Emit Conventional Comments-compatible PR review output |
| `history [project]` | history | Read stored review history |
| `diff [project]` or `delta [project]` | delta | Compare current and previous stored reviews |
| `learnings add|list|check|clear` | learnings | Manage false-positive review learnings |
| `fix <finding-ids>` or `apply approved findings` | fix pass | Apply only explicitly approved findings through `references/auto-fix-protocol.md` |
| unrecognized or ambiguous | clarify | Ask one concise scope/mode question |

## Auto-Detection

1. Parse explicit `--mode` flags first. Split comma-separated values and preserve repeated flags.
2. If explicit modes are present, run only those modes. Infer the target when safe, but never infer edit approval.
3. If no explicit mode is present, infer from args: empty changed diff -> session, empty clean tree -> menu, path -> scoped, PR number/URL -> PR, git range -> range, `audit` -> full audit, `simplify` -> simplification, `source` or external skill/source language -> source/provenance.
4. Multiple read-only modes run as separate lanes and reconcile through Judge.
5. `fix` and `simplify apply` are edit-capable. Never run them from inference alone and never mix them into a read-only bundle without explicit approved finding IDs.
6. `--lens` modifies the selected mode; it does not invent scope.
7. `--format` modifies output only; it does not choose scope.
8. Feature work, benchmarking, broad refactors, installs, or implementation requests without approved findings are out of scope.

## Scope Boundaries

In scope: review findings, source/provenance decisions, simplification analysis, simplification explanations, narrowly gated simplification apply passes, stored review history, review deltas, false-positive learnings, and approved post-review fixes.

Out of scope: new features, product implementation, benchmark design, broad refactors, live external installs, destructive cleanup, exploit execution, unaudited source promotion, and unapproved fixes.

## Classification Logic

1. Decide whether the request is review, simplification, source/provenance, state/history, output formatting, or implementation.
2. Reject implementation unless it is an approved finding fix or a `simplify apply` target that passes the eligibility gate.
3. Reject source installs unless the user separately requests a live install after the source/provenance decision.
4. When two modes could apply, prefer the read-only mode first and ask one concise question only if the target or approval state is unclear.

## Scaling Strategy

| Size | Strategy |
| --- | --- |
| Small | One file, snippet, or narrow source: run a single reviewer pass with the full finding contract |
| Medium | 2-5 related files: split by file ownership when safe and reconcile through judge protocol |
| Large | PR, git range, or mixed module diff: triage first, then assign non-overlapping review lanes by risk |
| Full audit | Create a Wave 0 shard map, assign risk-tiered non-overlapping lanes, run specialist lenses, and reconcile through Judge |
| Source/provenance bundle | Split metadata, executable surfaces, credentials/network, license/provenance, and dedupe checks |

## Progressive Disclosure

Start with this file only. Load reference files after dispatch and only for the chosen mode or lens. Do not preload all references for small reviews.

## Review Pipeline

1. **Triage**: identify scope, changed files, public contracts, project instructions, dependency graph, risk tier, and specialist lenses.
2. **Shard**: for large or multi-mode work, produce a Wave 0 shard map before spawning reviewers.
3. **Analyze**: inspect code/source using content-adaptive reviewers. Keep ownership non-overlapping when parallelizing.
4. **Verify**: check every non-trivial finding against source lines, tests, grep evidence, docs, or external research.
5. **Judge**: normalize, assign canonical `RV-*` IDs, dedupe, resolve conflicts, apply confidence thresholds, rank by severity/confidence/blast radius, and preserve strengths.
6. **Report**: present findings first, ordered by severity, with concise evidence and an approval gate.
7. **Fix pass**: only after explicit approval of selected finding IDs, load `references/auto-fix-protocol.md`, preview diffs, apply narrowly, and verify.

### Large Review Shards

For large or multi-mode reviews, every subagent must receive a lane ID, shard ID, exact scope, coverage expectations, non-goals, and artifact contract before dispatch.

### Judge Handoff

Worker findings use local IDs only. The Judge assigns canonical `RV-*` IDs after all lane artifacts are normalized, deduped, confidence-filtered, and ranked.

## Finding Contract

Every finding uses this order:

1. **Citation**: verified `[file:start-end]`, PR hunk, source URL, command output anchor, or provenance anchor.
2. **Reasoning**: why this matters and what breaks if it is left alone.
3. **Finding**: one concise statement of the issue.
4. **Severity and confidence**: P0-P3/S0-S3 plus 0.0-1.0 confidence.
5. **Evidence**: source/tool/research/test proof; include degraded-mode limits when tools are unavailable.
6. **Recommendation**: smallest safe next step.

Use `references/finding-contract.md` for full schema and scoring.

## Lens Contracts

Load references only when the selected mode needs them.

| Need | Read |
| --- | --- |
| finding schema and scoring | `references/finding-contract.md` |
| triage/scaling | `references/triage-protocol.md` |
| review checklists | `references/checklists.md` |
| reviewer team prompts | `references/team-templates.md` |
| creative review lenses | `references/review-lenses.md` |
| research validation | `references/research-validation.md` |
| judge reconciliation | `references/judge-protocol.md` |
| self-verification | `references/self-verification.md` |
| output variants | `references/output-formats.md` |
| SARIF output | `references/sarif-output.md` |
| Conventional Comments output | `references/conventional-comments.md` |
| CI annotations and automation | `references/ci-integration.md` |
| dependency graph and blast radius | `references/dependency-context.md` |
| supply-chain security | `references/supply-chain-security.md` |
| specialist lens map | `references/specialist-lenses.md` |
| simplification lens | `references/simplification-lens.md` |
| simplification taxonomy | `references/simplification-taxonomy.md` |
| source/provenance lens | `references/source-provenance-lens.md` |
| approval-gated fixes | `references/auto-fix-protocol.md` |

## Simplification Lens

`/review simplify` is behavior-preserving. It may identify or apply clarity improvements only when the target, unchanged invariants, validation basis, and scope boundaries are explicit.

- `analyze`: read-only report.
- `explain`: teaching/explanation only.
- `apply`: edit only a concrete file/symbol/snippet or tightly bounded diff after the eligibility gate passes.

Reject semantic changes, bug fixes, API changes, validation changes, security-policy changes, performance-only work, or broad refactors under simplification mode.

## Source/Provenance Lens

`/review source` is the trust gate for external skills and sources. Use source-list and read-only inspection before any install or promotion decision. Inspect hooks, scripts, command substitutions, allowed tools, package scripts, network calls, credential behavior, filesystem writes, provenance, license, owner, commit/hash, and dedupe against repo-owned skills.

Never run candidate scripts during audit except static/syntax checks in a staged local path. Do not install or sync external skills unless the user explicitly requests that live action.

## Browser-Grounded Review

For frontend, a11y, web-quality, docs UI, and other browser-dependent review, prefer Chrome DevTools MCP through the repo-managed `chrome-devtools` MCPHub attached-browser configuration. Use browser snapshots, console/network evidence, and screenshots from Chrome DevTools MCP when available. If Chrome DevTools MCP is unavailable, state degraded mode before falling back to existing smoke tests or Playwright-oriented project checks.

## Harness Portability

This `SKILL.md` is portable and prompt-first. It deliberately omits a root model override and skill-scoped hooks.

| Harness | Behavior |
| --- | --- |
| Claude Code | Uses portable skill metadata and argument hints. Skill hooks require separate `validate_hooks.py` and package proof before being added. |
| Codex | Skill discovery and any hook behavior are projected through repo/plugin config such as `config/hook-registry.json`, not assumed from this file. |
| OpenCode | Skill discovery comes from repo `opencode.json` and skill paths; models/plugins/overlays stay in OpenCode config. |
| Grok Build CLI | Uses Claude-compatible skill mirroring and `.grok/skills` discovery where available. |
| Generic Skills CLI targets | Core prompt must install cleanly through `npx skills add` and repo sync dry-runs. |

## Script Index

| Script | Purpose |
| --- | --- |
| `scripts/check.py` | Run review skill validation, eval validation, package dry-run, and audit |
| `scripts/project-scanner.py` | Triage project/file risk and review triggers |
| `scripts/finding-formatter.py` | Normalize findings and output variants |
| `scripts/review-store.py` | Store/load/list/diff review state |
| `scripts/learnings-store.py` | Manage false-positive learnings |
| `scripts/sarif-uploader.py` | Help emit/upload SARIF where supported |
| `scripts/source-audit.py` | Static audit of local external skill/source directories |

## Critical Rules

1. Never start a full audit from empty args unless the user says `audit`.
2. Never edit files during read-only review, source/provenance review, history, delta, or simplify analyze/explain.
3. Never apply fixes without explicit approval of selected findings.
4. Never vendor third-party skill files into `skills/` during source/provenance review.
5. Always verify citation anchors before reporting findings.
6. Always state degraded-mode limits when validation tools are unavailable.
7. Always separate evidence from inference.
8. Always preserve unrelated dirty work.
9. Do not present `honest-review`, `simplify`, or `external-skill-auditor` as installable or invocable skills. Rewrite active references to `/review`, `/review simplify`, or `/review source`; leave only clearly historical or research evidence mentions.

## Validation Contract

Before considering changes complete, run the focused checks relevant to this skill:

```bash
uv run python skills/review/scripts/check.py
uv run python skills/skill-creator/scripts/audit.py skills/review
uv run python skills/skill-creator/scripts/asset_toolkit/validate_evals.py skills/review
uv run python skills/skill-creator/scripts/package.py skills/review --dry-run
```

Completion criteria: checks pass, package dry-run is portable, eval schemas validate, script smoke checks pass, generated docs/catalog surfaces are refreshed when source changes require it, and any remaining legacy-name references are classified as wrappers, migration notes, generated evidence, or historical research.
