# AI UX Patterns

AI interfaces need control, state, provenance, and recovery. Decorative trust
signals are not enough.

## Pattern Checklist

| Pattern | Use When | Required Detail |
| --- | --- | --- |
| Wayfinder | User needs to know what the AI can do | Examples, templates, scope, limits |
| Tuner | Output quality depends on preferences | Visible controls, defaults, reset |
| Governor | User needs to constrain actions | Approval gates, permissions, reversible actions |
| Provenance | Output cites sources or data | Source list, timestamps, confidence/limits |
| Process status | Long-running generation | Current step, queued/running/done/error states |
| Review affordance | AI output affects real work | Diff, preview, undo, accept/reject |
| Memory indicator | Personalization or saved context exists | What was used, how to clear or edit it |

## Design Requirements

- Show what the system knows, what it is doing, and what it cannot verify.
- Put user control near the generated output it affects.
- Keep prompts and settings inspectable when they shape important results.
- Design error states for blocked tools, missing credentials, empty retrieval,
  rate limits, and partial output.
- Tie trust affordances to real behavior: citations, logs, diffs, provenance,
  or reproducible commands.

## Failure Modes

| Failure | User Impact | Design Response |
| --- | --- | --- |
| Hidden scope | User cannot tell what the AI can read or change. | Show active sources, permissions, and pending actions near the input or result. |
| Decorative trust | Badges or verified chips imply evidence that does not exist. | Bind trust labels to citations, logs, checks, reviewer state, or remove them. |
| Irreversible action | User cannot preview or undo an AI-proposed change. | Add review, diff, confirmation, undo, and recovery paths proportional to risk. |
| Tool opacity | Long waits or tool calls appear as generic loading. | Show bounded progress, safe tool labels, retry states, and blockers. |
| Citation theater | Citations exist but do not support the claim. | Make citation targets inspectable and design for claim-source comparison. |
| Prompt trap | User has to rewrite the whole prompt to steer results. | Provide tuners, constraints, examples, and scoped follow-up controls. |

## Proof Checklist

- The UI exposes thinking, tool use, partial completion, failure, and blocked
  permission states.
- Citations, badges, confidence, or provenance displays map to actual system
  data.
- Destructive or external actions have preview, confirmation, and recovery
  paths.
- Keyboard users can reach inputs, tuners, citations, result actions, and
  stop/retry controls in a sensible order.
- Empty, long-running, error, no-source, and low-confidence states have real
  content, not placeholders.

## Handoffs

Route model evaluation, prompt benchmarking, backend tool safety, or policy
design to the relevant evaluation/security/API workflow. `/design` owns the
user-facing interface, controls, provenance displays, and rendered proof.

## Avoid

- Claiming confidence without evidence.
- Hiding tool calls or irreversible actions behind a single "generate" button.
- Making prompt boxes the entire interface for repeated workflows.
- Showing decorative "thinking" when actionable progress is available.
