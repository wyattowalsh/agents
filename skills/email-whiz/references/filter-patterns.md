# Filter Patterns

> Gmail search operators, filter templates, pattern detection, and auto-rule generation for the email-whiz skill.

---

## Gmail Search Operators

### Sender and Recipient
```
from:user@example.com              exact sender
from:@domain.com                   any sender at domain
from:(@domain.com OR @other.com)   multiple domains
to:me                              sent directly to you (not CC)
```

### Subject
```
subject:invoice                    subject contains word
subject:"monthly report"           exact phrase
subject:(invoice OR receipt)       either word
-subject:unsubscribe               does NOT contain word
```

### Attachments and Size
```
has:attachment                     any attachment
filename:pdf                       PDF attachment
larger:5M                          email > 5 MB
smaller:1M                         email < 1 MB
```

### Dates and Status
```
newer_than:7d                      last 7 days
older_than:30d                     older than 30 days
after:2024/01/01                   after specific date
is:unread / is:read / is:starred   status flags
in:inbox / in:sent / in:spam       location
```

### Combining Operators
```
from:github.com subject:merged     AND (implicit)
from:github.com OR from:gitlab.com OR (explicit)
from:github.com -subject:security  AND NOT
(from:github.com OR from:gitlab.com) subject:PR   mixed
```

---

## Filter Templates

Ten ready-to-use configurations. Replace `{}` placeholders before applying.

| # | Name | criteria | action |
|---|------|----------|--------|
| 1 | Notification Silencer | `from: "notifications@{service}.com"` | label + skip inbox + markRead |
| 2 | GitHub Activity Router | `from: "@github.com"` | label + skip inbox |
| 3 | Invoice Collector | `hasWords: "invoice OR receipt OR billing"` | label only |
| 4 | Newsletter Quarantine | `hasWords: "unsubscribe"` | label + skip inbox |
| 5 | CI/CD Alert Filter | `from: "{ci}@{domain}", subject: "build OR deploy"` | label + skip inbox + markRead |
| 6 | Mailing List Router | `to: "{list}@{domain}"` | label + skip inbox |
| 7 | Large Attachment Tagger | `hasAttachment: true, hasWords: "larger:5M"` | label only |
| 8 | VIP Priority Booster | `from: "{vip@domain.com}"` | markImportant: true |
| 9 | Automated Domain Silencer | `from: "noreply@ OR no-reply@ OR donotreply@"` | label + skip inbox + markRead |
| 10 | Subject Prefix Router | `subject: "[{PREFIX}]"` | label + skip inbox |

---

## Pattern Detection

### Sender Clustering
```
1. Search: in:inbox older_than:30d → group results by sender address and domain
2. For each sender with count >= 5:
   - reply_rate = in:sent to:{sender} count / received count × 100
3. Flag: count >= 10 AND reply_rate < 10% → filter candidate
4. Cluster by domain when ≥3 addresses share a domain
5. Present: volume DESC, reply_rate ASC
```

### Subject Pattern Mining
```
1. Collect subjects from: in:inbox newer_than:90d
2. Extract repeating token structures:
   - Bracket prefixes: [WORD], [WORD-NNN]
   - Hash sequences: #NNN, PR #NNN, Invoice NNN
   - ALL CAPS prefixes: ALERT, URGENT, FYI
3. If pattern_count >= 5: propose subject:"{pattern}" → filter
```

### Mailing List Detection
```
Signals (check in order of reliability):
1. List-ID header present → definitive mailing list
2. List-Unsubscribe header present → automated list
3. Precedence: bulk header → bulk sender
4. To/CC does not contain your address directly → list address
Action: label + skip inbox; do NOT markRead (content worth scanning)
```

---

## Conflict Detection

Run before creating any filter to avoid rule collisions.

```
1. Call gmail_list_filters to get all existing filters
2. For each proposed filter:
   a. FROM overlap: does existing filter match same sender?
   b. SUBJECT overlap: do same keywords appear in another filter?
   c. ACTION conflict: one removes INBOX while another adds INBOX → conflict
3. Resolution:
   - Exact duplicate → skip, report "already covered"
   - Partial overlap → warn, require confirmation
   - Action conflict → surface both, ask which to keep
4. Re-fetch gmail_list_filters after creation to verify the new filter appears
```

---

## Gmail Filter Limitations

| Limit | Value | Workaround |
|-------|-------|------------|
| Max filters per account | 500 | Consolidate with OR: `from:(a@x.com OR b@x.com)` |
| Regex support | None | Partial string matching only |
| Retroactive application | New mail only | Batch-modify existing emails separately |
| NOT on from: field | Unsupported | Use `doesNotHaveWords` for body/subject only |
| Filter ordering | Not guaranteed | Design filters to avoid conflicting actions |

---

## Testing Filters Before Creating

```
1. Run criteria as a search query via gmail_search_emails (maxResults: 20)
2. Inspect sample: verify matches, check for false positives
3. Estimate volume: if 20/20 are matches, search for total count
4. Confirm action: if removeLabelIds:["INBOX"], verify no important emails in sample
5. Create filter (template or custom)
6. Verify: re-call gmail_list_filters and confirm new filter ID present
```

---

## Template-Based Filter Creation

Use `gmail_create_filter_from_template` for standard patterns — faster and less error-prone than custom filters.

```
template: "fromSender"
templateParams: { senderEmail: "notifications@github.com" }
action: { addLabelIds: ["Label_xxx"], removeLabelIds: ["INBOX"], markRead: true }

template: "mailingList"
templateParams: { listIdentifier: "dev@company.com" }
action: { addLabelIds: ["Label_xxx"], removeLabelIds: ["INBOX"] }

template: "withSubject"
templateParams: { subject: "invoice" }
action: { addLabelIds: ["Label_xxx"], removeLabelIds: ["INBOX"] }

template: "withAttachments"
templateParams: { hasAttachment: true }
action: { addLabelIds: ["Label_xxx"] }
```

Use `gmail_create_filter` (custom) instead when:
- Combining multiple criteria (e.g., `from:` AND `subject:`)
- Applying NOT conditions via `doesNotHaveWords`
- Complex boolean logic not covered by a template

---

## Auto-Rule Detection

Algorithms used by the `auto-rules` mode to surface filter candidates without manual input.

### Sender Cluster Algorithm
```
1. Search: in:inbox after:{90d_ago} (sample up to 500 emails)
2. For each sender:
   - volume       = count of emails from sender in sample
   - replied      = gmail_search_emails(query: "in:sent to:{sender}").count
   - reply_rate   = replied / volume × 100
3. Identify candidates:
   - volume >= 10 AND reply_rate < 10%   → filter (skip inbox)
   - volume >= 5  AND automated domain   → filter (skip inbox + label)
   - volume >= 20 AND reply_rate == 0    → offer delete or filter
4. Rank: volume DESC, reply_rate ASC
5. Assign confidence:
   HIGH   (>80%):   volume >= 20, reply_rate < 5%
   MEDIUM (50-80%): volume >= 10, reply_rate < 15%
   LOW    (<50%):   borderline — volume < 10 or reply_rate 15-30%
```

### Subject Pattern Mining Algorithm
```
1. Collect subjects: in:inbox newer_than:90d (up to 500)
2. Find repeating structures:
   - Bracket prefixes:   [JIRA-123], [company-name]
   - Hash sequences:     PR #456, Issue #789, Order #001
   - Word+number combos: Invoice 1234, Ticket 5678
3. For each pattern with occurrence_count >= 5:
   - Compute pattern_reply_rate (in:sent referencing pattern)
   - Propose: subject:"{pattern}" → label + skip inbox
   - If pattern_reply_rate < 5%: also propose markRead: true
4. Present ranked by occurrence_count DESC
```

### Confidence Score to Action Mapping
```
HIGH (>80%)
→ Offer to create immediately with one confirmation prompt
→ Show sender, volume, reply_rate, proposed action
→ Default: accept on Enter

MEDIUM (50-80%)
→ Present as numbered list for per-item approval
→ Allow bulk: "approve all MEDIUM"

LOW (<50%)
→ Display as suggestions only — do NOT create without explicit request
→ Explain low confidence (low volume or borderline reply rate)
```

---

## Auto-Rule Learning Loop

Re-analyze effectiveness after filters are created to refine coverage over time.

### Week 2 Check
```
For each auto-rule filter:
- hit_count  = gmail_search_emails(query: "{criteria} newer_than:14d").count
- miss_count = gmail_search_emails(query: "in:inbox from:{sender} newer_than:14d").count
- miss_rate  = miss_count / (hit_count + miss_count) × 100

If miss_rate > 20%:     expand criteria (add related addresses or subject variants)
If false_pos_rate > 5%: narrow criteria (tighten from: or add doesNotHaveWords)
Propose updated filter and confirm before replacing the existing rule.
```

### Month 1 Check
```
For each auto-rule filter:
- 30d_hits = gmail_search_emails(query: "{criteria} newer_than:30d").count
- If 30d_hits == 0: mark stale → offer to delete
- If 30d_hits >= 1: keep and log effectiveness

Re-run sender cluster algorithm on past 30d:
- Compare against existing filters
- Surface net-new candidates for another auto-rules pass

Report: filters created / active / stale / new candidates found
```

### Re-Analysis Triggers
```
- 50+ new unique senders appear in inbox since last analysis
- User reports inbox volume growing week-over-week
- User explicitly invokes /email-whiz auto-rules again
- Month 1 check identifies 3+ new candidate clusters
- Any filter's false positive rate exceeds 5%
```
