# Dependency Impact Reference

Every cleanup or offload recommendation must explain what depends on the target and
what happens after the action. Treat this as the evidence gate before approval.

## Required Fields

| Field | Meaning |
|-------|---------|
| Repercussion | User-visible consequence such as rebuild, redownload, sync delete, app re-index, broken VM, or lost backup |
| Dependency Evidence | Concrete proof: repo refs, lockfiles, process refs, app ownership, model references, cloud metadata, or package cache owner |
| Regeneration Cost | Evidenced time/bandwidth/CPU, or unknown; regeneration is not reversal |
| Restore Path | Exact undo, reinstall, app-native restore, cloud restore, or backup restore path |
| Confidence | High/medium/low with reason |
| Preview Evidence | Versioned command/report, observed coverage, and declared auxiliary writes; never infer safety from a dry-run label |
| Do Not Proceed If | Specific blocker that forces skip or user choice |

## Evidence Checks

| Target | Checks |
|--------|--------|
| Project files | `git status`, `.gitignore`, lockfiles, project manifests, recent mtime, open files |
| Running apps | Bounded owner/process observations; recursive `lsof +D` only for small explicit scopes |
| Package caches | package manager ownership, global vs project cache, lockfile presence |
| Xcode data | simulator/runtime/archive ownership, export status, active devices |
| Docker data | `docker system df`, named volumes, compose files, running containers |
| Models | model name, app path refs, uniqueness, redownload URL/source, quantization notes |
| Cloud files | provider, placeholder state, sync status, quota, duplicate remote IDs |
| Backups/snapshots | app-native listing, age, device owner, snapshot association |

## Confidence Rules

- **High:** dry-run output, owner evidence, restore path, and low ambiguity all exist.
- **Medium:** dry-run and restore path exist, but ownership or regeneration cost is approximate.
- **Low:** potential savings are visible but dependencies are uncertain; recommend review only.
- **Unknown:** evidence is absent or unsupported. Missing fields never default to
  high confidence, low risk, zero cloud impact, or a fabricated undo command.

Risk and confidence are different fields. An exact hash match is evidence of
content equality; it does not establish that a file is unused. Treat project,
DAW/sample, model, photo sidecar, app-library and cache ownership as relationships.
Preserve referenced groups instead of flattening them by extension or age. Check
`(st_dev, st_ino)` rather than inode alone for links across volumes.

## Approval Language

Use concrete phrasing:

```text
Recommendation: review Docker build cache using its owning tool.
Candidate logical bytes: 18.4 GB from the usage report. Reclaimable physical bytes: unknown.
Cloud bytes: unknown unless the relevant storage configuration is verified.
Dependency evidence: docker system df reports build cache; named volumes are excluded.
Repercussion: future image builds may take longer and re-download layers.
Restore path: rebuild images from Dockerfiles; no direct undo.
Observation: docker system df -v, no prune command run; this is not an exact prune preview.
Approval tier: High.
```

Never use vague phrases like "probably safe" without evidence.

Before execution, require an exact mapping and supported operation, not this
descriptive recommendation alone. Unknown ownership or unsupported restore
semantics stays report-only. See `references/extension-workflows.md` for the
separate cache/archive/backup/provider acceptance gates.
