# Email Workflows

> Playbooks for common email management scenarios. Each workflow defines the trigger, phases, tools, and expected outcome.

---

## Email Bankruptcy — Nuclear Reset

**Trigger:** Inbox unread > 1000 or user requests a clean slate.

```
0 — Rescue: is:unread is:important newer_than:7d | from:{VIP_LIST} newer_than:7d → star

1 — Confirm: show total unread, count older_than:7d, 5-email sample
    Warning: "This will archive N emails. Archive is reversible."

2 — Archive: is:unread older_than:7d
    gmail_batch_modify_emails: removeLabelIds: ["INBOX"], batchSize: 50

3 — Fresh start: apply _deferred to starred items; create baseline filters
    See inbox-zero-system.md for daily routine
```

---

## Email Bankruptcy — Staged Approach

**Trigger:** Inbox unread 200–1000, user prefers gradual recovery.

```
Week 1: is:unread older_than:30d → confirm → archive batch
Week 2: is:unread older_than:14d → confirm → archive batch
Week 3: is:unread older_than:7d  → confirm → archive batch
Week 4: switch to daily routine (inbox-zero-system.md)
```
At each step: show count + 3-email sample before archiving.

---

## VIP Management

**Trigger:** User wants priority handling for specific contacts.

```
Setup:
  gmail_get_or_create_label: "_vip"
  gmail_create_filter_from_template: fromSender
    action: {addLabelIds: ["Label_vip"], markImportant: true}

Daily: label:_vip is:unread → surface immediately before routine triage

Quarterly: remove stale VIP filters; promote new high-reply-rate senders
```

---

## Project Email Organization

**Trigger:** User starts a project or has project email scattered across inbox.

```
Setup:
  gmail_get_or_create_label: "_projects/{name}"
  gmail_create_filter: {hasWords: "keyword"} → addLabelIds: ["Label_projects/{name}"]
  Backfill: search {keywords} → gmail_batch_modify_emails

View: label:_projects/{name} is:unread | is:starred

Archival: hide label visibility; gmail_delete_filter; retain label for search
```

---

## Travel Email Management

**Trigger:** User mentions travel or has booking confirmations in inbox.

```
Labels: gmail_get_or_create_label: "_travel/confirmations" | "_travel/itinerary"

Filters:
  {hasWords: "booking confirmation OR reservation OR itinerary OR e-ticket"}
    → addLabelIds: ["_travel/confirmations"], markRead: true
  {from: "noreply@airbnb.com OR noreply@booking.com OR united.com OR delta.com"}
    → addLabelIds: ["_travel/confirmations"]

Backfill: (confirmation OR reservation OR itinerary) after:{trip_start}
  → gmail_batch_modify_emails: addLabelIds: ["Label_travel/confirmations"]

View: label:_travel/confirmations newer_than:30d
```

---

## Unsubscribe Strategies

**Trigger:** High newsletter/promotional volume or user reports inbox noise.

```
Identify: unsubscribe in:inbox after:{30d_ago}
Flag: sender > 5/month, 0 replies = candidate

A — Suppress (keep list, remove from inbox):
  gmail_create_filter_from_template: fromSender
  action: {addLabelIds: ["_reading/newsletters"], removeLabelIds: ["INBOX"], markRead: true}

B — Delete + unsubscribe:
  gmail_read_email → surface unsubscribe link (user clicks manually)
  from:{sender} → gmail_batch_delete_emails (confirm first)

C — Quarterly audit:
  label:_reading/newsletters is:unread older_than:14d → unsubscribe or delete
```

---

## Email Analytics

For full methodology, see `analytics-guide.md`. Quick reference:

### Inbox Health Queries
```
# This week received (inbox reach rate numerator)
in:inbox after:{7d_ago}

# Filtered/labeled (not inbox) — denominator for reach rate
-in:inbox -in:sent -in:drafts -in:trash after:{7d_ago}

# Good: <30% reaching inbox directly
# Needs work: >60% reaching inbox directly
```

### Backlog Detection
```
# Growing backlog: unread older than 7d
is:unread older_than:7d

# Deferred pile
label:_deferred

# Waiting-on responses
label:_waiting older_than:7d
```

### Quick Health Report
```
INBOX HEALTH

Inbox reach rate:  {pct}% (target: <30%)
Unread backlog:    {count} older than 7d
Deferred pile:     {count} items
Waiting:           {count} items older than 7d

Action: {top 1-3 quick wins}
```

---

## Batch Operations

Use `gmail_batch_modify_emails` for any operation affecting 3+ emails.

### Archive Batch
```
messageIds: [...], removeLabelIds: ["INBOX"], batchSize: 50
```

### Label Batch
```
messageIds: [...], addLabelIds: ["Label_xxx"], batchSize: 50
```

### Label Consolidation (merge two labels)
```
1. Search: label:{old_label} (maxResults: 500, paginate if needed)
2. gmail_batch_modify_emails: add new_label, remove old_label
3. gmail_delete_label: old_label
```

### Confirmation Protocol (required before every batch)
- Show count: "This will modify N emails"
- Show sample: first 3 subjects + senders
- State reversibility: archive is reversible; delete is not
- Delete warning: "Delete is IRREVERSIBLE. Archive instead if unsure."

---

## Label Hierarchy Best Practices

Gmail labels are flat but use `/` for visual hierarchy.

### Recommended Structure
```
_action/waiting    # Sent, awaiting reply
_deferred/         # Intentionally postponed
_reading/newsletters
_reference/receipts
_reference/docs
_projects/{name}   # Project-specific threads
_vip/              # Priority contacts
_dev/github        # CI / GitHub notifications
_dev/ci
_travel/confirmations
_travel/itinerary
```

### Rules
- Underscore prefix sorts system labels to top of Gmail sidebar
- Max 3 levels deep: Gmail UI truncates deeper nesting
- Archive, not label, for true reference material (search finds it either way)
- Always use `gmail_get_or_create_label` (idempotent); never `gmail_create_label` directly

### Label Cleanup (quarterly)
```
gmail_list_email_labels → messagesTotal = 0 → delete
No messages in 90d → stale, review
Merge overlapping labels using label consolidation above
```

---

## Security Hygiene

**Trigger:** User requests security audit or suspicious activity detected.

```
Suspicious pattern searches:
  subject:("password reset" OR "account verification" OR "unusual sign-in")
  from:{unknown-domain} has:attachment newer_than:7d
  subject:("urgent" OR "wire transfer" OR "gift card") is:unread

Phishing signals (surface to user; never click links on their behalf):
  sender domain mismatches display name | credential/payment requests | urgency + unknown sender

Exposure audit:
  subject:"data breach" OR subject:"security notice" newer_than:90d

Threat filter:
  gmail_create_filter: {hasWords: "wire transfer OR gift card OR bitcoin"}
  action: {addLabelIds: ["_review/security"], markImportant: true}
```

---

## Multiple Accounts

**Trigger:** User manages 2+ Gmail accounts through the MCP server.

Treat each account as a separate context. Never mix messageIds across accounts.

```
Per-account baseline:
  in:inbox is:unread | in:sent after:{7d_ago}
  gmail_list_email_labels | gmail_list_filters

Cross-account rules:
  Run analytics separately (never aggregate)
  Maintain separate VIP filter sets per account
  Tag forwarded mail with source account label
```

---

## High-Volume Transactional

**Trigger:** Inbox flooded with automated email (CI, monitoring, SaaS notifications).

```
Identify sources:
  in:inbox after:{7d_ago} → cluster by from: domain
  Flag: domain >20/week = transactional candidate

Tiered handling:
  Tier 1 — suppress inbox, keep accessible (mark read):
    action: {addLabelIds: ["_dev/github"], removeLabelIds: ["INBOX"], markRead: true}
  Tier 2 — suppress inbox, keep unread (review weekly):
    action: {addLabelIds: ["_dev/ci"], removeLabelIds: ["INBOX"]}
  Tier 3 — delete immediately (true noise, never needed):
    action: {delete: true}

Backfill: from:{sender} in:inbox → gmail_batch_modify_emails

Effectiveness (weekly): in:inbox after:{7d_ago} -label:_vip
  Count > 50 → find next filter candidates
```
