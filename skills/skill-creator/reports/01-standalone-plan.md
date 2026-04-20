# Repo-Wide Skill Refinement Program: Standalone Plans

Date: 2026-04-19

Approval source:
- source: user-approved implementation prompt in the current thread
- promoted set size: `15`
- extraction method: direct from approved plan, then grounded against live `audit.py` output and current `SKILL.md` surfaces

Program rules:
- These are implementation-ready planning artifacts.
- They do not authorize edits outside the named skill until that skill's plan is actively being executed.
- Preserve current directory names and public mode keywords unless a proven routing defect requires an alias-preserving change.

## Ordered Promoted Set

1. `data-pipeline-architect`
2. `schema-evolution-planner`
3. `event-driven-architect`
4. `release-pipeline-architect`
5. `observability-advisor`
6. `incident-response-engineer`
7. `shell-conventions`
8. `python-conventions`
9. `orchestrator`
10. `add-badges`
11. `host-panel`
12. `honest-review`
13. `prompt-engineer`
14. `simplify`
15. `skill-creator`

## Implementation Lanes

- `prompt/body structure`: dispatch, empty/help behavior, classification gates, scaling rules, approval boundaries
- `references/scripts/templates`: move deep detail out of `SKILL.md` and into progressive-disclosure surfaces
- `eval coverage`: expand `evals/evals.json` to match real mode count, negative controls, and misroute risk
- `verification`: `wagents validate`, `wagents eval validate`, `audit.py`, packaging dry-run, docs/readme checks only when needed
- `approval discipline`: each skill starts with baseline audit + plan confirmation before edits

## Wave Plan

- Wave 1: thin-surface architect/advisor skills (`data-pipeline-architect` through `incident-response-engineer`)
- Wave 2: conventions and orchestration contract skills (`shell-conventions`, `python-conventions`, `orchestrator`)
- Wave 3: bespoke non-standard skills (`add-badges`, `host-panel`)
- Wave 4: central lens skills (`honest-review`, `prompt-engineer`, `simplify`, `skill-creator`)

Work one skill at a time inside each wave. Do not batch-edit multiple promoted skills in one commit.

## Per-Skill Deliverable Cards

### 1. `data-pipeline-architect`

Why promoted now:
- `81 / B`
- complex architecture skill with no `references/`, no eval surface, and no explicit classification gate

Current gap snapshot:
- strong core vocabulary and mode set
- weak routing away from schema design, BI, and platform-ops prompts
- no structured support for replay, late data, checkpointing, or cost-vs-correctness tradeoffs

Required deliverables:
- add `Classification Gate`
- add `Scaling Strategy`
- add `State Management`
- add reference files for failure modes, decision matrix, examples, and output templates
- add `evals/evals.json` for empty args, all five modes, and common misroutes

Expected files/surfaces:
- `skills/data-pipeline-architect/SKILL.md`
- `skills/data-pipeline-architect/references/*`
- `skills/data-pipeline-architect/evals/evals.json`

Verification:
- `uv run wagents validate`
- `uv run wagents eval validate`
- `uv run python skills/skill-creator/scripts/audit.py skills/data-pipeline-architect/`
- package dry-run for the touched skill

Dependencies / notes:
- preserve existing mode names exactly
- do not widen into vendor-specific pipeline implementation

### 2. `schema-evolution-planner`

Why promoted now:
- `83 / B`
- solid migration logic but thin support for failure patterns and ambiguous routing

Current gap snapshot:
- strong expand-contract core
- no explicit gate between schema evolution, fresh schema design, DBA work, and release choreography
- no reusable migration matrices or rollout examples

Required deliverables:
- add `Classification Gate`
- add `Scaling Strategy`
- add refs for migration failure modes, change-type decision matrix, sample rollout sequences, and output templates
- add evals for rename-vs-redesign ambiguity, backfill idempotence, cutover abort criteria, empty args, and out-of-scope DBA tuning

Expected files/surfaces:
- `skills/schema-evolution-planner/SKILL.md`
- `skills/schema-evolution-planner/references/*`
- `skills/schema-evolution-planner/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- keep mode names `plan`, `review`, `backfill`, `cutover`, `deprecate`

### 3. `event-driven-architect`

Why promoted now:
- `83 / B`
- strong concepts, weak progressive disclosure for replay, saga, and contract-failure decisions

Current gap snapshot:
- good mode surface
- no formal rejection path for CRUD/API design, ETL confusion, or broker-installation asks
- no reusable decision aids for event-vs-command or choreography-vs-orchestration

Required deliverables:
- add `Classification Gate`
- add `Scaling Strategy`
- add refs for event-vs-command decisions, failure modes, saga comparison, and output templates
- add evals for empty args, mode separation, and out-of-scope CRUD/API prompts

Expected files/surfaces:
- `skills/event-driven-architect/SKILL.md`
- `skills/event-driven-architect/references/*`
- `skills/event-driven-architect/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve current mode names and argument patterns

### 4. `release-pipeline-architect`

Why promoted now:
- `84 / B`
- strong release semantics but no supporting matrix/checklist surfaces and weak front-end classification

Current gap snapshot:
- concise and credible core
- CI optimization, deploy debugging, and infra asks can still bleed into this skill
- no reference-backed guidance for rollout choices or provenance failure cases

Required deliverables:
- add `Classification Gate`
- add `Scaling Strategy`
- add refs for rollout decision matrix, provenance/evidence checklist, failure modes, and runbook/checklist templates
- add evals for all modes plus CI/debugging/infra misroutes

Expected files/surfaces:
- `skills/release-pipeline-architect/SKILL.md`
- `skills/release-pipeline-architect/references/*`
- `skills/release-pipeline-architect/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- do not convert this into generic CI or deploy-debug guidance

### 5. `observability-advisor`

Why promoted now:
- `87 / B`
- nearest to `Tune`, but still below `90` and missing refs/evals expected for a multi-mode advisor skill

Current gap snapshot:
- already has `Classification Gate`, `Scaling Strategy`, and `State Management`
- lacks reusable templates and examples for mixed `design` / `alert` / `slo` / `investigate` prompts
- critical rules can become more operational and less principle-like

Required deliverables:
- preserve current gate/scale/state semantics
- add refs for signal-selection matrix, alert anti-patterns, SLI/SLO examples, investigation workflows, and output templates
- tighten critical rules into more direct operator constraints
- add evals for mixed-mode prompts, empty args, and out-of-scope vendor/incident-command requests

Expected files/surfaces:
- `skills/observability-advisor/SKILL.md`
- `skills/observability-advisor/references/*`
- `skills/observability-advisor/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- keep current mode names unchanged

### 6. `incident-response-engineer`

Why promoted now:
- `86 / B`
- strong main contract, weak supporting structure for severity/comms/timeline patterns

Current gap snapshot:
- credible incident workflow
- no formal classification gate away from routine debugging, proactive security, or pure observability design
- no reference-backed severity matrix or comms templates

Required deliverables:
- add `Classification Gate`
- add `Scaling Strategy`
- add refs for severity matrix, communications templates, timeline/postmortem examples, and containment/recovery decision aids
- add evals for triage/stabilize/comms/review routing, weak-signal prompts, empty args, and non-incident misroutes

Expected files/surfaces:
- `skills/incident-response-engineer/SKILL.md`
- `skills/incident-response-engineer/references/*`
- `skills/incident-response-engineer/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve `fact / inference / hypothesis` discipline

### 7. `shell-conventions`

Why promoted now:
- `81 / B`
- thinnest conventions skill in the repo; no refs, no evals, no progressive disclosure

Current gap snapshot:
- useful core rules
- empty/help and `check` behavior are vague
- redirection boundaries against `shell-scripter` and `devops-engineer` are too light for auto-invoke behavior

Required deliverables:
- rewrite around explicit operator contract for active auto-invoke, empty/help, and `check`
- add refs for script baseline, Make/Just rules, redirection boundaries, and check-mode behavior
- tighten auto-invocation trigger logic and mixed-task non-trigger cases
- add evals for shell files, Makefiles, CI YAML false triggers, and redirection cases

Expected files/surfaces:
- `skills/shell-conventions/SKILL.md`
- `skills/shell-conventions/references/*`
- `skills/shell-conventions/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve public invocation names exactly

### 8. `python-conventions`

Why promoted now:
- `86 / B`
- strong repo-tooling rules, but operator contract and preference-vs-requirement lines remain too blurry

Current gap snapshot:
- hard rules for `uv` and `ty` are clear
- empty/help and mixed-language behavior are too shallow
- preferred-library table reads as stronger law than the exceptions framework supports

Required deliverables:
- convert body into clearer operator contract for active, empty/help, and `check`
- keep current refs and add tooling-contract plus redirection-boundaries refs
- separate hard requirements from guided preferences
- add evals for mixed Python/shell, mixed Python/JS, legacy-exception path, and rejection of `mypy`, `pip install`, or bare `python`

Expected files/surfaces:
- `skills/python-conventions/SKILL.md`
- `skills/python-conventions/references/*`
- `skills/python-conventions/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve public invocation names exactly

### 9. `orchestrator`

Why promoted now:
- `86 / B`
- central execution skill with strong doctrine but insufficiently formalized supporting structure

Current gap snapshot:
- powerful decomposition and tier model
- runtime claims and near-miss orchestration cases can drift
- too much doctrine is repeated inline rather than stabilized in refs

Required deliverables:
- tighten main operator contract for when to invoke, how to choose patterns, and how to recover/report
- expand refs with classification-gate, progress-accounting, runtime-capability-boundaries, and misroute examples
- sharpen empty/help gallery and near-miss behavior
- add evals for false trigger on single-action or same-file sequential work and for phase-gated skill precedence

Expected files/surfaces:
- `skills/orchestrator/SKILL.md`
- `skills/orchestrator/references/*`
- `skills/orchestrator/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve existing public commands: empty, `pattern <A-F>`, `tier`, `recovery`

### 10. `add-badges`

Why promoted now:
- `85 / B`
- non-standard shape: strong mechanics, weak canonical routing contract

Current gap snapshot:
- body starts directly in phases
- CLI flag surface is rich but front-door mode semantics are implicit
- write approval, missing-info, and `--replace` branches need stronger gating and evals

Required deliverables:
- recast into canonical dispatch + empty/help gallery while preserving flag surface exactly
- keep detect/select/present/insert as internal execution phases
- add stronger approval boundaries and stop-hooks around README writes
- add evals for `--dry-run`, `--replace`, approval-required writes, and missing required info

Expected files/surfaces:
- `skills/add-badges/SKILL.md`
- existing refs/scripts remain load-bearing
- add or consolidate into `skills/add-badges/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence
- confirm docs/readme checks only if discovery-facing copy changes

Dependencies / notes:
- preserve current `argument-hint` and CLI flags without renaming

### 11. `host-panel`

Why promoted now:
- `88 / B`
- content-rich but structurally non-canonical and right at the line-budget edge

Current gap snapshot:
- good empty-args gallery and argument contract exist only as prose
- anti-fabrication posture is present but not front-loaded enough
- body is too large to safely grow without extraction

Required deliverables:
- add canonical dispatch table and formal empty/help gallery
- preserve exact argument contract and format names
- move dense operational detail into refs for topic diagnostic, moderator rules, and synthesis
- centralize anti-fabrication rules and add evals for weak-topic, settled-topic, and under-researched-topic branches

Expected files/surfaces:
- `skills/host-panel/SKILL.md`
- expand `skills/host-panel/references/*`
- add or consolidate into `skills/host-panel/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- do not weaken current research/citation integrity requirements

### 12. `honest-review`

Why promoted now:
- central lens skill; high score, but body/templates/evals drift on core review contract

Current gap snapshot:
- reasoning-first finding contract is stronger in the body than in output templates
- small-scope vs full-team scaling semantics drift between body, refs, and evals
- duplicated orchestration text increases maintenance risk

Required deliverables:
- unify scaling contract across body, refs, and evals
- make reasoning-first output explicit in the common templates
- separate read-only review templates from post-approval/post-fix report templates
- expand evals for `history`, `diff`, approval-gate behavior, and reasoning-first output

Expected files/surfaces:
- `skills/honest-review/SKILL.md`
- `skills/honest-review/references/*`
- `skills/honest-review/evals/*` or canonical manifest

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve core wave model and evidence-validation posture

### 13. `prompt-engineer`

Why promoted now:
- central lens skill; high score, but heuristics and repeated preflight logic still create drift risk

Current gap snapshot:
- auto-detect is brittle for mixed or low-signal inputs
- common preflight steps repeat across modes
- negative-control and scope-refusal eval coverage is not deep enough

Required deliverables:
- introduce a shared preflight block for ingest, model class, context, and trust boundary
- tighten auto-detect with an explicit ask-first path for ambiguous cases
- strengthen scope-boundary / refusal contract for non-prompt work
- add evals for ambiguous craft-vs-analyze, malformed text, and scope refusal

Expected files/surfaces:
- `skills/prompt-engineer/SKILL.md`
- `skills/prompt-engineer/references/*`
- `skills/prompt-engineer/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve current public mode names

### 14. `simplify`

Why promoted now:
- central lens skill; structurally strong, but the remaining risk is exactly in its safety boundary logic

Current gap snapshot:
- auto-apply heuristic still invites overreach on vague requests
- snippet handling is declared but not sharply differentiated between analyze/explain/apply
- behavior-preservation verification should be more operational in the main contract

Required deliverables:
- tighten auto-apply gating
- define explicit snippet behavior for analyze, explain, and apply
- strengthen fallback-to-analyze or ask behavior when proof is weak
- add evals for snippet-only, mixed snippet/file, and ambiguous active-diff prompts

Expected files/surfaces:
- `skills/simplify/SKILL.md`
- `skills/simplify/references/*`
- `skills/simplify/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- preserve narrow non-behavior-changing scope

### 15. `skill-creator`

Why promoted now:
- central authority skill; already structurally strong, but repo-wide planning and approval-gate enforcement are still under-specified

Current gap snapshot:
- single-skill creation/improvement flow is strong
- repo-wide or multi-skill planning branch is still implied more than explicitly contracted
- approval-gate behavior needs stronger eval-backed enforcement

Required deliverables:
- add explicit repo-wide / multi-skill planning workflow branch
- define standalone refinement-plan output contract
- harden plan-before-edit behavior for existing-skill and repo-wide requests
- expand `evals/evals.json` to cover repo-wide planning, standalone-plan generation, and no-edit-before-approval enforcement

Expected files/surfaces:
- `skills/skill-creator/SKILL.md`
- `skills/skill-creator/references/workflow.md`
- `skills/skill-creator/references/audit-guide.md`
- `skills/skill-creator/evals/evals.json`

Verification:
- standard validate/eval/audit/package sequence

Dependencies / notes:
- keep this as repo authority; do not broaden into agent or MCP creation

## Validation Matrix

For each standalone implementation:

- `uv run wagents validate`
- `uv run wagents eval validate` when evals change
- `uv run python skills/skill-creator/scripts/audit.py skills/<name>/`
- skill-level packaging dry-run
- `uv run wagents readme --check` only when discovery-facing copy changes
- docs-steward flow only if public docs pages are affected

Acceptance bar:

- touched skill reaches `audit.py >= 90`
- no stale or missing eval coverage for changed routing
- no missing refs introduced by progressive-disclosure expansion
- no public dispatch or mode-name breakage unless alias-preserving and explicitly justified

## Risks / Blockers

- Current worktree is dirty in unrelated areas; promoted-skill execution must avoid reverting or co-mingling unrelated changes
- Several promoted skills are moving from single-file skills to multi-surface skills; execution should serialize per skill to avoid accidental docs/readme churn
- `add-badges`, `host-panel`, `honest-review`, and `skill-creator` are the highest risk for contract drift because they already have substantial custom structure

## Exit Criteria

- broad sweep remains the source-of-truth classification for all 43 skills
- each of the 15 promoted skills has an implementation-ready standalone plan
- no skill edits occur without entering the specific skill's standalone plan and running its validation sequence
