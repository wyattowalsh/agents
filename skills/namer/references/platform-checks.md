# Platform Checks

Per-platform availability check methods. Read during Phase 2 (availability sweep).

## Contents

- [Check Methods Overview](#check-methods-overview)
- [Domain Checking](#domain-checking)
- [Dev Registry Checks](#dev-registry-checks)
- [Social Platform Checks](#social-platform-checks)
- [Conflict & Distinctiveness Checks](#conflict--distinctiveness-checks)
- [Confidence Levels](#confidence-levels)
- [Error Handling](#error-handling)
- [Rate Limit Summary](#rate-limit-summary)

---

## Check Methods Overview

Three detection strategies (derived from the Sherlock project):

| Strategy | Mechanism | Example |
|----------|-----------|---------|
| **Status code** | HTTP 404 = available, 200 = taken | GitHub API, npm registry, PyPI |
| **Message** | Search response body for an error/absence string | Reddit username check (returns `true`/`false`) |
| **Response URL** | Redirect to a generic/default page = available | Bluesky handle resolution, some social platforms |

**Always prefer status-code checks.** They are deterministic. Message and redirect checks carry parsing risk.

---

## Domain Checking

### RDAP (Primary — Free, No API Key)

RDAP is the replacement for WHOIS. Returns structured JSON. No authentication required.

#### .com and .net

```
GET https://rdap.verisign.com/com/v1/domain/{name}.com
```

| Response | Meaning |
|----------|---------|
| `200` with JSON body | Registered (taken) |
| `404` with `"errorCode": 404` | Not registered (available) |
| `429` | Rate limited — back off 30s |

Extract registrar from `200` response: `entities[0].vcardArray` or `events[?eventAction=='registration'].eventDate`.

#### .net

```
GET https://rdap.verisign.com/net/v1/domain/{name}.net
```

Same response interpretation as .com.

#### .org

```
GET https://rdap.org/domain/{name}.org
```

Or use the PIR RDAP server:

```
GET https://rdap.publicinterestregistry.org/rdap/domain/{name}.org
```

Same 200/404 interpretation.

#### Other TLDs — IANA Bootstrap

1. Fetch the RDAP bootstrap file:
   ```
   GET https://data.iana.org/rdap/dns.json
   ```
2. Find the service entry matching the target TLD.
3. Use the base URL from that entry:
   ```
   GET {base_url}/domain/{name}.{tld}
   ```

**Common bootstrap mappings:**

| TLD | RDAP Server |
|-----|-------------|
| `.com`, `.net` | `https://rdap.verisign.com/{tld}/v1/` |
| `.org` | `https://rdap.publicinterestregistry.org/rdap/` |
| `.info` | `https://rdap.afilias.net/rdap/info/` |
| `.io` | No official RDAP — use Brave Search fallback |
| `.dev` | `https://rdap.nic.google/` |
| `.app` | `https://rdap.nic.google/` |
| `.ai` | No official RDAP — use Brave Search fallback |
| `.co` | `https://rdap.nic.co/` |

#### .dev and .app (Google Registry)

```
GET https://rdap.nic.google/domain/{name}.dev
GET https://rdap.nic.google/domain/{name}.app
```

Same 200/404 interpretation.

### Brave Search Fallback

Use when RDAP is unavailable for a TLD (`.io`, `.ai`, etc.) or to cross-check RDAP results.

```
brave_web_search "{name}.{tld}"
```

| Result | Interpretation |
|--------|----------------|
| Domain appears in results with active content | Registered and active |
| Domain appears but results show parking page language | Registered but parked — mark ⚠️ |
| Domain does not appear in results | Likely available — mark ❓ (not confirmed) |

### Domain Pricing

Query pattern for top candidates:

```
brave_web_search "{name}.{tld} domain price register"
```

**Typical price ranges** (fallback when search yields no pricing):

| TLD | New Registration | Renewal |
|-----|-----------------|---------|
| `.com` | $10-15/yr | $10-15/yr |
| `.dev` | $12-16/yr | $12-16/yr |
| `.io` | $30-50/yr | $30-50/yr |
| `.ai` | $50-90/yr | $50-90/yr |
| `.app` | $12-16/yr | $12-16/yr |
| `.co` | $25-35/yr | $25-35/yr |
| `.org` | $10-12/yr | $10-12/yr |

### Parked Domain Detection

Signals that a domain is registered but parked (not actively used):

| Signal | Weight |
|--------|--------|
| Page title contains "is for sale", "buy this domain", "parked" | Strong |
| Page served by Sedo, Afternic, GoDaddy parking, Dan.com | Strong |
| Single-page site with ads and no original content | Moderate |
| DNS resolves but returns HTTP 403 or generic hosting page | Moderate |
| MX records exist but no web content | Weak — may be email-only |

Mark parked domains as **⚠️ parked/inactive** — they are purchasable but at premium prices.

---

## Dev Registry Checks

Direct API checks. High accuracy — binary available/taken.

### GitHub

```
GET https://api.github.com/users/{name}
```

| Response | Meaning |
|----------|---------|
| `200` | Taken (user or org exists) |
| `404` | Available |

**Naming rules:** 1-39 chars, alphanumeric + hyphens, no leading/trailing hyphen, no consecutive hyphens.

**Rate limit:** 60 requests/hour unauthenticated. Include `User-Agent` header.

Also check organization namespace:

```
GET https://api.github.com/orgs/{name}
```

A name can be taken as a user but available as an org, or vice versa. Both share the same namespace — if either returns 200, the name is taken.

### npm

```
GET https://registry.npmjs.org/{name}
```

| Response | Meaning |
|----------|---------|
| `200` with package JSON | Taken |
| `404` | Available |

**Naming rules:**
- Lowercase only (no uppercase)
- Max 214 characters
- Cannot start with `.` or `_`
- No spaces
- Cannot match Node.js core module names (`fs`, `path`, `http`, etc.)
- Scoped packages: `@scope/name` — check both scope and package name

**Note:** npm has a "security hold" mechanism. A 404 does not guarantee the name is registrable — previously unpublished packages may be held. Mark as ✅ but note this caveat.

### PyPI

```
GET https://pypi.org/pypi/{name}/json
```

| Response | Meaning |
|----------|---------|
| `200` with package JSON | Taken |
| `404` | Available |

**PEP 503 normalization:** PyPI normalizes names before comparison. All of these are equivalent:
- `my-package`, `my_package`, `My.Package`, `MY--PACKAGE`

Normalization rule: lowercase, replace any run of `[-_.]+` with a single `-`.

Always normalize before checking. If `my-package` is taken, `my_package` is also taken.

### Crates.io (Rust)

```
GET https://crates.io/api/v1/crates/{name}
```

| Response | Meaning |
|----------|---------|
| `200` with crate JSON | Taken |
| `404` | Available |

**Naming rules:**
- ASCII alphanumeric + `-` + `_`
- Must start with a letter
- Max 64 characters
- Cannot be a Rust keyword

**Required header:** `User-Agent: namer-skill (https://github.com/user/agents)` — Crates.io blocks requests without a User-Agent.

### Homebrew

No direct API. Use search heuristic:

```
brave_web_search "homebrew formula {name} site:formulae.brew.sh"
```

| Result | Interpretation |
|--------|----------------|
| Formula page found on formulae.brew.sh | Taken — formula exists |
| No relevant results | Likely available — mark ⚠️ (cask names may differ) |

Also check casks:

```
brave_web_search "homebrew cask {name} site:formulae.brew.sh"
```

### Go Modules (--thorough only)

```
brave_web_search "pkg.go.dev {name}"
```

Go modules use full import paths (`github.com/user/name`), so direct name collision is rare. Check for popular packages that use the short name.

---

## Social Platform Checks

### Reddit

```
GET https://www.reddit.com/api/username_available.json?user={name}
```

| Response Body | Meaning |
|---------------|---------|
| `true` | Available |
| `false` | Taken |

**Naming rules:** 3-20 characters, alphanumeric + underscores + hyphens.

**Also check subreddits:**

```
GET https://www.reddit.com/r/{name}/about.json
```

| Response | Meaning |
|----------|---------|
| `200` with subreddit data | Subreddit exists |
| `404` or redirect to search | Available |

### Bluesky

```
GET https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle={name}.bsky.social
```

| Response | Meaning |
|----------|---------|
| `200` with `{"did": "..."}` | Taken |
| `400` with error | Available |

**Naming rules:** 1-253 chars for full handle; the `{name}` portion before `.bsky.social` must be valid DNS label (alphanumeric + hyphens, no leading/trailing hyphen).

### Twitter / X

No public API for availability. Use search heuristic:

```
brave_web_search "site:x.com/{name}"
```

| Result | Interpretation | Confidence |
|--------|----------------|------------|
| Profile page in results | Taken | ⚠️ Medium — could be suspended account |
| No results | Likely available | ⚠️ Medium — could be private or reserved |

**Naming rules:** 4-15 characters, alphanumeric + underscore only.

### YouTube

```
brave_web_search "site:youtube.com/@{name}"
```

| Result | Interpretation | Confidence |
|--------|----------------|------------|
| Channel page with `@{name}` handle | Taken | ⚠️ Medium |
| No results | Likely available | ⚠️ Medium |

### Instagram

```
brave_web_search "site:instagram.com/{name}"
```

| Result | Interpretation | Confidence |
|--------|----------------|------------|
| Profile page in results | Taken | ⚠️ Medium |
| No results | Likely available | ⚠️ Medium |

**Naming rules:** 1-30 chars, alphanumeric + periods + underscores.

### LinkedIn (Company Pages)

```
brave_web_search "site:linkedin.com/company/{name}"
```

| Result | Interpretation | Confidence |
|--------|----------------|------------|
| Company page in results | Taken | ⚠️ Medium |
| No results | Likely available | ⚠️ Medium |

### Mastodon

Use WebFinger protocol:

```
GET https://mastodon.social/.well-known/webfinger?resource=acct:{name}@mastodon.social
```

| Response | Meaning |
|----------|---------|
| `200` with JRD JSON | Taken on mastodon.social |
| `404` | Available on mastodon.social |

**Note:** Mastodon is federated. This only checks `mastodon.social`. Other instances may have the same handle. Mark as ⚠️ with instance qualifier.

---

## Conflict & Distinctiveness Checks

### Search Collision Volume

```
brave_web_search '"{name}" software'
```

| Result Count | Interpretation | Score Impact |
|--------------|----------------|--------------|
| 0-50 | Highly distinctive | Search distinctiveness: 9-10 |
| 51-500 | Moderately distinctive | Search distinctiveness: 6-8 |
| 501-5000 | Crowded — needs qualifier | Search distinctiveness: 3-5 |
| 5000+ | Generic — poor discoverability | Search distinctiveness: 0-2 |

Also check without quotes for broader collision:

```
brave_web_search "{name} software"
```

Compare quoted vs unquoted counts. High unquoted with low quoted = name is common words but not an established brand. Low risk.

### USPTO Trademark Search

```
brave_web_search "USPTO TESS trademark {name}"
```

Interpret results:

| Finding | Risk Level | Action |
|---------|-----------|--------|
| Active registration in same class (software = Class 9, SaaS = Class 42) | **High** | Disqualify or add risk warning |
| Active registration in unrelated class | **Low** | Note but do not disqualify |
| Dead/abandoned registration | **None** | Safe to use |
| No results | **None found** | Mark ❓ — absence of results is not proof of absence |

**--thorough mode only.** Skip for default runs to conserve search budget.

### Wikipedia Collision

```
brave_web_search "site:wikipedia.org {name}"
```

| Finding | Risk Level |
|---------|-----------|
| Wikipedia article about a product/brand with this name | **High** — dominated search results |
| Wikipedia article about an unrelated concept (e.g., mythology, science) | **Medium** — semantic interference |
| No Wikipedia article | **Low** |

---

## Confidence Levels

| Method | Confidence | Icon | Meaning |
|--------|------------|------|---------|
| Direct API (200/404) | High | ✅/❌ | Binary, deterministic result |
| Structured API (Reddit bool, Bluesky error) | High | ✅/❌ | Parsed from structured response |
| RDAP domain lookup | High | ✅/❌ | Authoritative registry data |
| Brave Search `site:` heuristic | Medium | ⚠️ | May miss private, suspended, or reserved handles |
| Brave Search general query | Low | ❓ | Suggestive only — requires manual verification |
| Inference from naming rules | Low | ❓ | Name may be valid but reserved by platform |

**Display rule:** Always show the confidence icon in availability matrices. Never upgrade ⚠️ or ❓ to ✅ without a direct API confirmation.

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| HTTP 429 | Rate limited | Mark ❓, note "rate limited — check manually", move to next candidate |
| HTTP 403 | Blocked / auth required | Mark ❓, note "access denied" |
| Timeout (>10s) | Network issue or slow API | Retry once after 5s. If still failing, mark ❓ |
| HTTP 5xx | Server error | Mark ❓, note "server error" |
| DNS resolution failure | Invalid endpoint or network down | Mark ❓ for all remaining checks on that platform |
| Unexpected JSON schema | API changed | Mark ❓, note "unexpected response format" |
| Empty response body | Edge case | Treat as ❓, do not assume available |

**Never fabricate availability data.** If a check fails for any reason, the result is ❓ unknown — never ✅ available.

---

## Rate Limit Summary

| Platform | Limit | Window | Auth Required | Strategy |
|----------|-------|--------|---------------|----------|
| RDAP (Verisign) | ~100 | Per minute | No | Batch with 100ms delay between requests |
| RDAP (Google) | ~50 | Per minute | No | Same as above |
| GitHub API | 60 | Per hour | No (60), Yes (5000) | Check all candidates in one burst, track remaining |
| npm Registry | ~300 | Per minute | No | No throttling needed for 25 candidates |
| PyPI | ~100 | Per minute | No | No throttling needed |
| Crates.io | 1 | Per second | No | Add 1s delay between requests |
| Reddit | ~60 | Per minute | No | Batch usernames, check subreddits separately |
| Bluesky | ~100 | Per minute | No | No throttling needed |
| Brave Search | Varies | Per plan | API key | Budget: ~30 searches per naming session |
| Mastodon (WebFinger) | ~300 | Per 5 min | No | No throttling needed |

**Budget allocation for 20 candidates (default mode):**

| Check Category | API Calls | Brave Searches |
|----------------|-----------|----------------|
| Domain (.com/.net RDAP) | 40 | 0 |
| Domain (other TLDs) | 0-20 | 5-10 |
| Dev registries (GH, npm, PyPI, Crates) | 80 | 0 |
| Social (Reddit, Bluesky) | 40 | 0 |
| Social (X, YT, IG, LinkedIn) | 0 | 8-12 |
| Conflict (search collision) | 0 | 5-10 |
| **Total** | **~160-180** | **~18-32** |

**Budget allocation for --thorough mode (25 candidates):**

| Check Category | API Calls | Brave Searches |
|----------------|-----------|----------------|
| All default checks (scaled) | ~225 | ~25-40 |
| Trademark (USPTO) | 0 | 5-10 |
| Wikipedia collision | 0 | 5-10 |
| Go modules | 0 | 5-10 |
| Homebrew | 0 | 5-10 |
| Domain pricing (top 5) | 0 | 5-10 |
| **Total** | **~225** | **~45-80** |
