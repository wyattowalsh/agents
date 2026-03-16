# Dispatch Routing Evals

Evaluation cases for email-whiz dispatch table routing. Each case specifies input arguments and expected mode.

---

## Explicit Mode Tests

| Input | Expected Mode | Notes |
|-------|--------------|-------|
| `triage` | Triage | Categorize inbox |
| `inbox-zero` | Inbox Zero | Daily/weekly routine |
| `filters` | Filters | Pattern-detected suggestions |
| `auto-rules` | Auto-Rules | Behavioral analysis |
| `analytics` | Analytics | Volume/response/sender metrics |
| `newsletters` | Newsletters | Subscription audit |
| `labels` | Labels | Taxonomy analysis |
| `search find invoices from Q4` | Search | Goal: "find invoices from Q4" |
| `senders` | Senders | VIP + noise identification |
| `digest` | Digest | Recent important summary |
| `cleanup` | Cleanup | Archive candidates |
| `audit` | Audit | Full health report |
| _(empty)_ | Auto-Scan | Run Phase 0 + account analysis, present action plan |

---

## Natural Language Routing Tests

| Input | Expected Mode | Reasoning |
|-------|--------------|-----------|
| `I want to reach inbox zero` | Inbox Zero | Explicit goal mention |
| `help me clean up my inbox` | Cleanup or Triage | Ambiguous — ask |
| `analyze my email habits` | Analytics | "analyze" + "habits" → analytics |
| `create filters automatically` | Auto-Rules | "automatically" → auto-rules |
| `suggest filters for my inbox` | Filters | "suggest" → filters not auto-rules |
| `I'm overwhelmed by newsletters` | Newsletters | Explicit mention |
| `find all emails from last week` | Search | Goal-oriented search |
| `what emails need my attention` | Digest or Triage | Ambiguous — ask |

---

## Edge Cases

| Input | Expected Behavior |
|-------|------------------|
| `TRIAGE` | Route to Triage (case-insensitive) |
| `inbox zero` | Route to Inbox Zero (space variant) |
| `search` (no goal) | Ask user for search goal |
| `create filters` | Ask: auto-rules or manual filters? |
| `draft an email` | Decline — composing emails is out of scope |
| `check my calendar` | Decline — calendar is out of scope |

---

## Post-Confirmation Flow Tests

| Confirmation Response | Expected Action |
|----------------------|-----------------|
| `execute` | Run the batch operation |
| `skip` | Cancel, return to menu |
| `create 1,2` | Create only rules 1 and 2 |
| `details 3` | Show full details for suggestion 3 |
| `modify 2: also match from:domain.com` | Update rule 2 criteria, re-confirm |

---

## Quick Mode Tests

| Input | Expected Mode | Notes |
|-------|--------------|-------|
| `quick search invoices` | Search (quick) | Skip Phase 0 |
| `quick digest` | Digest (quick) | Skip Phase 0 |
| `quick triage` | Reject | Triage is not quick-compatible. Run without quick prefix |
| `quick analytics` | Reject | Analytics is not quick-compatible. Run without quick prefix |
| `quick audit` | Reject | Audit is not quick-compatible. Run without quick prefix |

---

## Combo Mode Tests

| Input | Expected Mode | Notes |
|-------|--------------|-------|
| `triage + filters` | Triage then Filters | Combo mode, shared state |
| `audit + auto-rules` | Audit then Auto-Rules | Combo mode, shared state |
| `cleanup + inbox-zero` | Cleanup then Inbox Zero | Combo mode, shared state |
| `triage+filters` | Triage then Filters | No spaces variant |

---

## Tier Detection Tests

| INBOX messagesTotal | Expected Tier | Expected maxResults |
|---------------------|--------------|---------------------|
| 30 | Small | 50 |
| 200 | Medium | 100 |
| 1500 | Large | 200 |
| 5000 | Massive | 200 + date-range splitting |
| 15000 | Massive | 200 + date-range splitting |

---

## Fast-Lane Classification Tests

| Sender | Subject | Expected Bucket |
|--------|---------|----------------|
| noreply@github.com | "[repo] New issue: Fix bug" | NOISE |
| notifications@slack.com | "New message in #general" | NOISE |
| noreply@google.com | "Security alert: New sign-in" | REVIEW (security gate) |
| noreply@bank.com | "Your verification code" | REVIEW (security gate) |
| boss@company.com | "RE: Q4 budget review" | check_content (UNDECIDED) |
| newsletter@techcrunch.com | "Weekly Digest: AI News" | REFERENCE |

---

## Security Gate Tests

| Subject | Expected Action |
|---------|----------------|
| "Password reset requested" | Pull from NOISE → REVIEW |
| "Your order has shipped" | Stay as REFERENCE |
| "Unusual sign-in activity" | Pull from NOISE → REVIEW |
| "Weekly newsletter digest" | Stay as REFERENCE |
| "Your 2FA code is 123456" | Pull from NOISE → REVIEW |

---

## Session Cache Tests

| Scenario | Expected Behavior |
|----------|------------------|
| Cache file exists, valid (<1h old) | Use cached labels/filters/tier. Skip Phase 0 discovery |
| Cache file exists, expired (>1h old) | Ignore cache. Run full Phase 0 discovery |
| Cache file missing | Run full Phase 0 discovery |
| After `gmail_create_filter` write op | Invalidate cache. Re-fetch on next mode |
| After `gmail_batch_modify_emails` write op | Invalidate cache. Re-fetch on next mode |
| After `gmail_get_or_create_label` write op | Invalidate cache. Re-fetch on next mode |

---

## Bankruptcy Alert Level Tests

| Current Count | Baseline | Expected Level | Expected Action |
|--------------|----------|----------------|-----------------|
| 100 | 100 | NORMAL | Continue daily routine |
| 140 | 100 | YELLOW | Surface warning; suggest extra triage |
| 170 | 100 | ORANGE | Aggressive triage + filter creation |
| 250 | 100 | RED | Full bankruptcy protocol |
| 5000 | (new user, no baseline) | Use default 500 | RED — trigger bankruptcy |
| 12000 | 10000 | YELLOW (20% above) | Surface warning |
| 50000+ | any | RED (absolute floor) | Full bankruptcy protocol |

---

## Auto-Scan Tests

| Scenario | Expected Behavior |
|----------|------------------|
| Empty invocation, fresh account (no cache) | Run full Phase 0 + 6 analysis queries in mega-wave, present Auto-Scan Report |
| Empty invocation, warm cache (<1h) | Use cached Phase 0, run 6 analysis queries only, present Auto-Scan Report |
| Auto-Scan report shows 0 unread | Recommend: analytics or audit (no triage needed) |
| Auto-Scan report shows 500+ unread | Recommend: triage as #1 priority |
| Auto-Scan report shows 50+ newsletters | Recommend: newsletters mode |
| Auto-Scan report shows RED bankruptcy | Recommend: inbox-zero with bankruptcy recovery |
| User replies "all" to Auto-Scan | Chain top 3 recommendations as combo mode |
| User replies "menu" to Auto-Scan | Show full dispatch table |
| User replies number (e.g., "2") | Execute the corresponding recommended mode |
