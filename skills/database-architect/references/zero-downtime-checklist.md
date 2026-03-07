# Zero-Downtime Migration Checklist

Pre-flight checklist before applying any migration to production.

## Pre-Migration

- [ ] Migration has both UP and DOWN scripts
- [ ] DOWN script tested independently (rollback verified)
- [ ] No `DROP TABLE` or `DROP COLUMN` without data backup confirmation
- [ ] Large table operations use batched updates (not single UPDATE on millions of rows)
- [ ] Index creation uses `CONCURRENTLY` (PostgreSQL) or `ALGORITHM=INPLACE` (MySQL)
- [ ] Foreign key constraints added as `NOT VALID` then validated separately
- [ ] CHECK constraints added as `NOT VALID` then validated separately
- [ ] Data backfill operations are idempotent (safe to re-run)
- [ ] Migration tested against production-size data (not just dev fixtures)
- [ ] Lock duration estimated -- no long-running locks on hot tables

## Backwards Compatibility Check

- [ ] Old application code works with new schema (expand phase)
- [ ] New application code works with old schema (rollback safety)
- [ ] No column renames without expand-contract pattern
- [ ] No type narrowing without expand-contract pattern
- [ ] No NOT NULL additions without default + backfill first
- [ ] API layer handles both old and new schema shapes during transition

## Expand-Contract Timeline

1. **Deploy expand migration** -- add new structures, keep old ones
2. **Deploy dual-write code** -- application writes to both old and new
3. **Backfill historical data** -- copy from old to new (batched, idempotent)
4. **Switch reads** -- application reads from new structures
5. **Stop dual-write** -- application writes only to new
6. **Deploy contract migration** -- remove old structures

Each step should be a separate deployment. Never combine expand and contract in one release.

## Emergency Rollback

- [ ] Rollback script tested before applying forward migration
- [ ] Rollback does not lose data written after forward migration
- [ ] Monitoring alerts configured for migration-related errors
- [ ] Communication plan for stakeholders if rollback needed
- [ ] Database connection pool sized for migration load

## Post-Migration

- [ ] Run `ANALYZE` (PostgreSQL) or `ANALYZE TABLE` (MySQL) after large changes
- [ ] Verify query plans on critical queries (check for unexpected seq scans)
- [ ] Monitor error rates for 30 minutes post-migration
- [ ] Confirm application metrics are within normal range
- [ ] Update schema documentation / ER diagrams
