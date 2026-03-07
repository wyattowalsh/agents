# API Versioning Strategies

Versioning approaches, deprecation patterns, and backward compatibility checklist. Source of truth for Version and Compat modes.

## Contents

1. [Versioning Approaches](#versioning-approaches)
2. [Deprecation Patterns](#deprecation-patterns)
3. [Backward Compatibility Checklist](#backward-compatibility-checklist)
4. [Migration Guide Template](#migration-guide-template)

---

## Versioning Approaches

### URL Path Versioning

```
GET /api/v1/users
GET /api/v2/users
```

| Pros | Cons |
|------|------|
| Explicit, easy to understand | URL changes break bookmarks and caches |
| Simple routing and documentation | Version proliferation across many resources |
| Easy to run versions side-by-side | Forces full API versioning even for small changes |

**Best for:** Public APIs, APIs with major structural changes between versions.

### Header Versioning

```
GET /api/users
Accept: application/vnd.myapi.v2+json
```

Or custom header:

```
GET /api/users
X-API-Version: 2
```

| Pros | Cons |
|------|------|
| Clean URLs that never change | Less visible/discoverable |
| Can version individual resources | Harder to test in browser |
| Supports content negotiation | Requires header awareness in clients |

**Best for:** Internal APIs, APIs that rarely introduce breaking changes.

### Query Parameter Versioning

```
GET /api/users?version=2
```

| Pros | Cons |
|------|------|
| Easy to add and test | Pollutes query string |
| No URL structure changes | Can conflict with other query params |
| Optional (default to latest or stable) | Less semantically clean |

**Best for:** Simple APIs, gradual migration scenarios.

### Decision Matrix

| Factor | URL Path | Header | Query Param |
|--------|----------|--------|-------------|
| Discoverability | High | Low | Medium |
| Caching | Natural | Custom Vary | Custom Vary |
| Documentation | Simple | Complex | Simple |
| Client complexity | Low | Medium | Low |
| Granularity | Full API | Per-resource | Full API |

**Recommendation:** Default to URL path versioning unless there is a specific reason to prefer header or query param versioning. For internal APIs with infrequent breaking changes, header versioning provides cleaner URLs.

## Deprecation Patterns

### Timeline

| Phase | Duration | Action |
|-------|----------|--------|
| Announce | Day 0 | Add `Deprecation` header, update docs, notify consumers |
| Sunset | 3-12 months | Return `Sunset` header with date, log usage metrics |
| Remove | After sunset | Return 410 Gone with migration guide URL |

### HTTP Headers

```
Deprecation: true
Sunset: Sat, 01 Jun 2025 00:00:00 GMT
Link: <https://api.example.com/docs/migration-v2>; rel="successor-version"
```

### Response Warning

```json
{
  "data": { ... },
  "warnings": [{
    "code": "DEPRECATED_ENDPOINT",
    "message": "This endpoint is deprecated. Use /v2/users instead. Sunset: 2025-06-01."
  }]
}
```

### Rules

- Never remove endpoints without a deprecation period
- Minimum 3 months for public APIs, 1 month for internal
- Monitor usage of deprecated endpoints before removal
- Provide a migration guide for every deprecated endpoint
- Log deprecation warning responses for consumer tracking

## Backward Compatibility Checklist

### Non-Breaking (Safe) Changes

- Adding new endpoints
- Adding optional request parameters
- Adding new response fields
- Adding new enum values (if clients ignore unknown)
- Adding new HTTP methods to existing resources
- Relaxing validation constraints (e.g., longer max length)
- Adding new error codes

### Breaking Changes

- Removing endpoints or methods
- Removing or renaming response fields
- Removing or renaming request parameters
- Changing field types (string to integer)
- Adding required request parameters
- Tightening validation constraints
- Changing URL structure
- Changing authentication mechanism
- Changing error response format
- Changing pagination format
- Removing enum values

### Gray Area (Context-Dependent)

- Changing default values (may affect clients relying on defaults)
- Reordering response fields (breaks clients parsing by position)
- Adding required fields to nested objects in responses
- Changing rate limits (breaks clients at capacity)

## Migration Guide Template

```markdown
# Migration Guide: v1 to v2

## Overview
Summary of why v2 exists and key improvements.

## Timeline
- v2 available: YYYY-MM-DD
- v1 deprecated: YYYY-MM-DD
- v1 sunset: YYYY-MM-DD

## Breaking Changes

### 1. [Change description]
**Before (v1):**
[code example]

**After (v2):**
[code example]

**Migration steps:**
1. Step one
2. Step two

## New Features in v2
- Feature 1
- Feature 2

## Support
Contact api-support@example.com for migration assistance.
```
