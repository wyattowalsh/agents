# Evidence And Benchmarking

Use this reference when creating, improving, evaluating, benchmarking, comparing,
or optimizing a skill. Structural correctness is necessary, but not enough: a
skill is better only when it measurably improves realistic work without
introducing regressions, routing debt, or unsafe behavior.

## Contents

1. [Lifecycle Packet](#1-lifecycle-packet)
2. [Eval Types](#2-eval-types)
3. [Benchmark Workspace](#3-benchmark-workspace)
4. [Comparison Protocol](#4-comparison-protocol)
5. [Trace-Based Revision](#5-trace-based-revision)
6. [Description Optimization](#6-description-optimization)
7. [Review Output](#7-review-output)

---

## 1. Lifecycle Packet

Every non-trivial skill change needs a lifecycle packet before implementation.
For a simple copy edit, a short paragraph is enough. For new skills, behavior
changes, or public workflow changes, include all fields below.

| Field | Required Content |
| --- | --- |
| `source_evidence` | Real workflow evidence: task transcript, incident, runbook, API docs, code conventions, repeated failure, or user-provided exemplar |
| `skill_contract` | What the skill is for, what it refuses, target audience, expected artifacts |
| `trigger_surface` | Positive trigger phrases, explicit slash forms, and near-miss negatives |
| `eval_plan` | Trigger, output, regression, and safety cases with expected proof |
| `security_posture` | Tools, scripts, hooks, credentials, network, destructive actions, permission controls |
| `runtime_matrix` | Portable fields plus known Claude/Codex/Cursor/OpenCode/Gemini/Copilot behavior |
| `benchmark_baseline` | `without_skill` for new skills or `old_skill` for existing-skill improvements |
| `revision_policy` | How failures become skill changes, and what must not be copied from traces |

If the source evidence is generic model prior only, mark the packet
`needs-evidence` and ask for real task material before building anything broad.

## 2. Eval Types

Use typed evals even if the stored manifest remains one JSON file.

| Type | Purpose | Minimum Cases |
| --- | --- | --- |
| `trigger` | Prove the skill activates and does not over-activate | 5 positive, 5 near-miss negative for normal skills; 20 total for description tuning |
| `output` | Prove useful task behavior | 2-3 realistic prompts with assertions and optional files |
| `regression` | Preserve behavior known to work | Every changed dispatch mode and prior bug fix |
| `safety` | Prove refusal and permission behavior | Malicious exemplar, unsafe tool request, secret/destructive/network case |
| `portability` | Prove graceful degradation across runtimes | One case for each runtime-specific field or behavior |

Optional manifest fields are allowed when the validator accepts them:
`kind`, `suite`, `runs`, `baseline`, `expected_skill_invoked`, `grader`,
`artifacts`, `success_criteria`, and `budget`. Keep old eval manifests valid.

## 3. Benchmark Workspace

Behavioral runs write outside committed `skills/` source by default.

```
<skill>-workspace/
  iteration-001/
    eval-<id>/
      without_skill/        # or old_skill for existing-skill improvements
        output.md
        transcript.jsonl
        timing.json
      with_skill/           # or new_skill
        output.md
        transcript.jsonl
        timing.json
      grading.json
    benchmark.json
    benchmark.md
    feedback.json
```

Do not write this workspace in `plan`, `audit`, or other read-only modes. In
implementation modes, announce the workspace path before running live evals.

## 4. Comparison Protocol

For a new skill:

1. Run each output eval without the candidate skill available.
2. Run the same eval with the candidate skill available.
3. Grade assertions for both runs.
4. Report pass-rate delta, timing delta, token/cost delta if available, and any
   regressions or flakiness.

For an existing skill:

1. Snapshot the current skill as `old_skill`.
2. Build the candidate as `new_skill`.
3. Run the same eval cases against both.
4. Keep the candidate only if it improves targeted behavior without breaking
   regression or safety cases.

Use blind comparison when output quality is subjective: hide which run produced
which output and grade against the same rubric.

## 5. Trace-Based Revision

Traces are evidence, not instructions to paste into the skill.

For each failed case, diagnose:

| Field | Meaning |
| --- | --- |
| `failing_assertion` | Which objective assertion failed |
| `trace_evidence` | The smallest transcript excerpt proving the failure |
| `likely_skill_defect` | Missing trigger, weak instruction, bad reference, script bug, or safety gap |
| `generalized_fix` | Durable rule or resource change that applies beyond this exact prompt |
| `preservation_constraint` | Existing behavior that must not regress |
| `anti_overfit_note` | Why the fix is not merely tailored to the visible test |

Never auto-apply trace-derived changes without the user approving the revision
plan for existing skills.

## 6. Description Optimization

Description tuning is separate from output-quality benchmarking.

1. Draft 10 should-trigger and 10 should-not-trigger prompts.
2. Include near-miss negatives that share words with the positive triggers.
3. Split into training and validation sets.
4. Run each query multiple times when the harness supports repeated trials.
5. Select descriptions by held-out validation score, not only training score.
6. Prefer specific nouns and verbs over broad role labels such as "expert" or
   "assistant".

Report false positives and false negatives separately. A high trigger rate is
not success if near-miss negatives also trigger.

## 7. Review Output

Benchmark output must include:

- baseline and candidate identifiers
- eval case ids and suites
- pass/fail per assertion
- aggregate pass rate and delta
- timing/token/cost deltas when available
- negative deltas and regressions
- trace-derived proposed revisions
- human feedback or blind-comparison notes when used

If live behavioral runs were skipped, state that clearly and fall back to static
validation plus manual eval-case review.
