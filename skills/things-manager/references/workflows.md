# Things Manager Workflows

Use this reference for detailed Things planning, triage, review, capture, project structuring, task placement, cleanup, UI handoff, and audit workflows.

## Contents

1. Daily Planning
2. Inbox Triage
3. Weekly Review
4. Project Planning
5. Project Structuring
6. Task Placement
7. Tag Taxonomy Audit
8. Deadline And Reminder Review
9. Quick Capture
10. Quick Entry And UI Handoff
11. Cleanup
12. Search And Audit

## SupaThings Read Strategy

Default to compact reads with explicit limits when a tool supports `detail` or `limit`. Escalate to full detail only for selected items whose notes, checklist, or exact fields are needed for disambiguation or a write preview.

Useful advanced tools:

| Need | Tool |
|------|------|
| Health check | `things_app-status`, `things_version` |
| Project structure | `things_get-project-structure` |
| Project summary | `things_summarize-project` |
| Heading suggestions | `things_suggest-headings` |
| Heading validation | `things_validate-headings` |
| Task placement | `things_suggest-task-placement` |
| Structured new project | `things_create-project-with-headings` or `things_json` |
| UI handoff | `things_show`, `things_show-item`, `things_search`, `things_show-quick-entry` |

## Daily Planning

Read:

- `things_get-today` with compact detail
- `things_get-upcoming` with compact detail

Process:

1. Separate overdue, due today, scheduled today, This Evening/evening, reminders, and due-soon items.
2. Identify overloaded days and tasks without clear next actions.
3. Propose a realistic plan with no more than a small must-do set unless the user asks for an aggressive plan.
4. Separate recommendations from proposed writes.

Output groups:

- Must do today
- Should do today
- Waiting/blocked
- Candidate deferrals
- Deadline risks
- Reminder or evening placement risks
- Optional proposed Things updates

## Inbox Triage

Read:

- `things_get-inbox` with compact detail
- `things_get-projects` with compact detail
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

- `things_get-today` with compact detail
- `things_get-upcoming` with compact detail
- `things_get-anytime` with compact detail and limit
- `things_get-someday` with compact detail and limit
- `things_get-projects` with compact detail
- `things_get-logbook` with an appropriate recent period and compact detail

Inspect:

- Overdue and due-soon tasks
- Stale projects with no next action
- Projects whose headings do not match current work phases
- Projects with too many active tasks
- Tag taxonomy drift, including inherited area/project tags
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
- `things_suggest-headings` for complex new projects

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
- Heading structure when the project is complex

For a simple project, create with `things_add-project` only after approval. For a brand-new structured project, prefer `things_create-project-with-headings`; use `things_json` only when raw structured payload control is necessary and the full payload has been previewed. If an existing project matches, ask whether to update it instead.

## Project Structuring

Use when the user wants to organize, refactor, or plan a complex project.

New project flow:

1. Look for duplicate projects with `things_get-projects` or `things_search-items`.
2. Call `things_suggest-headings` with the project goal, work type, or methodology.
3. Preview headings, top-level todos, checklist items, `when`, deadline, tags, and area.
4. After confirmation, use `things_create-project-with-headings`.
5. Verify with `things_get-project-structure`.

Existing project flow:

1. Find the project and read `things_get-project-structure`.
2. Call `things_summarize-project` for a planning-focused summary.
3. Call `things_suggest-headings` to compare existing headings with a Things-native structure.
4. Call `things_validate-headings` before placing tasks under headings.
5. If headings are missing, explain that existing-project heading creation may require manual creation in Things before automated placement can continue.
6. Do not claim that missing headings were created unless a SupaThings write result confirms it.

## Task Placement

Use when tasks need to be added or moved into project headings.

1. Resolve the project with a narrow search or project lookup.
2. Read `things_get-project-structure`.
3. Run `things_suggest-task-placement` with the candidate task titles.
4. Preview every proposed create or move grouped by target heading.
5. Confirm the exact batch before `things_add-todo`, `things_update-todo`, or `things_update`.
6. After applying, report changed, skipped, failed, and ambiguous items.

If no suitable heading exists, propose a manual heading step or ask whether to place the task at project top level.

## Tag Taxonomy Audit

Read:

- `things_get-tags`
- `things_get-areas` with item context only when needed
- `things_get-projects` with compact detail
- `things_get-tagged-items` for suspicious or high-value tags
- `things_search-advanced` for combined filters

Inspect:

- Tags that represent context, person, energy, status, location, or priority
- Duplicate-like tags or inconsistent naming
- Area/project tags whose children inherit focus context
- Tags applied directly where inherited tags would be cleaner
- Important tags with no recent or active items

Output a read-only taxonomy report first. Propose retagging only as a separate Preview, and do not create missing tags unless a current SupaThings tool supports it and the user confirms.

## Deadline And Reminder Review

Read Today, Upcoming, advanced searches for deadlines, and relevant project structure.

Classify date fields:

| Field | Meaning |
|-------|---------|
| `when` | Things schedule/start date or list placement such as Today, Upcoming, Anytime, or Someday |
| evening | This Evening placement for work intended later today |
| reminder | Notification date/time tied to start/schedule intent |
| deadline | Due date with consequence if missed |

Review for:

- Overdue deadlines
- Due-soon work with no earlier start date
- Reminder-worthy tasks that are time-sensitive but not due dates
- Tasks scheduled too early or too late for the deadline
- Vague urgency that should not become a deadline without clarification

Preview schedule, evening, reminder, and deadline changes as separate fields.

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

## Quick Entry And UI Handoff

Use `things_show-quick-entry` when the user wants to manually review or edit capture in Things before saving. This is useful for sensitive notes, uncertain task titles, or capture from messy prose.

Use UI navigation instead of exposing private details when the user asks to open or inspect a target in Things:

| User Need | Tool |
|-----------|------|
| Open a known item | `things_show-item` |
| Open a list/project/tag by ID or query | `things_show` |
| Search visually in Things | `things_search` |

UI handoff is user-visible but usually non-mutating. Do not pair it with writes unless the user asked for edits and approved the Preview.

## Cleanup

Potential cleanup scopes:

- Duplicate tasks
- Stale Someday items
- Completed/canceled history review
- Logging completed items
- Trash review or emptying trash
- Tag cleanup
- Orphan tasks
- Projects with no next action
- Overloaded Today or Upcoming views

Always separate findings from actions. Bulk-complete, cancel, log completed items, empty trash, retag, or reschedule only after confirmation. Default cleanup to report-only first.

## Search And Audit

Use the narrowest tool:

| Question | Tool |
|----------|------|
| Find text | `things_search-todos` or `things_search-items` |
| Filter by status/date/tag/area/type | `things_search-advanced` |
| List by tag | `things_get-tagged-items` |
| Inspect structure | `things_get-project-structure` or `things_summarize-project` |
| Open a known item/list in Things | `things_show-item` or `things_show` |
| Recent activity | `things_get-recent` or `things_get-logbook` |

Report counts, patterns, and recommended next actions. Avoid dumping unrelated personal task data.
