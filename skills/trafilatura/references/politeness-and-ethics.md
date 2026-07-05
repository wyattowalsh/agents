# Politeness and Ethics

## Scraping etiquette

- Respect robots.txt and site terms.
- Trafilatura waits between requests by default — do not disable politeness without user intent.
- Avoid hammering a single domain with large batch jobs.

## Batch approval gate

Before `batch` or `local` modes:

1. State URL count or directory size.
2. Confirm output under `$HOME/Downloads/trafilatura/` (not the agents repo).
3. Acknowledge rate limits and robots constraints.

## Refusals

Refuse requests to:

- Bypass paywalls, DRM, or membership gates without authorization
- Bulk-scrape sites when the user has not approved scope
- Commit cookies, credentials, or `settings.cfg` secrets to the repo
- Use crawl output as a substitute for live web search (`research` skill)

## Cookies and config

User-owned `settings.cfg` may set `COOKIE=...` for authorized sessions. Reference path only in commands — never paste secret values in chat or commits.