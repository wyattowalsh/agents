# Triage Framework

> Decision trees and batch processing strategies for email categorization using the 5-bucket system.

## The 5D+N Framework

Triage assigns every email to exactly one of five buckets. "4D+N" is a misnomer — NOISE is a full bucket, not a suffix. Use 5 buckets consistently:

```
                    ┌─────────────────────────────┐
                    │    Is action required of me? │
                    └──────────────┬──────────────┘
                          Yes      │      No
               ┌──────────────────┤├──────────────────────┐
               ▼                  │                        ▼
    ┌──────────────────┐          │          ┌─────────────────────────┐
    │ Can someone else  │          │          │  Does it have value to  │
    │    do this?       │          │          │    keep for reference?  │
    └────────┬─────────┘          │          └────────────┬────────────┘
       Yes   │   No               │               Yes     │    No
             │   │                │                       │    │
             ▼   ▼                │               ┌───────┘    ▼
        DELEGATE DO               │               REFERENCE  NOISE
                                  │
              Is it urgent now?   │
            ┌─────────────────────┘
     Yes    │    No
     │      ▼
     │    DEFER
     ▼
    DO (P0/P1)
```

## Decision Criteria

### DO (Action Required)

| Priority | Criteria | Response Target |
|----------|----------|-----------------|
| P0 | Deadline today, VIP sender, blocking someone else | Within hours |
| P1 | Deadline this week, important stakeholder | Within 24h |
| P2 | Should respond, no hard deadline | Within 48h |

Signals: direct question to you, "please review" / "your approval needed", explicit deadline, VIP sender, you are in `To:` (not just `Cc:`).

### DELEGATE

Forward when someone else owns the topic, you were CC'd without being the primary addressee, or another team member has more context. Include one-sentence context + expected outcome.

### DEFER

Label `_deferred` and archive when actionable but not urgent, requires focus time, or is waiting on external input. Process during daily sweep (see `inbox-zero-system.md` Daily Routine Step 2).

### REFERENCE

Archive immediately when the email has useful information but requires no action — receipts, confirmations, documentation, announcements. Do not leave REFERENCE items in the inbox.

### NOISE

Archive or delete without reading when the email has no value: automated notifications, unwanted marketing, social alerts. Collect NOISE IDs during scan — batch-archive at Wave 2 end (see Batch Operations below).

## Sender Shortcuts

| Pattern | Default Bucket |
|---------|---------------|
| `notifications@*` | NOISE |
| `noreply@*` | NOISE or REFERENCE |
| `calendar-notification@*` | NOISE (unless attendance needed) |
| `*@your-company.com` | DO (check content) |
| Known VIP senders | DO |
| Mailing lists | REFERENCE or NOISE |

## Subject Signals

| Signal | Default Bucket |
|--------|---------------|
| `[ACTION]`, `[URGENT]`, `[REQUEST]` | DO |
| `[FYI]`, `[INFO]`, `[ANNOUNCEMENT]` | REFERENCE |
| `RE:` (your active thread) | DO if reply needed, else REFERENCE |
| `FWD:` | REFERENCE unless explicit ask |
| `Weekly digest`, `Newsletter`, `Roundup` | REFERENCE or NOISE |

## Content Signals

| Signal | Default Bucket |
|--------|---------------|
| Question mark directed at you | DO |
| "Please review" / "your input needed" | DO |
| "No action needed" / "for your records" | REFERENCE |
| Unsubscribe footer, bulk mailer headers | NOISE |
| "Automated message" / "do not reply" | NOISE |

## Batch Processing

Triage runs in three waves. Collect message IDs throughout — never process one email at a time when a batch call covers the same operation.

### Wave 1: Quick Scan (2 min)

- Scan subject + sender only. Do not open emails.
- Star obvious P0/P1 items.
- Collect IDs of clear NOISE into `noise_ids[]`.
- Collect IDs of clear REFERENCE into `ref_ids[]`.

### Wave 2: Categorize (5–10 min)

Apply full 5-bucket decision tree to remaining unread items.

At Wave 2 end, issue batch operations for collected IDs:

```
# Archive all NOISE in one call
gmail_batch_modify_emails(
  messageIds = noise_ids,
  addLabelIds = [],
  removeLabelIds = ["INBOX"]
)

# Label and archive all REFERENCE in one call
gmail_batch_modify_emails(
  messageIds = ref_ids,
  addLabelIds = ["_reference"],   # or "ARCHIVE" label
  removeLabelIds = ["INBOX", "UNREAD"]
)
```

Use `gmail_get_or_create_label` before the batch call to ensure `_reference` exists. Max 1000 IDs per call — split into chunks for large volumes.

### Wave 3: Process Action Queue (variable)

Work the DO queue in priority order: P0 → P1 → P2.

For DELEGATE items, batch-forward before working P1/P2 responses — forwarding is fast and unblocks others.

For DEFER items, apply the `_deferred` label in batch before closing the session:

```
gmail_batch_modify_emails(
  messageIds = deferred_ids,
  addLabelIds = ["_deferred"],
  removeLabelIds = ["INBOX"]
)
```

---

## Inbox Zero Integration

After triage, log results to the inbox-zero-system protocol (see `inbox-zero-system.md`).

### Post-Triage Checklist

1. Inbox contains only DO items (P0/P1/P2).
2. `_deferred` label holds actionable-but-not-now items.
3. NOISE and REFERENCE are out of inbox (batch-archived above).
4. Update progress tracking at `~/.claude/email-whiz/inbox-zero-progress.json`.

### Logging the Session

After Wave 3, record the final inbox count and unread count. If inbox reaches 0, increment the streak. If 2+ days have passed since last check, reset the streak per the rules in `inbox-zero-system.md`.

Recurring NOISE patterns seen during triage → candidates for new filters (`gmail_create_filter_from_template`). Surface these to the user at session end so they reduce future volume.

---

## Volume Strategies

| Daily Volume | Strategy |
|-------------|---------|
| < 30/day | Process as received; single daily Wave cycle |
| 30–100/day | Batch 2–3x daily; strict Wave 1/2/3 separation |
| 100–300/day | Strict filtering; process top 20% only; defer rest |
| 300+/day | Declare email bankruptcy; use staged recovery from `inbox-zero-system.md` |

At 100+/day, run `gmail_search_emails` with `is:important is:unread` before general triage to surface Gmail-ranked priority items first.

---

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Reading fully during Wave 1 | Triage takes 30+ min | Scan subject + first line only |
| Leaving "maybe later" in inbox | Inbox never empties | DEFER with label or delete |
| Opening the same email twice | Double processing time | One touch: decide and act |
| Skipping deferred review | Deferred pile grows unbounded | Schedule daily sweep per `inbox-zero-system.md` |
| Archiving NOISE one at a time | Slow; wastes API calls | Collect IDs, batch-archive at Wave 2 end |
| Forgetting to log progress | Streak tracking breaks | Always update `inbox-zero-progress.json` after triage |
