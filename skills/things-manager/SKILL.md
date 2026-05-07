---
name: things-manager
description: >-
  Use when managing Things 3 via SupaThings MCP: tasks, projects, tags,
  deadlines, Today, Upcoming, Inbox, GTD planning, reviews, triage, capture,
  cleanup, bulk updates. NOT for calendars, Gmail, other task managers,
  database edits, MCP server setup, secrets, or unconfirmed destructive/bulk writes.
argument-hint: "<workflow> [details]"
license: MIT
compatibility: "Requires macOS, Things 3, and the SupaThings MCP server launched with npx -y supathings-mcp."
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Things Manager

Safely manage Things 3 through the existing SupaThings MCP server. Treat Things data as private local personal data and all create/update/complete/cancel operations as write-capable.

## Dispatch

| $ARGUMENTS | Mode |
|------------|------|
| `intake <request>` | Intake |
| `capture <tasks>` | Quick Capture |
| `triage inbox` | Inbox Triage |
| `today` / `plan today` | Today Planning |
| `weekly review` | Weekly Review |
| `project <name or goal>` | Project Planning |
| `search <query>` / `audit <scope>` | Search And Audit |
| `cleanup <scope>` | Cleanup |
| `bulk <operation>` | Bulk Update With Approval |
| `report <scope>` / `read-only <scope>` | Read-Only Report |
| Natural language about Things tasks, GTD, reviews, planning, capture, or cleanup | Classify intent, then route |
| Empty | Ask which Things workflow the user wants and show the mode menu |

## Empty Args Handler

Ask: "Which Things workflow do you want?"

Offer these choices:

| Choice | Use When |
|--------|----------|
| Today plan | Plan a realistic day from Today and Upcoming |
| Inbox triage | Classify Inbox items and propose projects/tags/dates |
| Weekly review | Review Today, Upcoming, projects, Someday, and recent Logbook |
| Project planning | Turn a goal into a Things project and tasks |
| Search/audit | Find tasks, tags, areas, deadlines, or stale work |
| Capture tasks | Convert notes into Things todos |

## Classification Logic

Before using SupaThings tools, classify the request:

1. Decide whether the user's intent is read-only or write-capable.
2. Decide whether the target is a single item or a bulk item set.
3. Decide whether date, deadline, tag, project, area, title, or target item ambiguity blocks writes.
4. Decide whether the operation is destructive because it completes, cancels, or performs delete-like cleanup.
5. Route to the safest mode and ask clarifying questions before write tools when any write-blocking ambiguity remains.

| Dimension | Read-Only | Write-Capable |
|-----------|-----------|---------------|
| Intent | inspect, list, report, plan, review, search | create, update, schedule, deadline, tag, move, complete, cancel |
| Scope | single item or view | multiple items, project, area, tag, or bulk operation |
| Ambiguity | missing context is acceptable for a report | missing date, deadline, tag, project, area, title, or target item blocks writes |
| Risk | no mutation | complete, cancel, delete-like cleanup, or bulk edits require preview and explicit confirmation |

If write-capable intent is ambiguous, ask one concise clarification before writing. If the user asks for a read-only plan that could become edits, present recommendations first and ask whether to apply them.

| Classification Result | Mode |
|-----------------------|------|
| read-only personal planning | Read-Only Report or Today Planning |
| single clear capture | Quick Capture |
| multiple creates or updates | Bulk Update With Approval |
| completion, cancellation, or cleanup | Cleanup with destructive-write confirmation |
| unclear project, tag, date, deadline, or target item | Intake before write tools |

## Tool Use Guidance

Prefer SupaThings read tools before write tools:

| Need | Prefer |
|------|--------|
| Current workload | `things_get-today`, `things_get-upcoming`, `things_get-anytime`, `things_get-someday` |
| Inbox triage | `things_get-inbox` |
| Project/area/tag lookup | `things_get-projects`, `things_get-areas`, `things_get-tags` |
| Duplicate prevention | `things_search-todos`, `things_search-items`, `things_search-advanced` |
| Review/history | `things_get-logbook`, `things_get-recent` |
| Details for a target item | `things_show-item` |
| Creates | `things_add-todo`, `things_add-project` after preview when needed |
| Updates/completion/cancellation | `things_update-todo`, `things_update-project` after confirmation |

Use Logbook only for review/history workflows. Never edit Things' local database directly.

## Workflows

### Intake

1. Restate the requested Things workflow and classify it with the gate.
2. Identify required reads and whether any write approval will be needed.
3. Ask only for missing information that blocks the next safe step.

### Quick Capture

1. Preserve user wording for task titles unless cleanup is requested.
2. Parse optional notes, checklist items, tags, `when`, deadline, project, area, and heading.
3. Search first when a task sounds like it may already exist.
4. For one clear task, create it after explicit capture intent; for multiple tasks, show a Preview first.

### Inbox Triage

1. Read Inbox, projects, areas, and tags.
2. Group items as actionable, waiting, someday, reference-like, ambiguous, or duplicate candidates.
3. Ask for missing context before assigning unclear projects, tags, schedules, or deadlines.
4. Preview proposed updates, then apply only approved changes.

### Today Planning

1. Read Today and Upcoming.
2. Identify overdue, due-soon, time-sensitive, blocked, and overloaded work.
3. Propose a realistic plan with a short must-do list and deferrals.
4. Apply schedule/tag changes only after approval.

### Weekly Review

1. Inspect Today, Upcoming, Anytime, Someday, projects, and recent Logbook.
2. Identify stale projects, overloaded days, orphan tasks, missing next actions, ambiguous Someday items, and deadline risks.
3. Produce a grouped report with recommended next actions.
4. Convert recommendations into writes only after preview and confirmation.

### Project Planning

1. Clarify outcome, project name, area, deadline, and initial next actions.
2. Look up existing projects and areas before creating anything.
3. Preview the exact project, notes, headings, todos, and checklists.
4. Create or update the project only after approval.

### Search And Audit

1. Use the narrowest search or view for the question.
2. Summarize only necessary personal task details.
3. Return counts, patterns, risks, and recommended next actions.

### Cleanup

1. Search for stale, duplicate, completed, canceled, orphaned, or tag-specific items.
2. Present findings and proposed cleanup actions separately.
3. Never bulk-complete or bulk-cancel without explicit confirmation.

### Bulk Update With Approval

1. Read the target set and compute the exact affected items.
2. Show a Preview with exact creates, updates, completions, and cancellations.
3. Ask for explicit confirmation before calling write tools.
4. After applying, report changed, skipped, failed, and ambiguous items.

### Read-Only Report

1. Do not mutate Things.
2. Group findings by view, project, area, tag, deadline, or risk.
3. Include task counts and recommended next actions.

## Output Contracts

### Read-Only Reports

Include:

- Scope inspected
- Counts by group
- Highest-risk or highest-leverage findings
- Recommended next actions
- Privacy note if details were intentionally summarized

### Proposed Writes

Use this exact section title before any bulk or destructive write:

```markdown
## Preview

- Creates: ...
- Updates: ...
- Completions: ...
- Cancellations: ...
- Skips/ambiguity: ...
```

Then ask for confirmation. Do not write until the user approves.

### Completed Writes

Include:

- Changed items
- Skipped items and why
- Failed operations and next steps
- Remaining ambiguity

## Progressive Disclosure

- Read `references/safety.md` before write-capable, bulk, destructive, or privacy-sensitive workflows.
- Read `references/workflows.md` for detailed daily planning, weekly review, triage, project planning, multi-item capture, cleanup, and audit recipes.
- Do not load all references for simple read-only searches or single clear captures.

## Reference File Index

| File | Purpose | When to Read |
|------|---------|--------------|
| `references/safety.md` | Write-confirmation, duplicate-prevention, date/deadline, and privacy rules | Any write-capable, bulk, destructive, or privacy-sensitive operation |
| `references/workflows.md` | Detailed Things workflow recipes and output patterns | Planning, triage, review, project planning, capture, cleanup, or audits |

## Scope Boundaries

**IS for:** Things 3 tasks, todos, projects, areas, tags, checklists, schedules, deadlines, Today, Upcoming, Anytime, Someday, Inbox, Logbook, GTD workflows, reviews, planning, and cleanup through SupaThings MCP.

**NOT for:** generic calendar scheduling unless it becomes Things tasks, Gmail/email management, non-Things task managers, MCP server creation/configuration, direct local database edits, secret handling, or bypassing confirmation for destructive or bulk writes.

## Validation Contract

Run these before declaring changes to this skill complete:

```bash
uv run wagents validate
uv run wagents eval validate
uv run python skills/skill-creator/scripts/audit.py skills/things-manager/
uv run wagents package things-manager --dry-run
```

Completion criteria:

- All validations pass.
- Audit grade is A or any remaining gap is explicitly documented.
- Package dry-run reports `Portable: yes`.
- Smoke-check representative eval prompts for read-only planning, ambiguous deadlines, and bulk approval behavior.
- No docs generation is run by this skill; docs sync belongs to docs-steward.

## Critical Rules

1. Never mutate Things without explicit user intent.
2. For bulk creates, updates, completions, or cancellations, present a Preview and get confirmation first.
3. Require confirmation before completing, canceling, or delete-like cleanup, even if the target set seems obvious.
4. Do not infer deadlines from vague language; ask unless the user clearly states a deadline.
5. Distinguish `when` scheduling from `deadline` in every proposed write.
6. Preserve user wording for task titles unless the user asks for cleanup or rewriting.
7. Search before creating tasks that may already exist.
8. Use project, area, and tag lookup tools before assigning items to lists or tags.
9. Do not expose sensitive personal task details unless they are necessary for the requested workflow.
10. Never edit Things' local database directly; use only SupaThings MCP tools.
11. Do not create, install, or configure MCP servers; redirect SupaThings MCP setup requests to MCP tooling.

## Canonical Vocabulary

**Canonical terms** (use these exactly throughout):

- Modes: "Intake", "Quick Capture", "Inbox Triage", "Today Planning", "Weekly Review", "Project Planning", "Search And Audit", "Cleanup", "Bulk Update With Approval", "Read-Only Report"
- Date fields: `when` means Things schedule/start date; `deadline` means due date
- Risk labels: "read-only", "single-write", "bulk-write", "destructive-write"
