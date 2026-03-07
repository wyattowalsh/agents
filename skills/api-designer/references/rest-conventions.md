# REST API Conventions

Best practices for RESTful API design. Source of truth for Design, Spec, and Review modes.

## Contents

1. [Resource Naming](#resource-naming)
2. [HTTP Methods](#http-methods)
3. [Status Codes](#status-codes)
4. [Request/Response Patterns](#requestresponse-patterns)
5. [Pagination](#pagination)
6. [Filtering and Sorting](#filtering-and-sorting)
7. [Error Handling](#error-handling)
8. [Authentication](#authentication)
9. [Rate Limiting](#rate-limiting)
10. [HATEOAS](#hateoas)

---

## Resource Naming

- Use plural nouns: `/users`, `/orders`, `/products`
- Use kebab-case: `/user-profiles`, not `/userProfiles` or `/user_profiles`
- Nest for relationships: `/users/{id}/orders`
- Max 3 levels of nesting; flatten beyond that with query params
- No verbs in URLs: `/users/{id}/activate` is acceptable only for non-CRUD actions
- Use path params for identity: `/users/{userId}`
- Use query params for filtering: `/users?role=admin`

## HTTP Methods

| Method | Semantics | Idempotent | Safe | Request Body |
|--------|-----------|------------|------|--------------|
| GET | Read resource(s) | Yes | Yes | No |
| POST | Create resource | No | No | Yes |
| PUT | Full replace | Yes | No | Yes |
| PATCH | Partial update | No | No | Yes |
| DELETE | Remove resource | Yes | No | No |
| HEAD | Metadata only | Yes | Yes | No |
| OPTIONS | Available methods | Yes | Yes | No |

- PUT replaces the entire resource; PATCH updates specific fields
- POST to collection creates; POST to resource triggers action
- DELETE should be idempotent: deleting twice returns 204 or 404

## Status Codes

### Success (2xx)

| Code | Use |
|------|-----|
| 200 | GET success, PUT/PATCH success with body |
| 201 | POST created (include Location header) |
| 202 | Accepted for async processing |
| 204 | DELETE success, PUT/PATCH success with no body |

### Client Error (4xx)

| Code | Use |
|------|-----|
| 400 | Malformed request syntax or invalid parameters |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 405 | Method not allowed on this resource |
| 409 | Conflict (duplicate, version mismatch) |
| 422 | Semantically invalid (valid syntax, bad values) |
| 429 | Rate limit exceeded |

### Server Error (5xx)

| Code | Use |
|------|-----|
| 500 | Unexpected server error |
| 502 | Bad gateway (upstream failure) |
| 503 | Service unavailable (overload, maintenance) |
| 504 | Gateway timeout |

## Request/Response Patterns

### Request Body

```json
{
  "name": "string (required)",
  "email": "string (required, format: email)",
  "role": "string (optional, enum: [admin, user, viewer])"
}
```

### Success Response Envelope

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO 8601"
  }
}
```

### Collection Response

```json
{
  "data": [ ... ],
  "meta": {
    "total": 150,
    "page": 2,
    "per_page": 20
  },
  "links": {
    "self": "/users?page=2",
    "next": "/users?page=3",
    "prev": "/users?page=1"
  }
}
```

## Pagination

### Cursor-Based (preferred for large/real-time datasets)

```
GET /events?cursor=eyJpZCI6MTIzfQ&limit=20
```

Response includes `next_cursor` in meta. No total count (expensive).

### Offset-Based (acceptable for small, stable datasets)

```
GET /users?page=2&per_page=20
```

Response includes `total`, `page`, `per_page` in meta plus `links`.

### Rules

- Default page size: 20. Max: 100.
- Always include pagination on list endpoints
- Return empty array (not null) for empty results
- Include `links` object with `self`, `next`, `prev` (null if N/A)

## Filtering and Sorting

### Filtering

```
GET /users?role=admin&status=active
GET /orders?created_after=2024-01-01&total_gte=100
```

- Use field names directly for exact match
- Suffix operators: `_gte`, `_lte`, `_gt`, `_lt`, `_ne`, `_like`
- Multiple values: `?status=active,pending` (comma-separated)

### Sorting

```
GET /users?sort=created_at&order=desc
GET /users?sort=-created_at,name
```

- Prefix `-` for descending, no prefix for ascending
- Multiple sort fields comma-separated

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable summary",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address"
      }
    ],
    "request_id": "uuid"
  }
}
```

### Rules

- Every error response includes `code` (machine-readable) and `message` (human-readable)
- Validation errors include `details` array with per-field errors
- Include `request_id` for traceability
- Never expose stack traces or internal paths in production

## Authentication

| Pattern | Use Case | Header |
|---------|----------|--------|
| API Key | Server-to-server, simple integrations | `X-API-Key: <key>` |
| Bearer Token (JWT) | User-facing APIs, mobile/SPA | `Authorization: Bearer <token>` |
| OAuth 2.0 | Third-party integrations, delegated access | `Authorization: Bearer <token>` |
| Basic Auth | Internal/dev only | `Authorization: Basic <base64>` |

- Use HTTPS for all authenticated endpoints
- Include auth requirements in OpenAPI `securitySchemes`
- Return 401 for missing auth, 403 for insufficient permissions

## Rate Limiting

### Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1609459200
Retry-After: 60
```

### Strategy

- Per-endpoint limits for sensitive operations (login, create)
- Per-API-key global limits
- Return 429 with `Retry-After` header
- Document limits in OpenAPI spec `x-ratelimit` extension

## HATEOAS

Include navigational links for related resources:

```json
{
  "data": {
    "id": "123",
    "name": "Order #123",
    "links": {
      "self": "/orders/123",
      "items": "/orders/123/items",
      "customer": "/customers/456"
    }
  }
}
```

Optional but recommended for public APIs. Reduces client coupling to URL structure.
