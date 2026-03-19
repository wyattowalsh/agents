# Response Templates

> Copy-paste templates for confirmations, reports, and execution results. Substitute `{variables}` with actual values.

---

## Confirmation Templates

Show these BEFORE executing any operation that modifies email state.

### Single Action Confirmation

```
ACTION REQUIRED — CONFIRM

Operation: {Archive | Apply label "{label}" | Remove label "{label}" | Mark read}
Target: "{subject}" from {sender} ({date})

Reply "yes" to proceed. Reply "cancel" to abort.
```

### Batch Action Confirmation

```
📦 BATCH OPERATION

Operation: {Archive | Apply label | Remove label}
Scope: {count} emails matching "{search_criteria}"

Sample (first 3):
• "{subject}" from {sender} — {date}
• "{subject}" from {sender} — {date}
• "{subject}" from {sender} — {date}
{if count > 3}...and {count - 3} more{/if}

Reversible: Yes — can undo via archive

Reply: "execute" | "show all" | "cancel"
```

### Compact Batch Report

```
BATCH COMPLETE — {count} emails in {duration}

{operation}: {count} | Failed: {failed_count}
Top senders: {sender1} ({n}), {sender2} ({n}), {sender3} ({n})
```

### Context Pressure Warning

```
⚠ LARGE DATASET

{count} emails match this query. Processing in batches of {batch_size}.
Estimated: {rounds} rounds | ~{est_time} processing time

Reply "proceed" | "narrow scope" | "cancel"
```

### Baseline Bankruptcy Alert

```
⚠ INBOX ALERT — {level}

Current: {current_count} | Baseline: {baseline} | Delta: +{pct}%
Trend: {trend} for {weeks} weeks

{if YELLOW}Suggestion: Run an extra triage session today.{/if}
{if ORANGE}Recommendation: Aggressive triage + create filters for top noise senders.{/if}
{if RED}Action needed: Choose recovery plan — Daily Blitz | Staged | Nuclear Reset{/if}

Reply "triage" | "auto-rules" | "show recovery options"
```

### Label/Filter Deletion Warning

```
⚠ CONFIRM DELETION

Operation: Delete {label | filter}
Target: "{name}"

This removes the {label | filter} only — no emails are affected.

Reply "confirm" to proceed. Reply "cancel" to abort.
```

### Filter Creation Confirmation

```
NEW FILTER — CONFIRM

Criteria: {from: "{sender}" | subject contains: "{term}" | ...}
Action:   {Skip inbox | Apply label "{label}" | Mark read | Delete}
Effect:   Applies to {est_count} existing emails + all future matches

Reply "create" to save. Reply "cancel" to abort.
```

---

## Report Templates

### Triage Summary

```
TRIAGE COMPLETE — {total} emails in {duration}

DO        {count}  ({count} P0 | {count} P1 | {count} P2)
DELEGATE  {count}
DEFER     {count}
REFERENCE {count}
NOISE     {count}

Inbox: {count} remaining | Unread: {unread_count}

{if do_count > 0}
Action queue: P0 "{subject}" — {sender} | P1 "{subject}" — {sender}
{/if}
{if filter_candidates > 0}
Filter suggestions: {filter_candidates} noise patterns — run /email-whiz filters to create.
{/if}
```

### Fast-Lane Triage Summary

```
TRIAGE — {total} emails ({fast_lane_pct}% auto-classified)

FAST-LANE: {fast_count} auto-classified
  NOISE     {noise_count} (archived)
  REFERENCE {ref_count} (archived + labeled)
  DO        {do_count} (kept in inbox)
SECURITY GATE: {rescued_count} rescued from NOISE
INSPECTED: {inspect_count} content reads
  DO {n} (P0:{n} P1:{n} P2:{n}) | DELEGATE {n} | DEFER {n} | REF {n} | NOISE {n}

Inbox: {before} → {after}
Filter candidates: {filter_count} noise patterns — run /email-whiz filters
```

### Filter Suggestions Report

```
FILTER SUGGESTIONS — {count} patterns worth automating

{n}. {sender_or_pattern}
   Frequency: ~{count}/month
   Action: {Skip inbox + label "{label}" | Mark read + archive}
   Matches {est_pct}% of inbox volume

Reply "create all" | "create {n}" | "skip"
```

### Newsletter Audit Report

```
NEWSLETTER AUDIT — {count} subscriptions scanned

NEVER READ (unsubscribe):   {sender} — {count} emails, {oldest_unread}d unread
OCCASIONALLY READ (filter): {sender} — {pct}% read rate
REGULARLY READ (keep):      {sender} — {pct}% read rate

Recommended: Unsubscribe {unsubscribe_count}, filter {filter_count} to label.
Est. inbox reduction: {pct}%

Reply "unsubscribe all never-read" | "create filters" | "show details"
```

### Label Analysis Report

```
LABEL ANALYSIS — {total_count} labels ({system_count} system, {user_count} user)

ACTIVE (last 30d):    {name} — {count} total, {recent_count} new this month
COLD (30–90d):        {name} — last message {days}d ago
STALE (90d+):         {name} — last message {days}d ago → REMOVE?
EMPTY:                {name} → REMOVE?

Reply "remove stale" | "remove empty" | "remove all unused" | "skip"
```

### Full Audit Report

```
EMAIL AUDIT COMPLETE — {email_address}
Scope: {start_date} — {end_date}

VOLUME:   Inbox {inbox_total} | Unread {unread_count} | Sent (30d) {sent_count}
FILTERS:  Active {filter_count} | Redundant {redundant_count} | Gaps {gap_count}
LABELS:   Active {active_count} | Stale {stale_count} (cleanup recommended)

TOP NOISE:  {sender} — {count}/month, {reply_pct}% replied

QUICK WINS
1. {action} — est. {pct}% inbox reduction
2. {action} — est. {pct}% inbox reduction
3. {action} — est. {pct}% inbox reduction

Run: triage | filters | labels | analytics
```

### Email Digest

```
EMAIL DIGEST — {date}
INBOX: {count} | Unread: {unread_count}

ACTION NEEDED:
  • [{priority}] "{subject}" from {sender} — {age}

DEFERRED ({deferred_count}):
  • "{subject}" from {sender} — deferred {days}d ago

WAITING ON OTHERS ({waiting_count}):
  • "{subject}" — sent {days}d ago, no reply

Reply "triage" | "process deferred" | "follow up waiting"
```

---

## Analytics Report

```
📊 EMAIL ANALYTICS — {period}

VOLUME
Received: {received} | Sent: {sent}
Trend: {↑ growing | → stable | ↓ declining} ({pct_change}% vs prior {period})
Inbox reach rate: {pct}% ({good <30% | needs filters >60%})

RESPONSE HEALTH
Reply rate: {pct}%
Overdue threads: {count}
{if overdue_count > 0}
Oldest: "{subject}" from {sender} — {days}d ago
{/if}

TOP SENDERS (by volume, last 30d)
VIP: {name} ({count}), {name} ({count})
Filter candidates: {name} ({count}, {reply_pct}% replied)

LABEL HEALTH
Active: {count} | Stale: {count} labels
{if stale_count > 0}Cleanup candidates: {stale_label_names}{/if}

QUICK WINS
1. {action} → est. {pct}% inbox reduction
2. {action} → est. {pct}% noise reduction
```

---

## Inbox Zero Progress

### Daily Check-In

```
📬 INBOX ZERO CHECK

Date: {date}
Inbox: {count} emails | Unread: {unread_count}
Status: {✓ ZERO | ⚠ {count} remaining}

Streak: {current_streak} days (best: {longest_streak})
Last zero: {last_zero_date}

{if count > 0}
Remaining items:
• "{subject}" from {sender} ({age}) — Suggested: {DO | DEFER | ARCHIVE}
• ...

Reply "process remaining" | "defer all" | "done for today"
{/if}
```

---

## Auto-Rule Analysis

```
🤖 AUTO-RULE ANALYSIS

Analyzed: {count} emails over {period}

HIGH CONFIDENCE — CREATE NOW:
{for each high_confidence_rule}
  {n}. {rule_name}
     Match: {criteria}
     Action: {skip inbox + label | archive | mark read}
     ~{count}/month | Confidence: {pct}%
{/for}

MEDIUM CONFIDENCE — REVIEW:
{for each medium_confidence_rule}
  {n}. {rule_name}
     Match: {criteria}
     Reason: {why_suggested}
     Confidence: {pct}%
{/for}

LOW CONFIDENCE (skipped — insufficient data):
• {count} patterns below threshold

Est. inbox reduction: -{pct}% if all HIGH rules created

Reply: "create all high" | "create {n}" | "review {n}" | "skip"
```

### Auto-Scan Report

```
INBOX SCAN — {email_address}
Tier: {tier} | Inbox: {inbox_count} | Unread: {unread_count}
Trend: {trend} ({delta} vs last week) | Baseline: {baseline}
{if bankruptcy_level != NORMAL}⚠ {bankruptcy_level}: {pct}% above baseline{/if}

RECOMMENDED ACTIONS:
{for each recommendation, sorted by priority}
{n}. [{mode}] — {reason}
   Impact: {estimated_impact}
{/for}

Reply: number | mode name | "all" (run top 3) | "menu" (full mode list)
```

---

## Execution Result Templates

Show these AFTER an operation completes.

### Success

```
DONE

{Archive | Label | Filter created}: {count} email{count != 1 ? "s" : ""}
{if label_applied}Label applied: "{label_name}"{/if}
{if filter_created}Filter saved — applies to all future matches{/if}
```

### Partial Failure

```
PARTIALLY COMPLETE

Succeeded: {success_count} emails
Failed:    {failed_count} emails

Failed IDs:
  • {message_id} — {error_reason}

Reply "retry" | "skip failed" | "show errors"
```

### Error

```
ERROR — OPERATION NOT COMPLETED

Error: {error_message}
Code:  {error_code}

{if code == 401}Action: Re-authenticate the Gmail MCP server.{/if}
{if code == 403}Action: Check OAuth scopes in MCP server configuration.{/if}
{if code == 429}Action: Rate limited — retry in 60 seconds.{/if}
{if code == 500}Action: Gmail API outage — retry with exponential backoff.{/if}

No emails were modified.
```

---

## Memory Summary

Show at end of session when memories were saved or updated.

### Memory Update Report

```
MEMORIES UPDATED

Saved: {new_count} new | Updated: {updated_count} existing | Pruned: {pruned_count} stale
VIPs: {vip_count} | Noise: {noise_count} | Overrides: {override_count} | Corrections: {correction_count}

{if corrections_saved > 0}
Corrections recorded — will apply in future sessions:
  • {pattern} → {bucket} (was: {original_bucket})
{/if}
{if pruned_count > 0}
Pruned stale entries: {pruned_details}
{/if}
```
