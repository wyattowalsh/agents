# Validation Matrix

## Scope and baseline

Implemented against `main` at `99a5692a0df01e3b6ea416448efde842e3c94e6f`.
Local release checks used Linux and CPython 3.13.5. All filesystem operations in
the behavioral checks used disposable fixtures, not the maintainer's files.
No live tool installs, skill sync, cleanup, provider configuration, or daemon
installation was performed.

## Executed local checks

| Surface | Evidence and result |
| --- | --- |
| Complete skill suite | `uv run python scripts/check.py --tests`: bundled frontmatter, skill, eval, package and repository-audit gates pass; **168 tests passed, 4 native macOS tests skipped, 41 subtests passed** |
| Static quality | Skill-local Ruff check, Ruff format check (31 Python files), and ty check pass |
| Execution | 73 tests pass on Linux, with 4 native skips: exact approval, stale objects, collisions, concurrent writers and overlapping scopes, durable intent, bounded copy, reverse/quarantine, reconciliation, derived report and legacy inspection |
| Observation | 66 tests and 41 subtests pass: bounded inventory/resume, fresh dependencies, content consent, tool parsers, safe rules, watch settlement, cache/path poisoning, artifact containment and hardlinks |
| Reports | 24 Python tests pass: zero/unknown accounting, malformed shapes, source/manifest structure, escaping, unique output and no-follow state paths |
| Pipeline | Actual scanner -> duplicate-review -> report schema -> HTML renderer subprocess pipeline passes, including unusual filenames and unchanged source bytes |
| Package | A 59-file portable ZIP is built and extracted away from the repository; a new declared Python 3.13 environment installs from its lock and runs bundled checks/tests without a sibling audit or undeclared dependencies |
| Portability integration | Files Buddy portable-check and bundled-toolkit tests pass; canonical bundled toolkit synchronization check passes |
| Shared audit | 11 focused audit regressions pass, including portable dispatch/state paths and negative controls; structural skill score is 94/A, not a substitute for behavioral evidence |
| Documentation | 56 focused authoring/rendering/research-page tests pass; catalog index consistency, target renderer parity, research manifest and README freshness checks pass |
| Browser behavior | Node VM suite passes 16 named schema/import/escaping/refresh/accessibility-control checks; this is not rendered layout proof |
| Change specification | Strict OpenSpec reports `harden-files-buddy` valid with no issues |
| Diff hygiene | `git diff --check` passes |

The 31 natural-language eval cases are validated expectations. They were not run
as live model tool-call evaluations, and no model quality score is inferred.

## Original audit findings addressed

| Finding | Resolution and executable evidence |
| --- | --- |
| Synced staging described as remote-safe | Cloud references distinguish eviction, copy and synchronized move/delete; local executor rejects known cloud roots |
| Advertised undo missing | Exact reverse-plan preview and separately approved no-clobber execution; copied data is retained in reviewed quarantine |
| Intent recorded only after effects | Durable prepared state precedes filesystem effects; interruption fixtures reconcile without replay |
| Concurrent append lost updates | One canonical state plus serialized state/directory locks; subprocess concurrency regressions |
| Invalid outcomes could report success | Strict versioned state/plan validation, nonzero errors, and explicit corrupt discovery errors |
| Approval could widen by count | Exact mappings and before-state digest; new objects excluded and changed objects blocked |
| Zero savings and unknown risk fabricated | Separate metrics and explicit unknowns in Python/schema/browser; zero and absent values tested |
| Organize simulation could execute shell | Closed declarative allowlist checked before any simulation; unsafe actions/templates rejected |
| OSS syntax/schema drift | Pinned registry, source-linked representative fixtures, corrected recipes and fail-closed version handling |
| Standalone gate/dependency gaps | Declared PyYAML and lock, mandatory bundled packager, isolated missing-reference/missing-gate tests |
| Nonportable model/frontmatter | Portable source keys enforced, model inherited from invoking harness, nested metadata correctly projected into catalog |
| Schema-only eval confidence | Behavioral Python/Node tests and explicit distinction from authored model eval cases |
| Dashboard shape/lifecycle drift | Shared report normalizer/schema, structured manifest, validated import and bounded selected-file refresh |
| Parent mtime used as content validity | Fresh per-file fingerprints; changed-child/unchanged-parent regression |
| Manifest discovery escaped state scope | Contained no-follow discovery; symlink/nonregular entries unopened, corrupt regular entries explicit |

Independent adversarial review additionally found and closed case-alias policy
bypasses, inventory database traversal/hardlink/sidecar writes, poisoned cached
paths escaping hash scope, stale dependency classifications, managed/secret
content eligibility, and corrupt list/search omission. Repeat probes verified
zero forbidden content reads or preservation of linked targets. No remaining
blocking finding was reported in the independently reviewed observation,
policy, reporting, and execution-discovery boundaries.

## Native and rendered qualification

The dedicated Files Buddy workflow runs Python 3.13 package checks on Linux and
macOS, plus Node behavior and Chromium desktop/mobile/keyboard/error-state
acceptance using the existing locked Playwright dependency. It retains browser
screenshots as artifacts. Workflow results are recorded after publication.

Local Chromium launch was blocked by the environment's socket restriction
(`Operation not permitted`). No local rendered screenshot, responsive layout,
or browser focus pass is claimed. Four native execution tests were skipped on
Linux; the case-alias test also skips a case-sensitive native volume.

Even a successful native CI run does not qualify live File Provider residency,
TCC configurations, all APFS metadata/snapshot/shared-extent behavior, physical
space reclamation, backup restore services, perceptual duplicate keepers, or
actual installed external binaries. Tool JSON fixtures are representative,
source-linked fixtures, not fabricated native CLI captures. Unsupported
operations remain rejected or report-only. Locks coordinate cooperating
helpers, not arbitrary same-user writers; SQLite retains a documented pathname
API limitation under concurrent uncooperative directory replacement.

## Confirmed pre-existing repository failures

These were checked against the untouched detached baseline. They were not
weakened or repaired as unrelated changes:

- `wagents validate`: missing `wagents.mcphub.things_contract` import, identical
  baseline failure.
- Whole-repository strict OpenSpec validation: the same eight unrelated failing
  change/spec IDs and identical issues; this change is valid.
- Broad portability run: 113 passed and one existing `harness-master` failure
  for missing `scripts/grok_workflow_projection.py`; the failing case also
  reproduces alone on the pristine baseline.
- Global generated-doc freshness: baseline has nine stale artifacts; the scoped
  update has seven, all from that baseline set. Target and shared index checks
  pass. Canonical generation initially touched 2,203 files; 2,197 unrelated
  outputs were restored, leaving six generated/source documentation paths.
- Shared index regeneration includes existing word-count discrepancies and
  age-based research-staleness updates. Other source/authoring pages and README
  remain unchanged.
- Root formatter differences in `wagents/rendering.py`, `wagents/docs.py`, and
  `tests/test_rendering.py` reproduce on pristine baseline content. New changes
  pass lint and focused tests; no unrelated formatting rewrite was retained.
- Astro build prerequisites: owning `pnpm@11.10.0` frozen install rejects the
  existing `patchedDependencies` configuration/lock mismatch. No lockfile or
  supply-chain gate was bypassed, and a production docs build is not claimed.
