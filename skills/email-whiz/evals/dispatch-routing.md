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
| _(empty)_ | Menu | Show all modes |

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
