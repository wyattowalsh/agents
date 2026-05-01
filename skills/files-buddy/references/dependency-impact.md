# Dependency Impact Reference

Every cleanup or offload recommendation must explain what depends on the target and
what happens after the action. Treat this as the evidence gate before approval.

## Required Fields

| Field | Meaning |
|-------|---------|
| Repercussion | User-visible consequence such as rebuild, redownload, sync delete, app re-index, broken VM, or lost backup |
| Dependency Evidence | Concrete proof: repo refs, lockfiles, process refs, app ownership, model references, cloud metadata, or package cache owner |
| Regeneration Cost | Time/bandwidth/CPU needed to restore the data |
| Restore Path | Exact undo, reinstall, app-native restore, cloud restore, or backup restore path |
| Confidence | High/medium/low with reason |
| Dry-run Proof | Command/report that produced the finding without mutation |
| Do Not Proceed If | Specific blocker that forces skip or user choice |

## Evidence Checks

| Target | Checks |
|--------|--------|
| Project files | `git status`, `.gitignore`, lockfiles, project manifests, recent mtime, open files |
| Running apps | `lsof +D <path>` for small scopes; process names for app-owned dirs |
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

## Approval Language

Use concrete phrasing:

```text
Recommendation: prune Docker build cache only.
Local bytes: 18.4 GB. Cloud bytes: 0.
Dependency evidence: docker system df reports build cache; named volumes are excluded.
Repercussion: future image builds may take longer and re-download layers.
Restore path: rebuild images from Dockerfiles; no direct undo.
Dry-run proof: docker system df -v, no prune command run.
Approval tier: High.
```

Never use vague phrases like "probably safe" without evidence.
