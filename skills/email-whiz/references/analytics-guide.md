# Analytics Guide

> Email communication analytics methodology. Volume trends, response time analysis, sender frequency, time-of-day patterns, and report formats.

## Overview

Email analytics answers these questions:
- **Volume**: How many emails per day/week/month? Growing or shrinking?
- **Response**: How fast do I reply? Which threads are overdue?
- **Senders**: Who sends the most? Who gets replies? Who is noise?
- **Patterns**: When does email arrive? When do I respond?
- **Labels**: Which categories are most active? Which are stale?

All analytics use `gmail_search_emails` with date-range and label filters. Attachment metadata is available from `gmail_read_email` message payloads without downloading files.

---

## Volume Analysis

### Total Volume

```
# Received this week
in:inbox after:{7d_ago}

# Received this month
in:inbox after:{30d_ago}

# Received last month (comparison)
in:inbox after:{60d_ago} before:{30d_ago}

# Total sent this month
in:sent after:{30d_ago}
```

### Volume Trend

Compute for last 4 weeks:
```
Week N:   in:inbox after:{28d_ago} before:{21d_ago}
Week N-1: in:inbox after:{21d_ago} before:{14d_ago}
Week N-2: in:inbox after:{14d_ago} before:{7d_ago}
Week N-3: in:inbox after:{7d_ago}
```

Classify trend:
- Growing (>10% week-over-week) → filter opportunities
- Stable (±10%) → normal
- Declining (>10% decrease) → filters working

### Inbox vs Filtered Ratio

```
# Direct inbox (not filtered)
in:inbox has:nouserlabels after:{30d_ago}

# Total incoming
in:anywhere -in:sent after:{30d_ago}

Ratio = inbox / total × 100
Good: <30% reaching inbox
Needs work: >60% reaching inbox
```

---

## Response Time Analysis

### Overdue Response Detection

```
# Starred (action needed) older than 48h
is:starred older_than:2d

# Threads waiting for reply
in:inbox subject:Re: is:unread older_than:24h
```

### Reply Rate Calculation

```
# Emails you received (sample: last 100)
in:inbox after:{30d_ago}

# Emails you replied to
in:sent subject:Re: after:{30d_ago}

Reply rate = sent Re: / received × 100
Note: not exact but indicative
```

### Response Time Buckets

For each thread requiring action, classify by age:
```
<4h    → Same-day responsive
4-24h  → Normal
1-3d   → Slow
3-7d   → Overdue
>7d    → Critical backlog
```

Report format:
```
RESPONSE OVERVIEW (last 30 days)

Same-day:  {count} ({pct}%)
Normal:    {count} ({pct}%)
Slow:      {count} ({pct}%)
Overdue:   {count} <- address these
Critical:  {count} <- urgent

Oldest unaddressed: {subject} from {sender} ({age}d ago)
```

---

## Sender Frequency Analysis

### Top Senders

```
# Find high-volume senders
# Query batches: search each and count
in:inbox after:{30d_ago}

Sort results by from: field, count occurrences
```

### Sender Engagement Matrix

For top 20 senders, compute:
- **Volume**: emails received from sender in 30d
- **Reply rate**: search `in:sent to:{sender} after:{30d_ago}` / received
- **Read rate**: estimated from recency and label activity
- **Category**: VIP / Active / Passive / Noise

```
Classification:
Volume > 10 AND reply_rate > 50% → VIP candidate
Volume > 10 AND reply_rate < 10% → Filter candidate
Volume > 20 AND reply_rate = 0%  → Likely noise
```

### Sender Report Format

```
TOP SENDERS (last 30 days)

VIP (reply often):
1. {sender} — {count} emails | {reply_rate}% replied
2. ...

Filter candidates (high volume, low engagement):
1. {sender} — {count} emails | {reply_rate}% replied
2. ...

Noise (high volume, never replied):
1. {sender} — {count} emails | filter suggestion: {criteria}
2. ...
```

---

## Time-of-Day Patterns

### Email Arrival Patterns

Sample last 200 emails from search results. Extract hour from `date` field.

```
# Morning batch (6am-10am)
in:inbox after:{date_0600} before:{date_1000}

# Work hours (10am-6pm)
# Evening (6pm-10pm)
# Overnight (10pm-6am)
```

### Your Sending Patterns

```
in:sent after:{30d_ago}
Extract hour from date field of each result
```

Report format:
```
EMAIL TIMING PATTERNS

Arrival peak: {hour}:00 ({pct}% of daily email)
Your send peak: {hour}:00

Arrival by period:
Morning (6-10am):  ████░ {pct}%
Work (10am-6pm):   ████████ {pct}%
Evening (6-10pm):  ██░ {pct}%
Overnight:         █░ {pct}%

Recommendation: {batch_time_suggestion}
```

---

## Label Distribution

### Active Labels

```
For each label from gmail_list_email_labels:
  - Search: label:{name} newer_than:30d → activity count
  - Search: label:{name} → total count
  - Last email date from search results
```

### Stale Label Detection

Classify:
- **Active**: messages in last 30d
- **Cold**: last message 30-90d ago
- **Stale**: no messages in 90d+ (deletion candidate)
- **Empty**: 0 messages ever (cleanup candidate)

---

## Attachment Analysis

Attachment metadata (filename, size, MIME type) is available in `gmail_read_email` response body under `parts[].filename` and `parts[].body.size` — no download required.

```
# Find large emails with attachments
has:attachment larger:5M after:{30d_ago}

# Find specific file types
filename:pdf after:{30d_ago}
filename:zip after:{30d_ago}
```

Storage report:
```
ATTACHMENT SUMMARY (last 30 days)

Total emails with attachments: {count}
Large (>5MB): {count} — {total_size}MB

Top file types:
- PDF: {count} files
- ZIP: {count} files
- Images: {count} files
```

---

## Full Analytics Report Format

```
EMAIL ANALYTICS

Period: {start} — {end}

VOLUME
Received: {count} | Sent: {count}
Trend: {growing/stable/declining} ({pct}% vs prior period)
Inbox reach rate: {pct}% (target: <30%)

RESPONSE
Reply rate: {pct}%
Avg response time: {hours}h
Overdue: {count} threads need attention

TOP SENDERS
VIP:     {names}
Filters: {names} → {estimated_reduction}% inbox reduction
Noise:   {names}

TIMING
Peak arrival: {hour}:00 | Your send peak: {hour}:00

LABEL HEALTH
Active: {count} | Cold: {count} | Stale: {count} (cleanup recommended)

QUICK WINS
1. {action} — {impact}
2. {action} — {impact}
3. {action} — {impact}
```

---

## Performance Notes

- Fetch 50-100 emails per search (set maxResults explicitly)
- Use date ranges to scope large analyses
- Sender frequency analysis: sample 200 most recent, not full history
- Response time: estimate from thread structure, not exact measurement
- All metrics are approximate — Gmail MCP doesn't expose read receipts or exact open times
