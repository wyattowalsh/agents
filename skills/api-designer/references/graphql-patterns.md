# GraphQL Schema Design Patterns

Best practices for GraphQL API design. Source of truth for Design, Spec, and Review modes when protocol is GraphQL.

## Contents

1. [Schema Design](#schema-design)
2. [Query Patterns](#query-patterns)
3. [Mutation Patterns](#mutation-patterns)
4. [Error Handling](#error-handling)
5. [Pagination](#pagination)
6. [Authentication](#authentication)
7. [Performance](#performance)

---

## Schema Design

### Naming Conventions

- Types: PascalCase (`User`, `OrderItem`)
- Fields: camelCase (`firstName`, `createdAt`)
- Enums: SCREAMING_SNAKE_CASE values (`ACTIVE`, `IN_PROGRESS`)
- Mutations: verb + noun (`createUser`, `updateOrder`, `deleteProduct`)
- Queries: noun or noun phrase (`user`, `users`, `ordersByStatus`)

### Type Design

- Use non-nullable (`!`) for fields that always have values
- Use interfaces for shared fields across types
- Use unions for polymorphic return types
- Use custom scalars for domain types (`DateTime`, `Email`, `URL`)
- Avoid deeply nested types (max 3-4 levels)

### Input Types

```graphql
input CreateUserInput {
  name: String!
  email: String!
  role: UserRole = USER
}

input UpdateUserInput {
  name: String
  email: String
  role: UserRole
}
```

- Separate input types for create vs update
- Create inputs have required fields; update inputs are all optional
- Reuse input types across mutations when semantics match

## Query Patterns

### Single Resource

```graphql
type Query {
  user(id: ID!): User
  userByEmail(email: String!): User
}
```

- Return nullable type (null = not found)
- Use specific lookup fields (`byEmail`, `bySlug`) rather than generic filter

### Collection

```graphql
type Query {
  users(
    first: Int = 20
    after: String
    filter: UserFilter
    orderBy: UserOrderBy = CREATED_AT_DESC
  ): UserConnection!
}
```

- Always return connection type (never raw list)
- Default page size, max enforced server-side
- Filter input type for complex filtering

## Mutation Patterns

### Input/Payload Pattern

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}

type UserError {
  field: String
  code: ErrorCode!
  message: String!
}
```

- Single `input` argument wrapping all fields
- Return payload type with result + errors
- Errors are domain errors (validation, business rules), not transport errors

### Rules

- Mutations should be idempotent where possible (use idempotency keys)
- Return the modified resource in the payload
- Use enums for error codes, strings for messages

## Error Handling

### Transport vs Domain Errors

| Type | Mechanism | Example |
|------|-----------|---------|
| Transport | GraphQL `errors` array | Auth failure, syntax error, rate limit |
| Domain | Mutation payload `errors` field | Validation failure, business rule violation |

### Error Extensions

```json
{
  "errors": [{
    "message": "Not authorized",
    "extensions": {
      "code": "UNAUTHORIZED",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }]
}
```

- Use `extensions.code` for machine-readable error classification
- Never expose internal details in error messages

## Pagination

### Relay Connection Pattern

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

- Use for all list fields
- `totalCount` is optional (expensive for large datasets)
- Cursor-based pagination is strongly preferred

## Authentication

- Pass auth token via HTTP header (`Authorization: Bearer <token>`)
- Resolve auth in context middleware, not in individual resolvers
- Use directives for field-level auth: `@auth(requires: ADMIN)`
- Return `UNAUTHORIZED` error in extensions for auth failures

## Performance

- **N+1 problem:** Use DataLoader for batching database queries
- **Query depth:** Limit max depth (typically 7-10 levels)
- **Query complexity:** Assign costs to fields, reject queries exceeding budget
- **Persisted queries:** Hash queries for production, reject ad-hoc in production
- **Field-level caching:** Use `@cacheControl` directive with `maxAge` and scope
