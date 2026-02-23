# Orchestration Patterns A-F

Detailed pattern descriptions for parallel execution, agent teams, and multi-wave pipelines.

---

## Pattern A: Parallel Subagent Wave (most common)

For 2-6 independent subtasks within a single session:

```
[Main session]
  ├── Subagent 1 (research module A) ──► summary
  ├── Subagent 2 (research module B) ──► summary
  ├── Subagent 3 (run test suite)    ──► results
  └── Subagent 4 (fetch docs)        ──► context
Main synthesizes all results, continues work.
```

**When to use**: 2-6 independent actions identified by the Decomposition Gate, no inter-agent communication needed.

**Key rules**:
- All independent subagents MUST be dispatched in the same message.
- Use `run_in_background: true` for subagents whose results are not needed immediately.
- Give every subagent a detailed, self-contained prompt with exact file paths, expected output format, and domain context.
- Do NOT rely on the subagent inheriting your conversation history — it does not.

---

## Pattern B: Agent Team with File Ownership

For cross-domain features or large refactors:

```
[Lead: orchestrate only, delegate mode]
  ├── Backend teammate   (owns src/api/, src/db/)
  ├── Frontend teammate  (owns src/components/, src/styles/)
  ├── Testing teammate   (owns tests/)
  └── Reviewer teammate  (read-only, reviews all PRs)
```

**When to use**: 3+ domain-crossing streams, coordination needed, distinct file ownership possible.

**Key rules**:
- Start with 2-4 teammates. Scale up only when justified.
- Assign each teammate a distinct domain and non-overlapping file ownership.
- Aim for 5-6 tasks per teammate — enough to stay productive, small enough for check-ins.
- Tasks should be self-contained units producing a clear deliverable.
- Use delegate mode (Shift+Tab) to prevent the lead from implementing work itself.

---

## Pattern C: Competing Hypotheses

For debugging or architecture decisions:

```
[Lead: synthesize]
  ├── Hypothesis A teammate (investigate theory A)
  ├── Hypothesis B teammate (investigate theory B)
  ├── Hypothesis C teammate (investigate theory C)
  └── Devil's advocate teammate (challenge all theories)
Teammates message each other to debate. Lead synthesizes consensus.
```

**When to use**: Multiple plausible explanations or approaches, need systematic comparison.

**Key rules**:
- Each hypothesis teammate investigates independently.
- Devil's advocate teammate challenges all theories — prevents groupthink.
- Lead synthesizes consensus from teammate findings.
- Teammates can message each other to debate findings.

---

## Pattern D: Plan-then-Swarm

For maximum directed execution on large tasks:

```
1. Plan mode: generate detailed implementation plan (low-context, fast)
2. Human review and approval
3. Spawn agent team to execute the approved plan (well-directed)
```

**When to use**: Large tasks where undirected execution risks wasted effort. Human approval adds safety.

**Key rules**:
- Plan phase uses plan mode — read-only, low-context.
- Human must approve the plan before spawning the execution team.
- Execution team receives the full approved plan as context.
- Use plan approval for risky changes: "Require plan approval before they make any changes."

---

## Pattern E: Teams of Subagent-Using Teammates

For maximum throughput on very large tasks:

```
[Lead: orchestrate]
  ├── Backend teammate
  │     ├── Subagent: run backend tests
  │     └── Subagent: fetch API docs
  ├── Frontend teammate
  │     ├── Subagent: explore component tree
  │     └── Subagent: run visual regression
  └── Testing teammate
        └── Subagent: run full integration suite
```

**When to use**: Very large tasks where teammates themselves need parallelism. Teammates can spawn subagents but NOT nested teams.

**Key rules**:
- Teammates CAN use subagents for verbose operations (tests, logs, doc fetches).
- Teammates CANNOT spawn their own teams — no nested teams.
- Delegate verbose ops to subagents within teammates to keep teammate context lean.
- Lead orchestrates teammates; teammates orchestrate their own subagents.

---

## Pattern F: Multi-Wave Pipeline (phased parallel execution)

For tasks requiring explore, implement, and verify phases:

```
Wave 1 (explore): parallel subagents gather context
  ├── Subagent: explore module A
  ├── Subagent: explore module B
  └── Subagent: fetch docs/deps
Main synthesizes findings → builds implementation context for Wave 2.

Wave 2 (implement): parallel subagents execute changes (NO file overlap)
  ├── Subagent: implement change in module A
  ├── Subagent: implement change in module B
  └── Subagent: update configs
Main verifies no conflicts → builds verification plan for Wave 3.

Wave 3 (verify): parallel subagents test and review
  ├── Subagent: run test suite A
  ├── Subagent: run test suite B
  └── Subagent: lint + type check
Main synthesizes final result.
```

**When to use**: Tasks with natural explore → implement → verify phases. Also used as the explore-first path when the Decomposition Gate cannot decompose without exploration.

**Key rules**:
- Between waves (MANDATORY): Read ALL results. Apply the Accounting Rule — recover any unresolved agents before proceeding.
- Resolve contradictions, include synthesized context (including recovery outcomes) in next-wave prompts.
- Do NOT dispatch Wave N+1 until Wave N has zero unresolved agents.
- If >50% of a wave fails, re-examine the wave's premise before re-dispatching.
- Update task statuses and summarize outcomes as part of the inter-wave protocol.

---

## Recovery Ladder

Execute in order for each failed or timed-out agent:

| Step | Action | When |
|------|--------|------|
| 1. Resume | Resume via agent ID with original prompt + error context + partial results | Partial result or recoverable error (subagents only — teammates cannot be resumed) |
| 2. Re-spawn | New agent with same prompt + error context + partial results | Resume failed, timed out, or is a teammate |
| 3. Re-assign | Assign task to a different teammate or subagent | Same agent fails twice on the same task |
| 4. Escalate | Report to user: what was attempted, what failed, what remains incomplete | All automated recovery exhausted (max 2 attempts), or systemic issue |

**Skip criteria**: A failed agent's result may be skipped only if the task was read-only AND other agents' results fully cover the same information. Document every skip in synthesis. Never skip implementation, verification, or dependency tasks.

**Teammate-specific**: Teammates cannot be resumed — lead must re-assign via TaskUpdate with failure context. If a teammate idles without completing, message it to investigate before assuming failure.
