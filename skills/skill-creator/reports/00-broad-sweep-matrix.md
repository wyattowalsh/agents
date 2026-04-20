# Repo-Wide Skill Refinement Program: Broad Sweep Matrix

Date: 2026-04-19

Scope: all 43 repo-local skills under `skills/*`

Source of truth:
- `uv run python skills/skill-creator/scripts/audit.py --all --format table`
- targeted read-only review of promoted-plan cohorts
- live `SKILL.md` inspection for routing, structure, and disclosure surfaces

Program rule:
- This sweep is read-only.
- No skill edits are authorized from this artifact alone.
- Any skill marked `Plan` requires its standalone refinement plan before implementation.

## Repo Snapshot

- Local skill count: `43`
- Catalog basis: local skills are collected from `skills/*/SKILL.md`
- Current worktree is dirty in unrelated areas; this program does not treat preexisting edits as part of the sweep
- Deliverable intent: classify every skill as `Maintain`, `Tune`, or `Plan`, then promote only the approved 15 skills into standalone plans

## 43-Skill Sweep Matrix

| skill | current audit score / grade | honest-review findings | prompt-engineer findings | simplify findings | skill-creator structural findings | action class | projected score delta | needs standalone plan |
|---|---|---|---|---|---|---|---|---|
| `add-badges` | `85 / B` | README write path, approval boundaries, and `--replace` risk branches are under-specified | Phase-only front door hides routing and empty-args behavior | Control flow is spread across phases instead of one clear dispatch contract | Missing dispatch-table and stronger progressive disclosure; evals are thin for approval and missing-info branches | `Plan` | `+10 to +15` | `yes` |
| `agent-conventions` | `98 / A` | Strong correctness posture and redirection boundaries | Dispatch is clear and low-risk | Already compact without being cryptic | Good scripts/state surfaces; only minor disclosure polish remains | `Maintain` | `+0 to +2` | `no` |
| `api-designer` | `100 / A` | Strong contract discipline; no meaningful correctness drift found | Mode routing is clear and domain-specific | Complexity is justified by scope and mostly pushed into refs/scripts | Mature multi-surface skill with refs, scripts, and templates already doing the heavy lift | `Maintain` | `+0 to +2` | `no` |
| `changelog-writer` | `99 / A` | Sound release-note contract with no major risk gaps | Dispatch/menu surface is already easy to parse | Concise and appropriately scoped | Structurally healthy; only optional disclosure polish is left | `Maintain` | `+0 to +2` | `no` |
| `data-pipeline-architect` | `81 / B` | Failure modes like replay, late data, and checkpoint tradeoffs are not deep enough | No classification gate to reject schema design, BI, or platform ops prompts | Main body is already lean; improvement should come from extracted refs, not more prose | Thin single-file skill with no refs, evals, or deeper supporting surfaces | `Plan` | `+13` | `yes` |
| `data-wizard` | `98 / A` | Good domain coverage; no major correctness concerns | Prompt surface is broad but still intelligible | Body is dense but manageable | Strong refs/scripts/templates already exist; only optional pattern depth remains | `Tune` | `+2 to +4` | `no` |
| `database-architect` | `98 / A` | Good contract clarity and boundary discipline | Dispatch is clear for major database-design asks | Complexity is mostly appropriate to scope | Strong structural surfaces; only optional gating/state improvements remain | `Tune` | `+2 to +4` | `no` |
| `devops-engineer` | `97 / A` | Safe default posture; no major contract drift | Routing is clear but could sharpen edge-case classification | Body is compact enough for current scope | Healthy refs/scripts/templates; remaining gaps are incremental | `Tune` | `+2 to +4` | `no` |
| `discover-skills` | `93 / A` | Safe and purposeful, though repo-wide recommendation logic could be more explicit | Dispatch is understandable but can be sharpened for adjacent-skill confusion | Reasonably concise for current breadth | Good audit/state/hook surfaces; more disclosure depth would help | `Tune` | `+2 to +5` | `no` |
| `docs-steward` | `100 / A` | Strong safety gates and read-vs-write separation | Robust dispatch/classification model already exists | Large body but justified by framework breadth | Deep refs/scripts and progressive disclosure are already present | `Maintain` | `+0 to +2` | `no` |
| `draw-thing` | `92 / A` | Domain contract is sound, but risk controls depend heavily on prose | Routing is acceptable but could use crisper front-door cues | Long body could eventually move more detail into refs | Good reference support; no standalone plan justified | `Tune` | `+2 to +5` | `no` |
| `email-whiz` | `92 / A` | Strong operational guidance; remaining issues are mostly breadth and consistency | Mode/flow surface is broad and could benefit from tighter disambiguation in a few paths | Dense but still coherent; more extraction would help future maintainability | Healthy refs/scripts/state; incremental disclosure improvements only | `Tune` | `+2 to +5` | `no` |
| `event-driven-architect` | `83 / B` | Ordering, replay, and saga-compensation tradeoffs need stronger support material | No formal gate for CRUD/API or ETL confusion | Core body is appropriately lean; details should move into refs | Thin single-file skill with no refs/evals for a complex architecture domain | `Plan` | `+11` | `yes` |
| `files-buddy` | `92 / A` | Good safety posture; some surface-area breadth still invites future drift | Prompt contract is broad but mostly stable | Complexity is justified by file-management scope | Strong structural base; only disclosure polish remains | `Tune` | `+2 to +5` | `no` |
| `frontend-designer` | `99 / A` | Strong design/build contract with no major correctness drift | Routing is clear and action-oriented | Large but deliberately structured | Mature ref-backed skill; no standalone work warranted | `Maintain` | `+0 to +2` | `no` |
| `git-workflow` | `101 / A` | Strong contract, careful safety boundaries, no material drift | Dispatch/menu is crisp | Compact and appropriately explicit | Structurally mature; only optional disclosure polish remains | `Maintain` | `+0 to +1` | `no` |
| `harness-master` | `97 / A` | Good operational correctness, though repo/runtime overlap boundaries could be sharper | Routing is mostly clear; a few edge cases could be tightened | Acceptably concise for current breadth | Good refs and scripts; more disclosure depth would improve long-term stability | `Tune` | `+2 to +4` | `no` |
| `honest-review` | `97 / A` | Strong review doctrine, but body, templates, and evals drift on team scaling and report structure | Reasoning-first contract is stronger in the body than in output templates | Duplication across body and refs now drives drift risk | Large, mature surface, but template/eval alignment needs coordinated cleanup | `Plan` | `+7` | `yes` |
| `host-panel` | `88 / B` | Topic-quality and evidence-quality safety are good but not consistently front-loaded or evaled | Argument contract and empty-args gallery exist only as prose, not canonical dispatch | Body is at the line-budget ceiling and needs extraction, not expansion | Missing dispatch-table and deeper progressive disclosure despite rich content | `Plan` | `+8 to +12` | `yes` |
| `incident-response-engineer` | `86 / B` | Incident flow is credible, but severity/comms/timeline support material is missing | Needs an explicit gate to reroute routine debugging and non-incident work | Body is efficient; the gap is supporting artifacts, not inline verbosity | Strong main contract but no refs/evals for a high-stakes operator skill | `Plan` | `+9` | `yes` |
| `infrastructure-coder` | `98 / A` | Correctness posture is strong | Prompt contract is clear for the main modes | Scope and complexity are justified | Good refs/scripts/templates; only optional structural gains remain | `Tune` | `+2 to +4` | `no` |
| `javascript-conventions` | `91 / A` | Useful guardrails, but the auto-invoke boundary remains terse | Dispatch is compact and could use a richer empty/help surface | Nicely short, though slightly over-compressed | Minimal refs and no deeper disclosure make this a small tune target, not a promoted plan | `Tune` | `+3 to +5` | `no` |
| `learn` | `94 / A` | Safe and narrow; no major contract gaps | Prompt surface is compact and clear enough | Already quite lean | Small structural surface is proportionate to scope | `Tune` | `+2 to +4` | `no` |
| `mcp-creator` | `99 / A` | Strong design/build safety across a complex domain | Dispatch is broad but well-structured | Large body is mostly justified and well-partitioned | Deep refs and progressive disclosure already carry complexity well | `Maintain` | `+0 to +2` | `no` |
| `namer` | `92 / A` | Good safety/availability posture; high breadth is the main future risk | Prompt contract is broad but still readable | Could move more variation detail out of the body | Strong scripts/templates/hooks base; incremental disclosure gains only | `Tune` | `+2 to +5` | `no` |
| `nerdbot` | `94 / A` | Strong operational boundaries | Routing is mostly clear, though breadth could create future ambiguity | Dense but still manageable | Good refs/scripts/progressive disclosure; only incremental gains remain | `Tune` | `+2 to +4` | `no` |
| `observability-advisor` | `87 / B` | Strongest in the cohort, but output consistency and support material are still too thin for the domain | Good mode surface, but examples and templates are missing for mixed prompts | Do not compress further; extract examples and matrices into refs | Has gate/scale/state sections already, but no refs/evals and some rules are still principle-like | `Plan` | `+8` | `yes` |
| `orchestrator` | `86 / B` | Powerful doctrine, but some runtime claims are too absolute and drift-prone | Empty-args and near-miss orchestration handling need clearer routing behavior | Main body repeats doctrine that belongs in refs | Strong central skill, but missing formal classification/state/disclosure surfaces for its complexity | `Plan` | `+9` | `yes` |
| `performance-profiler` | `97 / A` | Correctness posture is solid | Routing is clear enough for current scope | Complexity is mostly justified | Strong ref/script/template base; remaining gains are incremental | `Tune` | `+2 to +4` | `no` |
| `prompt-engineer` | `98 / A` | Main risk is wrong-mode routing and repeated preflight logic, not missing content | Auto-detect heuristics are still brittle for mixed or low-signal inputs | Repetition across modes is the main simplification target | Structurally strong, but negative-control eval depth still trails surface complexity | `Plan` | `+8` | `yes` |
| `python-conventions` | `86 / B` | Hard repo-tooling rules are clear, but some blanket preferences overreach | Dispatch is too shallow for empty/help, mixed-language, and exception cases | Body mixes policy, operator flow, and preference tables more than necessary | Has refs, but still needs stronger scaling/disclosure structure and eval depth | `Plan` | `+8` | `yes` |
| `reasoning-router` | `94 / A` | Good decision-surface discipline | Prompt/routing surface is broad and could use more negative controls over time | Body is compact enough for current use | Healthy refs/scripts; incremental pattern work only | `Tune` | `+2 to +4` | `no` |
| `release-pipeline-architect` | `84 / B` | Release semantics are strong, but rollout/provenance failure guidance needs references | Needs a clearer front-end gate to reject CI tuning, deploy debugging, and infra asks | Core body is already concise and should stay that way | Strong single-file contract, weak supporting structure and eval coverage | `Plan` | `+9` | `yes` |
| `research` | `100 / A` | Strong verification discipline and failure handling | Rich dispatch and wave model are already coherent | Large body is justified and well-structured | Mature refs/scripts/templates/hooks/state surfaces already support complexity | `Maintain` | `+0 to +2` | `no` |
| `schema-evolution-planner` | `83 / B` | Migration logic is strong, but backfill/cutover failure patterns need support material | Needs a front-end gate for fresh schema design, DBA work, and rollout-adjacent ambiguity | Main body is lean enough; references should absorb the growth | Thin single-file skill with no refs/evals for a nuanced migration domain | `Plan` | `+11` | `yes` |
| `security-scanner` | `98 / A` | Correctness and safety posture are strong | Mode surface is clear enough | Complexity is proportionate to domain breadth | Good refs/scripts/templates; no promoted plan needed | `Maintain` | `+0 to +2` | `no` |
| `shell-conventions` | `81 / B` | Operator contract is too terse for an auto-invoked conventions skill | Empty/help and `check` behavior are underspecified; redirection is thin | Over-compressed rather than over-long | No refs, evals, or progressive-disclosure surfaces; structurally the thinnest conventions skill | `Plan` | `+12` | `yes` |
| `shell-scripter` | `101 / A` | Strong correctness boundaries and domain fit | Dispatch is crisp and easy to route | Compact and well-scoped | Structurally mature with good refs/scripts | `Maintain` | `+0 to +1` | `no` |
| `simplify` | `98 / A` | Main risk is auto-apply overreach, not missing content | Snippet handling and ambiguous apply routing still need hardening | Clean body; only safety logic needs tightening | Strong ref-backed structure, but eval coverage should deepen on snippet/auto-apply edges | `Plan` | `+6` | `yes` |
| `skill-creator` | `98 / A` | Strong authority skill; main gap is enforcement rather than correctness | Dispatch is clear for single-skill work but repo-wide planning is still implicit | Already concise and well-structured | Structurally strongest of the lens skills; improvement is workflow expansion and stronger approval-gate evals | `Plan` | `+5` | `yes` |
| `tech-debt-analyzer` | `94 / A` | Good inventory/roadmap posture | Routing is broad but coherent | Complexity is justified | Good state/script/template support; no standalone plan justified | `Tune` | `+2 to +4` | `no` |
| `test-architect` | `98 / A` | Strong contract and low correctness risk | Prompt surface is clear enough | Body is concise relative to scope | Healthy refs/scripts/templates; only optional structural tuning remains | `Maintain` | `+0 to +2` | `no` |
| `wargame` | `100 / A` | Strong methodological rigor and bias handling | Rich routing is already well-supported | Large body is justified and supported by refs | Mature progressive disclosure and domain structure already exist | `Maintain` | `+0 to +2` | `no` |

## Promotion Outcome

Promoted to standalone-plan status, in approved order:

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

## Cross-Cutting Gaps

- Thin-surface B-grade skills cluster around the same pattern debt: no `references/`, no deeper eval inventory, and weak progressive disclosure for domain-heavy prompts.
- Several A-grade skills are not structurally weak, but still have narrow prompt-contract issues around empty/help behavior, ambiguous routing, or repeated preflight logic.
- The strongest skills consistently separate operator contract from deep detail through refs, scripts, templates, hooks, and state surfaces.
- The promoted 15 are the right next tranche because they either fall below `90`, have weak front-door routing, or govern how the rest of the repo gets improved.

## Promotion Rules Applied

- `Plan` if audit score is below `90`
- `Plan` if dispatch is missing, weak, or ambiguous
- `Plan` if progressive disclosure is missing on a complex skill
- `Plan` if prompt contract or eval coverage is weaker than the apparent surface area
- `Tune` for A-grade skills with narrow qualitative issues
- `Maintain` for strong A-grade skills with no meaningful four-lens concerns
