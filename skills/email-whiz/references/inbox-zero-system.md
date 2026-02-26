# Inbox Zero System

> Structured daily and weekly routines for achieving and maintaining inbox zero. Includes progress tracking, habit building, and bankruptcy recovery protocols.

## Overview

Inbox zero is a habit, not a one-time event. This system provides:
- **Daily routine** (5 min): Quick triage to keep inbox clear
- **Weekly review** (15 min): Deeper maintenance and filter optimization
- **Progress tracking**: Streak and backlog trend monitoring
- **Bankruptcy recovery**: Staged approach when inbox is beyond control

---

## Daily Routine (5 min)

Run at a consistent time (morning recommended).

### Step 1: Quick Scan (1 min)
```
Search: is:unread newer_than:1d
Goal: identify anything requiring same-day action
Action: star P0/P1, skip the rest
```

### Step 2: Triage Unread (2 min)
Apply 4D+N to everything unread:
- DO: flag with INBOX/star, leave in inbox
- DELEGATE: add to forward list (batch after)
- DEFER: apply label `_deferred`, archive
- REFERENCE: archive immediately
- NOISE: archive or delete (batch via `gmail_batch_modify_emails`)

### Step 3: Batch Operations (2 min)
```
1. Archive all NOISE in batch
2. Apply DEFER labels in batch
3. Forward DELEGATE items
4. Inbox should contain only DO items
```

### Target State
```
Inbox = only emails requiring action from you today
Unread count = 0 or close to it
Time spent < 5 minutes
```

---

## Weekly Review (15 min)

Run once per week (Friday afternoon or Monday morning).

### Step 1: Clear Deferred (5 min)
```
Search: label:_deferred older_than:7d
For each: act, re-defer with date, or archive
Search: label:_waiting older_than:14d
For each: follow up or archive
```

### Step 2: Filter Effectiveness (5 min)
```
Check inbox for recurring noise → add to filters
Check _deferred label → anything that should be filtered?
Check top 5 senders by volume → any new filter candidates?
```

### Step 3: Newsletter Review (3 min)
```
Search: label:_reading/newsletters is:unread older_than:14d
Action: read or unsubscribe (unread older_than:14d = not interested)
```

### Step 4: Inbox State Check (2 min)
```
If inbox empty → log streak + 1
If inbox has items → address or consciously defer
Update progress tracking
```

---

## Progress Tracking

Store progress at `~/.claude/email-whiz/inbox-zero-progress.json`.

### Schema

```json
{
  "current_streak": 0,
  "longest_streak": 0,
  "last_zero_date": null,
  "history": [
    {
      "date": "YYYY-MM-DD",
      "inbox_count": 0,
      "unread_count": 0,
      "achieved_zero": false
    }
  ],
  "weekly_reviews": [
    {
      "week": "YYYY-WNN",
      "completed": false,
      "filters_added": 0,
      "unsubscribed": 0
    }
  ]
}
```

### Streak Rules
- Streak increments when inbox count reaches 0 at daily check
- Streak resets to 0 if 2+ days pass without a check
- Longest streak preserved across resets
- Weekly review completion tracked separately

### Reporting
When reporting progress, show:
```
INBOX ZERO PROGRESS

Streak: {current} days (best: {longest})
Last zero: {last_zero_date}
This week: {weekly_review_status}

Trend: {chart of last 7 days inbox counts}
Day  | Count
Mon  | 0  v
Tue  | 3
Wed  | 0  v
...
```

---

## Bankruptcy Detection

Trigger staged recovery when:
- Inbox unread > 500, OR
- Inbox count growing for 3+ consecutive days, OR
- User reports feeling overwhelmed

### Assessment Query
```
Search: is:unread
Count: {total unread}

Search: is:unread newer_than:7d
Count: {recent unread}

If recent / total > 0.8: inbox is active but overwhelming → Daily Blitz
If recent / total < 0.3: backlog problem → Staged Approach
```

### Option 1: Daily Blitz (for active overwhelm)
```
Day 1: Process only newer_than:1d
Day 2: Process only newer_than:2d
...continue until cleared
```

### Option 2: Staged Approach (for deep backlog)
```
Week 1: Archive all is:unread older_than:30d (with confirmation)
Week 2: Archive all is:unread older_than:14d
Week 3: Archive all is:unread older_than:7d
Week 4: Normal daily routine
```

### Option 3: Nuclear Reset (for 1000+ unread)
```
Step 1: Rescue critical emails:
  - is:unread is:important newer_than:7d → Review
  - is:unread from:{VIP_LIST} → Review

Step 2: Archive everything else (with explicit confirmation):
  - is:unread older_than:7d → Archive all (batch)

Step 3: Fresh start:
  - Set up daily routine
  - Create basic filters
  - Commit to 5-min daily check
```

> **Always confirm** before batch archiving. Show sample emails and total count.

---

## Graduation Protocol

After 21 consecutive days at inbox zero, suggest moving to a weekly-only routine: increase batch processing tolerance and shift focus to filter optimization over daily triage.

After 30 days without a bankruptcy trigger, the inbox system is stable — recommend a quarterly audit instead of monthly.

---

## Common Failure Modes

| Failure | Detection | Fix |
|---------|-----------|-----|
| Inbox zero obsession | >30min/day spent | Batch to 2x weekly |
| Defer pile growing | `label:_deferred` > 50 | Weekly review + ruthless archive |
| Filter explosion | >200 filters | Consolidate with OR operators |
| Newsletter creep | >50% inbox = newsletters | Run newsletter audit |
| Reply backlog | `is:starred` > 20 | Priority triage session |
