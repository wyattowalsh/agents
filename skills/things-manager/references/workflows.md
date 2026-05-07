# Things Manager Workflows

Use this reference for detailed Things planning, triage, review, capture, cleanup, and audit workflows.

## Contents

1. Daily Planning
2. Inbox Triage
3. Weekly Review
4. Project Planning
5. Quick Capture
6. Cleanup
7. Search And Audit

## Daily Planning

Read:

- `things_get-today`
- `things_get-upcoming`

Process:

1. Separate overdue, due today, scheduled today, and due-soon items.
2. Identify overloaded days and tasks without clear next actions.
3. Propose a realistic plan with no more than a small must-do set unless the user asks for an aggressive plan.
4. Separate recommendations from proposed writes.

Output groups:

- Must do today
- Should do today
- Waiting/blocked
- Candidate deferrals
- Deadline risks
- Optional proposed Things updates

## Inbox Triage

Read:

- `things_get-inbox`
- `things_get-projects`
- `things_get-areas`
- `things_get-tags`

Classify each Inbox item:

| Class | Action |
|-------|--------|
| actionable | assign project/area, optional tag, optional `when` |
| waiting | tag or note with dependency if available |
| someday | move/schedule to Someday only after approval |
| reference-like | ask whether to convert to task, note, or cancel |
| ambiguous | ask for missing outcome or context |
| duplicate candidate | search and propose merge/update/skip |

Preview updates before applying. Preserve task titles unless cleanup is requested.

## Weekly Review

Read:

- `things_get-today`
- `things_get-upcoming`
- `things_get-anytime`
- `things_get-someday`
- `things_get-projects`
- `things_get-logbook` with an appropriate recent period

Inspect:

- Overdue and due-soon tasks
- Stale projects with no next action
- Projects with too many active tasks
- Someday items that became relevant or obsolete
- Orphan tasks with no project/area when they should have one
- Recently completed work for momentum and follow-up gaps

Output:

- Workload summary
- Deadline risks
- Stale or blocked projects
- Missing next actions
- Suggested cleanup or planning actions

Do not apply updates during the review unless the user asks and confirms the Preview.

## Project Planning

Read first:

- `things_get-projects` to avoid duplicate projects
- `things_get-areas` for placement
- `things_get-tags` if tags are requested

Clarify when missing:

- Project outcome
- Area/list
- Deadline versus schedule
- First concrete next action

Preview:

- Project title
- Notes
- Area
- `when`
- Deadline
- Tags
- Initial todos and checklists

Create with `things_add-project` only after approval. If an existing project matches, ask whether to update it instead.

## Quick Capture

For one clear task:

1. Parse title, notes, checklist, `when`, deadline, tags, project, area, and heading.
2. Search if duplicate risk exists.
3. Create when the user's intent to capture into Things is explicit.

For multiple tasks:

1. Convert each line or bullet into one task unless the user asks for checklists.
2. Preserve wording.
3. Preview all creates.
4. Ask for confirmation.

Use checklists when a set of steps belongs inside one outcome rather than becoming separate commitments.

## Cleanup

Potential cleanup scopes:

- Duplicate tasks
- Stale Someday items
- Completed/canceled history review
- Tag cleanup
- Orphan tasks
- Projects with no next action
- Overloaded Today or Upcoming views

Always separate findings from actions. Bulk-complete, cancel, retag, or reschedule only after confirmation.

## Search And Audit

Use the narrowest tool:

| Question | Tool |
|----------|------|
| Find text | `things_search-todos` or `things_search-items` |
| Filter by status/date/tag/area/type | `things_search-advanced` |
| List by tag | `things_get-tagged-items` |
| Inspect a known item/list | `things_show-item` |
| Recent activity | `things_get-recent` or `things_get-logbook` |

Report counts, patterns, and recommended next actions. Avoid dumping unrelated personal task data.
