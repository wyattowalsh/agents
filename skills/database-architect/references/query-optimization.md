# Query Optimization Patterns

Index strategies and query rewriting patterns for common performance issues.

## Index Type Selection

| Query Pattern | Recommended Index | Why |
|--------------|-------------------|-----|
| Exact match (`WHERE col = ?`) | B-tree (default) | O(log n) lookup |
| Range scan (`WHERE col > ?`) | B-tree | Ordered traversal |
| Pattern match (`WHERE col LIKE 'prefix%'`) | B-tree | Prefix matching |
| Pattern match (`WHERE col LIKE '%suffix'`) | GIN trigram | Cannot use B-tree for suffix |
| Full-text search | GIN/GiST | Inverted index for text |
| JSON field access | GIN | Containment and existence |
| Geospatial queries | GiST/SP-GiST | Spatial indexing |
| High-cardinality set membership | Hash (PostgreSQL) | O(1) lookup, no range support |
| Array containment | GIN | Array operators (@>, &&) |

## Covering Index Pattern

Include all columns needed by a query to avoid table lookups:

```sql
-- Query: SELECT email, name FROM users WHERE status = 'active'
-- Covering index:
CREATE INDEX idx_users_status_covering ON users (status) INCLUDE (email, name);
```

**When to use:** High-frequency queries where the table lookup is the bottleneck.
**Trade-off:** Larger index, slower writes.

## Partial Index Pattern

Index only rows matching a condition to reduce index size:

```sql
-- Only index active users (80% of queries target active users)
CREATE INDEX idx_users_active ON users (email) WHERE status = 'active';
```

**When to use:** Queries consistently filter on a common condition.
**Trade-off:** Only useful for queries matching the WHERE clause.

## Common Anti-Patterns

### N+1 Query Problem

```sql
-- BAD: 1 query for orders + N queries for items
SELECT * FROM orders WHERE user_id = 1;
-- For each order:
SELECT * FROM items WHERE order_id = ?;

-- GOOD: Single query with JOIN
SELECT o.*, i.* FROM orders o
JOIN items i ON i.order_id = o.id
WHERE o.user_id = 1;
```

### Over-Indexing

Signs of over-indexing:
- Write performance degrades (every INSERT/UPDATE maintains all indexes)
- Disk usage growing faster than data
- `pg_stat_user_indexes` shows indexes with zero scans

Rule of thumb: If an index has zero scans in 30 days, consider dropping it.

### Missing Composite Index

```sql
-- Query: WHERE status = ? AND created_at > ?
-- BAD: Two separate indexes (database picks one, ignores other)
CREATE INDEX idx_status ON orders (status);
CREATE INDEX idx_created ON orders (created_at);

-- GOOD: Composite index with selective column first
CREATE INDEX idx_status_created ON orders (status, created_at);
```

**Column order rule:** Put the most selective (highest cardinality) column first,
unless the query always uses both columns with equality on the first.

## EXPLAIN Plan Reading

Key metrics to check:
- **Seq Scan** on large tables → likely needs an index
- **Nested Loop** with large outer set → consider Hash Join
- **Sort** with high cost → add index matching ORDER BY
- **Rows** estimate far from actual → statistics are stale, run ANALYZE

## Query Rewriting Patterns

| Problem | Fix |
|---------|-----|
| `SELECT *` | List only needed columns |
| `ORDER BY RANDOM()` | Use `TABLESAMPLE` or application-side random |
| `COUNT(*)` for existence | Use `EXISTS (SELECT 1 ...)` |
| `IN (SELECT ...)` with large subquery | Rewrite as `JOIN` or `EXISTS` |
| `DISTINCT` on large result | Check if JOIN is causing duplication |
| `OFFSET` for pagination | Use keyset pagination (`WHERE id > last_id`) |
