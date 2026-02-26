## Gmail MCP Tool Reference

> All 19 Gmail MCP tools available in this skill, organized by category. Use this reference when selecting tools for a workflow.

### Email Management (6 tools)

**`gmail_search_emails`**
Search emails using Gmail search syntax.
- Params: `query` (string), `maxResults` (int, default 10)
- Returns: list of `{id, threadId, subject, from, date, snippet}`
- Note: Primary discovery tool. Set `maxResults` explicitly; default is only 10.

**`gmail_read_email`**
Fetch full email content for a single message.
- Params: `messageId` (string)
- Returns: full message with headers, body, and attachment metadata
- Note: Use after `gmail_search_emails` to inspect content before acting.

**`gmail_modify_email`**
Add or remove labels on a single email.
- Params: `messageId` (string), `addLabelIds` (string[]), `removeLabelIds` (string[])
- Returns: updated message object
- Note: For single-email label changes only. Use `gmail_batch_modify_emails` for multiple.

**`gmail_delete_email`**
Permanently delete a single email.
- Params: `messageId` (string)
- Returns: empty 204
- Note: IRREVERSIBLE. Show destructive warning template and confirm before calling.

**`gmail_send_email`**
Send an email.
- Params: `to`, `subject`, `body`, optional `cc`, `bcc`, `replyTo`, `attachments`
- Returns: sent message id
- Note: Out of scope for inbox management workflows. Do not use during triage.

**`gmail_draft_email`**
Create a draft email.
- Note: NOT included in allowed-tools. Out of scope for this skill.

---

### Batch Operations (2 tools)

**`gmail_batch_modify_emails`**
Apply label changes to multiple emails in one call.
- Params: `messageIds` (string[], up to 1000), `addLabelIds` (string[]), `removeLabelIds` (string[]), `batchSize` (int, default 50)
- Returns: `{success: count, failed: []}`
- Note: Prefer over a loop of `gmail_modify_email`. Max 1000 messages per call; split larger sets.

**`gmail_batch_delete_emails`**
Delete multiple emails in one call.
- Params: `messageIds` (string[], up to 1000), `batchSize` (int, default 50)
- Returns: `{success: count, failed: []}`
- Note: IRREVERSIBLE. Always show the destructive warning template and get explicit confirmation before calling.

---

### Label Management (5 tools)

**`gmail_list_email_labels`**
Get all labels in the account.
- Params: none
- Returns: `[{id, name, type, messagesTotal, messagesUnread}]`
- Note: Always call in Phase 0 discovery to map existing labels before any label operations.

**`gmail_create_label`**
Create a new label.
- Params: `name` (string), `labelListVisibility` (show/hide), `messageListVisibility` (show/hide)
- Returns: created label with `id`
- Note: Use `gmail_get_or_create_label` instead for idempotent creation.

**`gmail_get_or_create_label`**
Get an existing label or create it if absent.
- Params: `name` (string)
- Returns: label object (existing or newly created)
- Note: Preferred for workflow operations where the label may or may not already exist.

**`gmail_update_label`**
Rename a label or change its visibility.
- Params: `labelId` (string), optional `name`, `labelListVisibility`, `messageListVisibility`
- Returns: updated label object
- Note: Use when consolidating or renaming labels. Move emails to the target label first.

**`gmail_delete_label`**
Delete a label.
- Params: `labelId` (string)
- Returns: empty 204
- Note: Safe — emails lose the label but are NOT deleted. Use after moving emails away.

---

### Filter Management (4 tools)

**`gmail_list_filters`**
Get all filters in the account.
- Params: none
- Returns: `[{id, criteria, action}]`
- Note: Always call in Phase 0 and before creating new filters for conflict detection.

**`gmail_get_filter`**
Get details for a single filter.
- Params: `filterId` (string)
- Returns: full filter details with criteria and action
- Note: `gmail_list_filters` covers most needs; use this for targeted inspection.

**`gmail_create_filter`**
Create a custom filter with arbitrary criteria.
- Params: `criteria` (`{from, to, subject, hasWords, doesNotHaveWords, hasAttachment, excludeChats}`), `action` (`{addLabelIds, removeLabelIds, forward, markRead, markImportant, delete}`)
- Returns: created filter object
- Note: Use for patterns not covered by templates. Prefer `gmail_create_filter_from_template` for standard cases.

**`gmail_create_filter_from_template`**
Create a filter from a preset template.
- Params: `template` (one of `fromSender` | `withSubject` | `withAttachments` | `largeEmails` | `containingText` | `mailingList`), `templateParams` (varies by template), `action`
- Returns: created filter object
- Note: Faster than custom for standard patterns. Check existing filters first to avoid duplicates.

**`gmail_delete_filter`**
Delete a filter.
- Params: `filterId` (string)
- Returns: empty 204
- Note: Use when consolidating overlapping filters or removing stale rules.

---

## System Limits

| Limit | Value | Impact |
|-------|-------|--------|
| Batch size default | 50 | Configurable up to 1000 |
| Max batch per call | 1000 emails | Split large operations into chunks |
| Filter maximum | 500 filters | Consolidate with OR logic when approaching limit |
| Search results default | 10 | Set `maxResults` explicitly for broader scans |
| Search results max | ~500 | Use date ranges to paginate large datasets |

---

## Tool Selection Guide

| Goal | Preferred Tool |
|------|----------------|
| Discover inbox state | `gmail_search_emails` + `gmail_list_email_labels` + `gmail_list_filters` |
| Read one email fully | `gmail_read_email` |
| Apply labels to many emails | `gmail_batch_modify_emails` |
| Create a standard filter | `gmail_create_filter_from_template` |
| Create a custom filter | `gmail_create_filter` |
| Rename or merge a label | `gmail_update_label` → move emails → `gmail_delete_label` |
| Idempotent label creation | `gmail_get_or_create_label` |

---

## Error Codes

| Error | Cause | Recovery |
|-------|-------|----------|
| 401 Unauthorized | Token expired | Re-authenticate the Gmail MCP server |
| 403 Forbidden | Insufficient OAuth scope | Check MCP server permission configuration |
| 404 Not Found | Message, label, or filter already deleted | Skip and continue processing |
| 429 Rate Limited | Too many requests | Reduce batch size; retry after 1 minute |
| 500 Server Error | Gmail API outage | Retry with exponential backoff |
