# Database-Specific Idioms

Type choices, syntax differences, and feature availability across engines.

## PostgreSQL

### Preferred Types

| Use Case | Type | Notes |
|----------|------|-------|
| Primary key | `BIGSERIAL` or `UUID` | BIGSERIAL for internal, UUID for distributed |
| Timestamps | `TIMESTAMPTZ` | Always store with timezone |
| Currency | `NUMERIC(precision, scale)` | Never use FLOAT for money |
| Text (variable) | `TEXT` | No performance difference vs VARCHAR in PG |
| Boolean | `BOOLEAN` | Native support |
| JSON | `JSONB` | Binary, indexable. Use `JSON` only for write-only logs |
| Arrays | `TYPE[]` | Native arrays with GIN indexing |
| Enums | `CREATE TYPE ... AS ENUM` | Schema-level enums, hard to modify |

### PostgreSQL-Specific Features

- `CREATE INDEX CONCURRENTLY` -- non-blocking index creation
- `ALTER TABLE ... ADD CONSTRAINT ... NOT VALID` -- add constraint without scanning
- `VALIDATE CONSTRAINT` -- validate separately (can be concurrent)
- `EXCLUDE USING` -- exclusion constraints for range overlaps
- `GENERATED ALWAYS AS` -- computed columns
- `PARTITION BY RANGE/LIST/HASH` -- native partitioning
- Advisory locks for distributed coordination

### Anti-Patterns

- Using `SERIAL` instead of `BIGSERIAL` (32-bit overflow risk)
- `VARCHAR(255)` -- PG has no performance reason for length limits on TEXT
- Storing timestamps without timezone (`TIMESTAMP` vs `TIMESTAMPTZ`)
- Using `ENUM` for frequently-changing value sets (use lookup table instead)

## MySQL / MariaDB

### Preferred Types

| Use Case | Type | Notes |
|----------|------|-------|
| Primary key | `BIGINT AUTO_INCREMENT` | Or `BINARY(16)` for UUID |
| Timestamps | `DATETIME(6)` or `TIMESTAMP` | TIMESTAMP has 2038 limit |
| Currency | `DECIMAL(precision, scale)` | Same as NUMERIC |
| Text (variable) | `VARCHAR(N)` | Length matters for indexing in MySQL |
| Boolean | `TINYINT(1)` | MySQL has no native BOOLEAN |
| JSON | `JSON` | MySQL 5.7+, limited indexing |

### MySQL-Specific Considerations

- InnoDB default: clustered primary key (PK order = physical order)
- `ALTER TABLE ... ALGORITHM=INPLACE` for online DDL
- `pt-online-schema-change` for zero-downtime on large tables
- `VARCHAR(255)` matters: prefix index limits differ by charset (767 bytes for utf8mb4)
- `ON UPDATE CURRENT_TIMESTAMP` for automatic modification tracking

### Anti-Patterns

- `UTF8` charset (only 3 bytes, use `utf8mb4` for full Unicode)
- Implicit type coercion in WHERE clauses (destroys index usage)
- Using `FLOAT`/`DOUBLE` for exact values

## SQLite

### Preferred Types

| Use Case | Type | Notes |
|----------|------|-------|
| Primary key | `INTEGER PRIMARY KEY` | Alias for rowid (auto-increment) |
| Timestamps | `TEXT` (ISO 8601) | No native datetime type |
| JSON | `TEXT` with `json()` functions | SQLite 3.9+ |

### SQLite-Specific Considerations

- Type affinity system (declared types are suggestions, not constraints)
- No native `ALTER TABLE DROP COLUMN` before 3.35.0
- No concurrent access (use WAL mode for read concurrency)
- Foreign keys disabled by default (`PRAGMA foreign_keys = ON`)
- Entire DB is a single file -- no partitioning

## MongoDB

### Schema Design Patterns

| Pattern | When to Use |
|---------|------------|
| **Embedding** | 1:1 or 1:few relationships, always accessed together |
| **Referencing** | 1:many or many:many, independent access patterns |
| **Bucket** | Time-series data, group by time window |
| **Outlier** | Most documents small, rare documents large |

### MongoDB Considerations

- No JOINs (use `$lookup` sparingly -- it is slow)
- Design schema around query patterns, not normalization
- Document size limit: 16 MB
- Index on `_id` is automatic
- Compound indexes follow leftmost prefix rule (same as B-tree)
- Use `createIndex({background: true})` for non-blocking index creation
