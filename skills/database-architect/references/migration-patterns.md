# Migration Patterns

Zero-downtime migration strategies for common schema operations.

## Expand-Contract Pattern

The safest approach for non-backwards-compatible changes. Two-phase deployment:

1. **Expand** — add new structure alongside old (both work simultaneously)
2. **Migrate** — backfill data from old to new structure
3. **Contract** — remove old structure after all consumers switch

## Operation Safety Matrix

| Operation | Backwards Compatible | Data Loss Risk | Zero-Downtime Strategy |
|-----------|---------------------|----------------|----------------------|
| ADD COLUMN (nullable) | Yes | None | Direct apply |
| ADD COLUMN (NOT NULL) | No | None | Add nullable → backfill → set NOT NULL |
| DROP COLUMN | No | Yes | Stop writing → deploy → drop |
| RENAME COLUMN | No | None | Expand-contract with dual-write |
| ALTER TYPE (widen) | Yes | None | Direct apply (e.g., VARCHAR(50) → VARCHAR(100)) |
| ALTER TYPE (narrow) | No | Possible | Expand-contract with validation |
| ADD INDEX | Yes | None | CREATE INDEX CONCURRENTLY (PostgreSQL) |
| DROP INDEX | Yes | None | Direct apply (verify query plans first) |
| ADD FOREIGN KEY | Yes | None | Add NOT VALID → validate separately |
| DROP TABLE | No | Yes | Verify zero references → backup → drop |
| ADD CHECK CONSTRAINT | Depends | None | Add NOT VALID → validate separately |

## Column Rename (Expand-Contract)

```sql
-- Phase 1: Expand
ALTER TABLE users ADD COLUMN full_name TEXT;
UPDATE users SET full_name = name WHERE full_name IS NULL;

-- Application: write to both columns, read from new
-- Phase 2: Contract (after all consumers updated)
ALTER TABLE users DROP COLUMN name;
```

## NOT NULL Addition

```sql
-- Phase 1: Add with default
ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending';

-- Phase 2: Backfill existing rows
UPDATE orders SET status = 'pending' WHERE status IS NULL;

-- Phase 3: Add constraint
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
```

## Type Change (e.g., INT → BIGINT)

```sql
-- Phase 1: Add new column
ALTER TABLE events ADD COLUMN id_new BIGINT;

-- Phase 2: Backfill
UPDATE events SET id_new = id WHERE id_new IS NULL;

-- Phase 3: Swap (in transaction)
BEGIN;
ALTER TABLE events RENAME COLUMN id TO id_old;
ALTER TABLE events RENAME COLUMN id_new TO id;
COMMIT;

-- Phase 4: Drop old
ALTER TABLE events DROP COLUMN id_old;
```

## Migration Validation Checklist

1. Every UP migration has a corresponding DOWN migration
2. No migration uses DROP without a backup strategy
3. Large table operations use batched updates (not single UPDATE)
4. Index creation uses CONCURRENTLY where supported
5. Foreign key constraints use NOT VALID + separate VALIDATE
6. Data backfill operations are idempotent (re-runnable)
7. Migration names follow `NNNN_description` convention
8. Each migration file does exactly one logical operation
