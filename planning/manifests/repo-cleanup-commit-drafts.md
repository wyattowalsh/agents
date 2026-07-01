# Commit message drafts (do not commit unless requested)

## Bundle A — repo cleanup + RV-RC review fixes

```
Complete catalog SSOT cleanup and session review remediation.

Remove legacy external-skills.md dual-read; enforce quarantine on authoring
MDX and catalog index; align harness-master evals with authoring MDX +
generated index SSOT; modularize validate collectors; refresh docs provenance
bulk and instruction sync surfaces.
```

**Staged paths:** see `planning/manifests/bundle-a-paths.txt` (~1495 paths)

## Bundle B — review-skill collateral (separate PR)

```
Harden review skill asset: portable check.py, state management reference,
expanded specialist lenses, validation contract alignment, and tests.
```

**Paths:** see `planning/manifests/bundle-b-paths.txt` (9 paths)

- `skills/review/**` (except `scripts/asset_toolkit/`)
- `tests/test_review_check.py`
- `planning/manifests/review-skill-findings-*`
- `docs/src/authoring/skills/review.mdx`

## Stage commands

```bash
# Bundle A
git restore --staged .
cat planning/manifests/bundle-a-paths.txt | xargs git add

# Bundle B (after A committed or unstaged)
git restore --staged .
cat planning/manifests/bundle-b-paths.txt | xargs git add
```
