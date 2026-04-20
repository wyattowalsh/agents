---
name: orchestrator
description: >-
  Review and orchestrate parallel execution via subagent waves, teams, and
  pipelines. Use when 2+ independent actions need coordination. NOT for
  single-action tasks.
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Orchestration: Subagents, Agent Teams & Parallel Execution

These rules govern ALL parallelization decisions. Apply them on every task.

Not for single-action requests, simple file edits, or sequential-only workflows.

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| *(empty)* | Show the empty/help gallery, then apply the Classification Gate and Decomposition Gate to the current request |
| `pattern <A-F>` | Show the named pattern from `references/patterns.md` |
| `tier` | Display Tier Selection table and model guidance |
| `recovery` | Show the Accounting Rule and Recovery Ladder |

## Canonical Vocabulary

| Canonical Term | Meaning |
|----------------|---------|
| **subagent** | A Task-tool-spawned agent running in parallel within a session |
| **wave** | A batch of parallel subagents dispatched in a single message |
| **team** | A TeamCreate-spawned group of teammates coordinated by a lead |
| **teammate** | A member of an agent team with assigned file ownership |
| **lead** | The orchestrating agent in a team; never implements directly |
| **dispatch** | Send one or more subagents/teammates to execute in parallel |
| **gate** | A mandatory checkpoint that must pass before proceeding |
| **accounting rule** | N dispatched = N resolved; no agent silently dropped |

## Gating Logic

Use this gate before loading the full orchestration doctrine:

1. If the request has exactly one action, stay in a single session and do not invoke this skill.
2. If the work has multiple steps but they all edit the same file or depend on strict sequencing, do not force parallelism; keep the sequential constraint explicit.
3. If decomposition is unclear, run an explore-first pass and then re-enter the gate instead of guessing the topology.
4. If another active skill has a stricter phase order or dispatch precondition, preserve that skill's control flow and parallelize only inside its allowed boundaries.
5. If the user explicitly requests a specific execution approach, honor it unless it conflicts with a hard safety constraint.

## Operator Contract

### Empty / Help

1. Show the public entry paths: empty/help, `pattern <A-F>`, `tier`, and `recovery`.
2. Run the Classification Gate before applying the Decomposition Gate.
3. Explain the near-miss cases where this skill should not take over: single-action work, same-file sequential work, and phase-gated skills with stricter ordering.
4. Point to the specific references needed for pattern selection, progress accounting, runtime limits, and misroute examples instead of pasting the entire doctrine.

### `pattern <A-F>`

1. Load `references/patterns.md`.
2. Present the named pattern, when to use it, when not to use it, and the recovery implications.
3. Keep Pattern E as the default unless the named pattern is the clear better fit for the actual request.

### `tier`

1. Load `references/runtime-capability-boundaries.md` before discussing mechanism limits or environment-specific tooling constraints.
2. Show the Tier Selection table and explain why the highest applicable tier wins.
3. Name the near-miss cases where a lower tier is still correct, such as exactly one action or a single-domain, no-coordination task.

### `recovery`

1. Load `references/progress-accounting.md`.
2. Present the Accounting Rule, recovery ladder, and reporting contract.
3. Explain how to handle missing agents, re-spawns, and explicit skips before advancing to the next wave.

## 0. Decomposition Gate (MANDATORY before any work)

Before executing any request that involves tool-mediated work:

1. **DECOMPOSE**: List the actions needed (file reads, edits, searches, commands, analyses).
2. **CLASSIFY**: Which actions are independent (no data dependency)? Which are dependent?
3. **MAXIMIZE**: Actively split actions further — find every opportunity to parallelize. Each independent action = its own subagent. Challenge: can any action be split into two?
4. **CONFLICT CHECK**: Two independent actions editing the same file → make those sequential; all others remain parallel.
5. **DISPATCH**: Default is Pattern E — TeamCreate with nested subagent waves per teammate. Pre-approve permissions before spawning. Use bare subagent waves only when single domain, no coordination, no context pressure. Single session only when there is literally 1 action.
6. **TRACK**: For orchestrated work, create TaskCreate entries before dispatch (see Section 7).

**Fast path**: Single-action requests skip directly to single session.

**Explore-first path**: Cannot decompose without exploration → spawn parallel exploration team first (Pattern F Wave 1), then re-enter this gate.

**Transition heuristic**: Subagent waves hitting context limits or agents need to share findings → upgrade to Pattern E (teams + nested waves).

**User override**: Explicit user requests for a specific execution approach take precedence.

### Common rationalizations (all invalid)
- "It's faster to do it myself" — Parallel subagents complete N tasks in time of the slowest 1.
- "The task is too simple" — If it has 2+ independent actions, parallelize them.
- "I'll just do this one thing first" — Decompose BEFORE doing anything.

### Mode constraints
- **Plan mode**: Read-only subagents only. No teams, no write-capable agents.
- **Implementation mode**: All tiers available. Default to highest applicable tier.
- **Delegate mode**: Lead orchestrates only. All implementation via teammates/subagents.

### Skill integration
When a superpowers skill is active, the gate operates WITHIN the skill's execution structure:
- **Phase-gated skills**: Parallelize within each phase. Do not parallelize across phase boundaries.
- **Per-task review loop skills**: The skill's sequential structure takes precedence. Parallelize exploration within each task, not across tasks.
- **Dispatch-precondition skills**: The skill's "Don't use when" conditions remain valid. The gate does not override skill-level safety guards.

See `references/misroute-examples.md` for concrete near-miss cases such as same-file sequential edits, phase-gated review loops, and single-action requests.

---

## 1. Tier Selection (mandatory — highest applicable tier wins)

| Tier | Mechanism | Use when | Model |
|------|-----------|----------|-------|
| **Team + nested waves (Pattern E)** | TeamCreate + subagent waves per teammate — up to ~50 agents total | 2+ independent streams — THE DEFAULT | opus (default) / Copilot: Opus 4.6 max thinking; Sonnet 4.6 max thinking only for extremely trivial `/fleet` work |
| **Subagent wave** | Task tool, parallel calls | 2+ independent actions in one domain, no coordination pressure, and no same-file linear chain | opus (default) / Copilot: Opus 4.6 max thinking; Sonnet 4.6 max thinking only for extremely trivial `/fleet` work |
| **Single session** | Direct execution | Exactly 1 action, or any same-file sequential chain that must remain linear | N/A |

Select the highest tier whose criteria are met. Never select a lower tier to
reduce cost. A count of 2 is not enough on its own; the actions must be
independent.

## Scaling Strategy

| Situation | Recommended shape |
|-----------|-------------------|
| Small multi-action task in one domain | Use a subagent wave only if there are 2+ truly independent actions and no coordination pressure. |
| Cross-domain implementation | Use Pattern E with distinct ownership lanes and nested waves only where verbose work benefits from delegation. |
| Explore → implement → verify work | Use a multi-wave pipeline and close accounting between waves before advancing. |
| Same-file or tightly ordered work | Keep the sequential boundary explicit instead of manufacturing parallelism. |

---

## 2. Subagent Best Practices

### Spawning
- **One response, multiple Task calls.** All independent subagents MUST be dispatched in the same message.
- Use `run_in_background: true` for subagents whose results are not needed immediately.
- N independent actions = N parallel subagents. Merge only when they share file/directory scope.

### Prompt-tuning
- Give every subagent a detailed, self-contained prompt with exact file paths, expected output format, and domain context.
- Do NOT rely on the subagent inheriting conversation history — it does not.

### Model selection
- Default policy: `opus` for every subagent, teammate, and wave.
- GitHub Copilot CLI override: all plans should be `/fleet`-optimized per `/orchestrator`. For `/fleet`, use **Claude Opus 4.6 with max thinking** for every non-trivial subagent, teammate, wave, and `/fleet` member.
- Use **Claude Sonnet 4.6 with max thinking** only for incredibly/extremely trivial `/fleet` subagents. If there is any ambiguity, escalate to Opus.
- When both policies are present, apply the environment-specific override for the active runtime.

### Context management
- Delegate verbose operations (test suites, log parsing, doc fetching) to subagents.
- Use subagent resumption (agent ID) for multi-phase work rather than spawning fresh.
- After a wave completes, apply the Accounting Rule (Section 4) before
  synthesizing or dispatching the next wave.

---

## 3. Agent Team Best Practices

- Scale teammates to match the work — no artificial cap. Use as many as needed for maximum parallelism (up to ~50 agents total including nested subagents). Token budget is not a constraint.
- Pre-approve common permissions before spawning teammates to reduce friction.
- Assign each teammate a distinct domain and non-overlapping file ownership.
- Assign as many tasks per teammate as the domain requires — no artificial limit.
- Include all task-specific context in spawn prompts: file paths, architecture decisions, acceptance criteria. Teammates do not inherit conversation history.
- Use delegate mode to prevent the lead from implementing work itself.
- Task claiming uses file locking — no race conditions when multiple teammates claim simultaneously.
- Never assign two teammates overlapping file ownership.
- The lead must not proceed to synthesis until all teammate tasks are accounted for (Section 4).

---

## 4. Quality Gates & Failure Recovery

### The Accounting Rule (MANDATORY after every parallel dispatch)

When N agents are dispatched, all N must be accounted for before proceeding:

1. **COLLECT**: Wait for all N agents to return. Poll with `TaskOutput` block=false for timeout detection.
2. **TALLY**: Results received vs dispatched. Missing = unresolved.
3. **RESOLVE** all non-successes via the Recovery Ladder (see `references/patterns.md`).
4. **GATE**: Do NOT advance until every agent has SUCCESS or explicit SKIP.
5. **REPORT**: Summarize all agent outcomes via TaskUpdate before proceeding.

### Hooks for automated enforcement
- **TeammateIdle** hook: prevent teammates from idling before work is verified.
- **TaskCompleted** hook: prevent tasks from closing before tests pass.
- Both use exit code 2 to send feedback and keep the teammate/task active.

### Plan approval workflow
- For risky changes, include "Require plan approval before making changes" in the spawn prompt.
- Teammate enters read-only plan mode, sends plan_approval_request to lead when ready.
- Lead approves or rejects with feedback. Teammate revises if rejected.
- Influence approval criteria in spawn prompt: "only approve plans that include test coverage."

---

## 5. Orchestration Patterns

| Pattern | Name | Use When | Details |
|---------|------|----------|---------|
| A | Parallel subagent wave | 2+ independent subtasks in a session | see `references/patterns.md` |
| B | Agent team with file ownership | Cross-domain features, large refactors | see `references/patterns.md` |
| C | Competing hypotheses | Debugging, architecture decisions | see `references/patterns.md` |
| D | Plan-then-swarm | Large tasks needing human approval | see `references/patterns.md` |
| **E** | **Teams of subagent-using teammates (DEFAULT)** | **2+ independent streams — use by default** | see `references/patterns.md` |
| F | Multi-wave pipeline | Explore → implement → verify phases | see `references/patterns.md` |

---

## 6. Limitations

- No session resumption for teammates (`/resume` and `/rewind` won't restore them).
- No nested teams (teammates can use subagents but cannot spawn teams).
- One team per session. Clean up before starting a new one.
- Lead is fixed — cannot transfer leadership.
- All teammates inherit the lead's permission mode at spawn.
- Subagent resumption may not recover from all failure modes (re-spawn instead).
- No built-in timeout detection — orchestrator must poll with `TaskOutput` manually.
- Recovery re-spawns count toward the session's agent budget.
- Display modes: in-process (Shift+Down to cycle) is default; split panes require tmux or iTerm2.
- Teammate interaction: Enter to view session, Escape to interrupt, Ctrl+T for task list.

## Progressive Disclosure

- Do not load every orchestration detail by default.
- Read `references/classification-gate.md` when deciding whether this skill should own the task at all.
- Read `references/patterns.md` only when the user requests a specific pattern or the topology choice is the main question.
- Read `references/progress-accounting.md` when discussing reporting, accounting, or recovery behavior.
- Read `references/runtime-capability-boundaries.md` when tool/runtime limits or environment-specific constraints affect the topology.
- Read `references/misroute-examples.md` when a request is close to the trigger boundary.

---

## Critical Rules

1. Never dispatch independent actions sequentially — all independent Task calls MUST appear in one response.
2. Always run the Decomposition Gate before any tool-mediated work; skipping it is never acceptable.
3. Never reduce parallelism or tier when the higher tier criteria are met; follow the documented environment-specific model policy.
4. Never silently drop a failed subagent — N dispatched = N accounted for; apply the Accounting Rule after every wave.
5. Never advance to Wave N+1 with unresolved agents — resolve all agents in Wave N first.
6. Always create TaskCreate entries before dispatching subagent waves or agent teams — silent orchestration is forbidden.
7. Never assign two teammates overlapping file ownership — overlapping edits cause lost work.
8. Always include full context in subagent and teammate prompts — they do not inherit conversation history.

---

## Reference File Index

| File | Content | Read When |
|------|---------|-----------|
| `references/classification-gate.md` | Invocation gate, near-miss rules, and ask-first logic before orchestration starts | Deciding whether to invoke the skill |
| `references/patterns.md` | Detailed patterns A-F with ASCII diagrams, key rules, recovery ladder | Designing parallel execution or selecting a pattern |
| `references/progress-accounting.md` | Progress tracking contract, Accounting Rule details, and recovery/reporting expectations | Explaining recovery, accounting, or reporting |
| `references/runtime-capability-boundaries.md` | Tier and runtime boundary guidance, including when tool or environment limits constrain the topology | Choosing a tier or discussing environment limits |
| `references/misroute-examples.md` | Concrete false-trigger and near-miss scenarios | Checking borderline requests |

---

## 7. Progress Visibility (MANDATORY for orchestrated work)

All orchestrated work must produce structured progress indicators via TaskCreate/TaskUpdate.

| Tier | Requirement | Granularity |
|------|------------|-------------|
| **Subagent wave** | MUST | One task per subagent, created before dispatch |
| **Agent team** | MUST | One task per teammate assignment, created during setup |
| **Single session** (3+ steps) | SHOULD | One task per logical step |

### Rules
- Create tasks before execution begins, not retroactively.
- Each task MUST have a descriptive `activeForm` in present continuous tense naming the specific action and target.
- Update tasks to `in_progress` before starting, `completed` immediately after.
- After wave completion + accounting, summarize all agent outcomes before dispatching the next wave.

## Scope Boundaries

**IS for:** decomposition, orchestration topology, pattern selection, progress accounting, recovery/reporting, and multi-agent execution rules.

**NOT for:** single-action requests, same-file sequential work that should stay serialized, or overriding stricter phase-gated skill contracts.
