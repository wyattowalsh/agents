# Things Manager Safety

Use this reference for write-capable, bulk, destructive, or privacy-sensitive Things workflows.

## Contents

1. Write Confirmation
2. Dates And Deadlines
3. Duplicate Prevention
4. Privacy Handling
5. Destructive Operations

## Write Confirmation

Classify every operation before tool use:

| Risk | Examples | Requirement |
|------|----------|-------------|
| read-only | search, list, report, review | No confirmation needed |
| single-write | create one clearly requested task | Explicit user write intent is enough |
| bulk-write | create/update multiple tasks or project contents | Preview plus confirmation |
| destructive-write | complete, cancel, delete-like cleanup, remove schedule/deadline from many items | Preview plus confirmation |

Preview exact mutations before bulk or destructive writes:

- Item title or project name
- Operation type
- Target `when`, deadline, tags, project, area, notes, or checklist changes
- Reason for the change
- Items skipped because of ambiguity or duplicate risk

Do not treat silence, vague approval, or prior general intent as confirmation. Ask a direct yes/no confirmation question.

## Dates And Deadlines

Things has two distinct concepts:

| Field | Meaning | Ask When |
|-------|---------|----------|
| `when` | Schedule/start date or list placement such as today, tomorrow, anytime, someday, or YYYY-MM-DD | The user says "do this", "plan this", or "put this on my list" without a date |
| `deadline` | Due date with consequence if missed | The user uses vague urgency like "soon", "ASAP", "important", or "next" without a clear due date |

Only set a deadline when the user clearly states one: "due Friday", "deadline May 12", "must be done by tomorrow". If a phrase could mean schedule rather than deadline, ask.

## Duplicate Prevention

Search before creating when any of these are true:

- The task title resembles an existing commitment or project name
- The user says "remind me again", "add another", "make sure", or "do we have"
- Creating from a meeting note, long note, or imported list
- The write is part of a bulk capture

If duplicates are found, present options: update existing, create separate task, skip, or merge into checklist.

## Privacy Handling

Things can contain sensitive personal data. Minimize exposure:

- Summarize patterns instead of listing every personal detail when a count or category is enough.
- Avoid quoting private notes unless needed for disambiguation.
- Do not include unrelated tasks in reports.
- Do not export or persist Things data outside the active response unless explicitly requested.
- Do not search secrets, credentials, or private files as part of task management.

## Destructive Operations

Completion and cancellation are write operations with historical consequences. Treat them as destructive when done in bulk or during cleanup.

Before completing or canceling items:

1. Confirm the exact target set.
2. Show the Preview.
3. Ask for confirmation.
4. Apply only approved changes.
5. Report changed, skipped, failed, and ambiguous items.

Never directly edit the Things database. Use SupaThings MCP tools only.
