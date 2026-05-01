# Scan Performance

Large filesystem scans must be resumable, bounded-memory, and cloud-safe.

## Phases

1. **Volume discovery:** enumerate requested paths, `/Volumes/*`, cloud roots, filesystem type, free space, and protected exclusions.
2. **Pruning:** exclude `.git/`, hard-blocked paths, app-managed report-only internals, and symlink escapes.
3. **Fast inventory:** collect size, mtime, type, inode/link count, and top-N heavy paths.
4. **Classification:** identify user files, caches, app stores, cloud placeholders, packages, archives, models, VMs, and backups.
5. **Duplicate pregroup:** group by size first; skip singleton sizes and zero-byte placeholders.
6. **Partial hash:** hash first/last chunks for large candidate groups when supported.
7. **Full hash:** run `fclones`/`rmlint` only on candidate groups or scoped paths.
8. **Media similarity:** optional `czkawka_cli`/media tools; never mutating.
9. **Dependency check:** enrich candidates with owners, refs, restore path, and repercussions.
10. **Synthesis:** ranked recommendations and progress/report JSON.

## Rules

- Use NUL-safe paths (`-0`, JSON, or Python `Path`) whenever possible.
- Do not store every file in memory for huge trees; keep aggregates and top-N lists.
- Write checkpoints to `~/.files-buddy/runs/{run-id}/checkpoints/`.
- Resume by phase and skip unchanged directories using path, mtime, size, and inode summaries.
- Limit local parallelism by volume; limit cloud parallelism to 2 and add delays.
- Do not materialize cloud placeholders during broad scans. Recommend a targeted deep scan instead.
- Treat removable volumes as volatile; revalidate before execution.

## Scale Defaults

| Files | Behavior |
|-------|----------|
| <1k | Full scan and full preview |
| 1k-10k | Full scan, grouped preview, periodic progress |
| 10k-100k | Checkpoints, top-N memory caps, candidate-only hashing |
| 100k+ | Per-volume phases, sampled UI preview, resumable run ID required |

## Progress Events

Emit phase events after discovery, pruning, inventory, duplicate pregroup, hash, dependency check, synthesis, approval, execution, and verification. See `progress-reporting.md`.
