# Normalization Guide

Decision rules for when to normalize and when to denormalize.

## Normal Forms Quick Reference

| Normal Form | Rule | Violation Example |
|-------------|------|-------------------|
| **1NF** | No repeating groups, atomic values | `tags: "a,b,c"` in single column |
| **2NF** | No partial dependencies on composite keys | Non-key column depends on part of composite PK |
| **3NF** | No transitive dependencies | `city` depends on `zip_code`, not on PK |
| **BCNF** | Every determinant is a candidate key | Non-trivial FD where LHS is not a superkey |
| **4NF** | No multi-valued dependencies | Independent multi-valued facts in same table |

## When to Normalize (Default)

Normalize to 3NF by default. Benefits:
- Eliminates data redundancy
- Prevents update/insert/delete anomalies
- Reduces storage
- Simplifies constraint enforcement

## When to Denormalize

Denormalize when ALL of these conditions are met:
1. Measured query performance is unacceptable (not speculative)
2. The denormalized data has a clear consistency strategy
3. The write-to-read ratio is low (read-heavy workload)
4. Indexing and query optimization have already been tried

### Acceptable Denormalization Patterns

| Pattern | When to Use | Trade-off |
|---------|------------|-----------|
| **Materialized view** | Complex aggregations read frequently | Staleness (refresh lag) |
| **Computed column** | Derived value needed in most queries | Storage + trigger complexity |
| **Cached count** | Aggregate count queried often | Consistency (counter drift) |
| **Embedding** | 1:1 relationship always accessed together | Wasted space if rarely used |
| **Star schema** | Analytics/reporting workloads | Update anomalies acceptable |

### Anti-Patterns (Never Denormalize This Way)

- Storing comma-separated values in a single column (violates 1NF)
- Duplicating entire rows for "history" (use temporal tables)
- Adding `_cache` columns without a refresh mechanism
- Storing JSON blobs for structured data that needs querying

## Decision Framework

```
Is query performance actually measured as slow?
├── No → Stay normalized (don't prematurely optimize)
└── Yes → Can indexing or query rewriting fix it?
    ├── Yes → Add index or rewrite query
    └── No → Is the workload read-heavy (>90% reads)?
        ├── Yes → Consider materialized view or computed column
        └── No → Stay normalized, optimize write path instead
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Tables | plural snake_case | `user_accounts` |
| Columns | singular snake_case | `first_name` |
| Primary keys | `id` or `<table>_id` | `user_id` |
| Foreign keys | `<referenced_table>_id` | `organization_id` |
| Indexes | `idx_<table>_<columns>` | `idx_users_email` |
| Unique constraints | `uq_<table>_<columns>` | `uq_users_email` |
| Check constraints | `chk_<table>_<description>` | `chk_orders_positive_amount` |
