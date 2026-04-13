# Efficiency Guide

> Parallelization and rate-limit bible for email-whiz Gmail management (v4.0). Governs session caching, call fusion, tier-based throttling, and error recovery.

## Session Cache Protocol

- **Path:** `~/.{gemini|copilot|codex|claude}/email-whiz/session-cache.json`
- **TTL:** 60 minutes. Invalidate on any write operation (filter/label create, batch modify).
- **Schema:**
  ```json
  {
    "labels": [{"id": "str", "name": "str", "type": "str", "messagesTotal": 0, "messagesUnread": 0}],
    "filters": [{"id": "str", "criteria": {}, "action": {}}],
    "inbox_count": 0,
    "unread_count": 0,
    "tier": "Small|Medium|Large|Massive",
    "last_fetched": "2026-03-15T12:00:00Z"
  }
  ```
- **Load:** !`uv run python scripts/inbox_snapshot.py cache load`
- **Save:** !`uv run python scripts/inbox_snapshot.py cache save --labels '...' --filters '...' --inbox-count N --tier TIER`
- **Clear:** !`uv run python scripts/inbox_snapshot.py cache clear`
- **Write-through invalidation:** After any `gmail_create_label`, `gmail_get_or_create_label`, `gmail_create_filter`, `gmail_create_filter_from_template`, or `gmail_batch_modify_emails`, re-fetch the affected resource and update cache immediately. Never serve stale data after a write.

---

## Parallel Call Map

Fuse independent calls into the fewest messages possible. Each row = one mode.

| Mode | Message 1 (Phase 0 + fusion) | Message 2 | Message 3 |
|------|------------------------------|-----------|-----------|
| **Triage** | 3x discovery + unread search | 3x batch_modify (NOISE/REF/DEFER) | 5-8x read_email (UNDECIDED) |
| **Inbox Zero** | 3x discovery + unread + deferred | batch ops | — |
| **Analytics** | 3x discovery + 12x queries (mega-wave) | — | — |
| **Audit** | 3x discovery + 11x queries (mega-wave) | — | — |
| **Cleanup** | 3x discovery + 4x stale queries | parallel batch_modify | — |
| **Filters** | 3x discovery + sender + subject + list_filters | parallel create_filter | — |
| **Auto-Rules** | 3x discovery + sender + subject + filters | parallel create_filter | — |
| **Senders** | 3x discovery + sample + reply-rate queries | — | — |
| **Newsletters** | 3x discovery + list:* + subject:newsletter | per-sub read-rate queries | — |
| **Auto-Scan** | 3x discovery + 6x analysis queries + 2x scripts (~10) | scoring + report (0 tools) | — |

**Quick-compatible modes** (skip Phase 0): `search`, `digest`. Go straight to the primary query.

---

## MCP Server Constraints

- **`gmail_search_emails`:** Accepts `query` + `maxResults` only. No `pageToken`. Hard ceiling 500 per call.
- **`gmail_read_email`:** Accepts `messageId` only. Always returns full message. No format control. Expensive.
- **`gmail_batch_modify_emails`:** Accepts `messageIds` + `addLabelIds`/`removeLabelIds` + `batchSize` (default 50). Up to 1000 IDs per call.
- **`gmail_batch_delete_emails`:** Not in allowed-tools. Email deletion is disabled in this skill.
- **`resultSizeEstimate`** is unreliable. Use INBOX label `messagesTotal` from `gmail_list_email_labels`.
- **N+1 fetch pattern:** `search_emails` likely fetches full message for each result. `maxResults=500` ≈ 501 API calls ≈ 2505 quota units.

---

## Gmail API Rate Limits

- **15,000 quota units/user/minute.**
- `messages.list` = 5 units, `messages.get` = 5 units, `batchModify` = 50 units (up to 1000 msgs).
- `batchModify` is 100x more efficient than individual modify calls.
- With N+1: `maxResults=200` ≈ 1005 units. ~15 such queries/minute before hitting limits.
- Daily quota (1.2M units/project) is not a practical concern for single-user usage.

---

## Inbox Tier System

| Inbox Size | Tier | maxResults | Why Not Higher | Strategy |
|------------|------|------------|----------------|----------|
| <50 | Small | 50 | N/A | Process all |
| 50-500 | Medium | 100 | N+1: 505 units | Sample recent + unread |
| 500-5000 | Large | 200 | N+1: 1005 units | Importance-first, date-range splitting |
| 5000+ | Massive | 200 | Split by date-range | Date-range parallel queries, baseline bankruptcy |

### Massive Tier Protocol (5k-20k)

1. Get INBOX `messagesTotal` from `gmail_list_email_labels` for accurate count.
2. Calculate date chunks: `total ÷ 200 = N chunks`.
3. Issue ALL chunk queries in 1 message (date-range splitting).
4. Always query `is:important is:unread` alongside the general scan.
5. Bankruptcy: relative to rolling 30-day baseline from snapshot history.
6. Cap `gmail_read_email` at 20 per mode to manage context.

---

## Fast-Lane Protocol

Summary (full details in `triage-framework.md` § Fast-Lane):

- Classify 60-80% of emails without content reads using sender + subject + snippet signals.
- Security gate mandatory: scan NOISE subjects for security keywords before archiving.
- Never auto-archive `noreply@` emails `newer_than:7d` (login notifications have no expiry).
- Fast-lane resolved emails feed directly into filter candidate detection.

---

## Date-Range Splitting

The only pagination mechanism available (no `pageToken` on MCP server):

1. Estimate total time range from inbox age or messagesTotal.
2. Split into N chunks where each chunk ≈ 200 results.
3. Issue ALL chunk queries in ONE message.
4. Merge results after all return, dedup by message ID.

**Example** for 90d with ~3000 emails:
```
Query 1: in:inbox after:2025/12/15 before:2026/01/14
Query 2: in:inbox after:2026/01/14 before:2026/02/13
Query 3: in:inbox after:2026/02/13
```
All 3 queries dispatched in a single message.

---

## Quick Mode

Modes that skip Phase 0: **search**, **digest**.

Skip means: no label discovery, no filter discovery, no tier assessment. Go straight to the mode's primary query. Use when the user needs a fast answer and full inbox context is unnecessary.

---

## Combo Mode Protocol

For `<mode1> + <mode2>`:

1. Phase 0 runs once (shared across both modes).
2. Mode 1 executes fully, returns modification manifest (archived IDs, created filters/labels).
3. If mode 1 performed writes: refresh affected resources before mode 2.
4. Mode 2 executes with enriched context, excluding already-processed IDs.
5. Phase 0 is NOT re-run for mode 2.

Common combos: `triage+filters`, `audit+auto-rules`, `cleanup+inbox-zero`.

---

## Adaptive Rate Limit Recovery

- Start at max parallelism (up to 15-20 concurrent calls).
- On first 429: preserve completed results, drop to sequential with 2-second gaps.
- 3x 429 in 60 seconds: circuit breaker — pause ALL Gmail calls for 60s, report to user.
- Batch size adaptation: halve on 429 (`50→25→12`), never below 10.
- After 10 successful sequential calls: try 2-parallel, then progressively restore.

---

## Context Window Management

- 500 email snippets ≈ 75k-125k tokens. Per-mode caps prevent overflow.
- `gmail_read_email` (full body): cap at 20 per mode.
- Summary-and-discard pattern: after processing each batch, compress findings before fetching next.
- Warning template when mode needs >300 emails: `"Processing in batches of {size}."`

---

## Error Recovery

| Error | Action |
|-------|--------|
| 429 Rate Limited | Adaptive parallelism (above). Halve batchSize. |
| 404 Not Found | Skip, continue, note in report. |
| Partial batch failure | Report succeeded/failed counts, offer retry for failed IDs. |
| Context pressure | Cap read_email at 20. Summary-and-discard between batches. |
| MCP connection failure | Report error, provide manual Gmail URL fallback. |
| Label ID mismatch | Re-fetch labels via `gmail_list_email_labels` and remap. |

---

## Per-Entity Query Batching

When a mode requires per-sender, per-label, or per-subscription queries:

- **≤12 entities**: Issue all reply-rate/activity queries in 1 message alongside discovery.
- **13-25 entities**: Split into 2 messages (12 + remainder).
- **>25 entities**: Split into messages of 10-12 queries each.

This prevents exceeding the 15-20 call-per-message cap while maximizing parallelism.

Examples:
- **Senders mode** with 20 top senders: 3 discovery + 12 reply queries (msg 1) → 8 reply queries (msg 2).
- **Labels mode** with 30 labels: 10 activity queries per message → 3 messages.
- **Newsletters mode** with 50 subscriptions: 12 read-rate queries per message → 5 messages.
