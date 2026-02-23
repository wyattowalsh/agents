# Auto-Fix Protocol

Dry-run fix workflow: preview diffs, get approval, apply safely, verify.
Read when user selects "implement fixes" after a review report.

## Contents

- [Dry-Run Preview](#dry-run-preview)
- [Confirmation Gate](#confirmation-gate)
- [Conflict Detection](#conflict-detection)
- [Rollback Safety](#rollback-safety)
- [Post-Fix Verification](#post-fix-verification)

## Dry-Run Preview

Before applying any fix, generate a unified diff preview for each finding:

1. For each approved finding, generate the fix as a unified diff (do not write to disk).
2. Present all diffs grouped by file, ordered by line number ascending.
3. Annotate each diff with: finding ID, confidence, effort estimate.

```text
FIX PREVIEW — HR-S-001 [P0, Confidence: 0.85, Effort: S]
--- a/src/auth.py
+++ b/src/auth.py
@@ -43,4 +43,7 @@
     token = request.headers.get("Authorization")
+    if token_expired(token):
+        raise TokenExpiredError("Token has expired")
+
     user = lookup_user(token)
```

For multi-file fixes (batched findings), present all diffs in batch order with a batch header.

## Confirmation Gate

After presenting all previews, ask the user for approval:

```text
Implement fixes? Choose one:
  [all]     — apply all N fixes
  [select]  — choose individual fixes by ID (e.g., "HR-S-001, HR-S-003")
  [skip]    — do not implement any fixes
  [edit]    — modify a fix before applying (provide finding ID)
```

**Rules:**

- Never apply fixes without explicit user approval.
- If user selects "edit", present the specific diff and accept modifications.
- If user selects "select", apply only the chosen finding IDs.

## Conflict Detection

Before applying selected fixes, check for conflicts:

1. **Overlapping edits**: Two fixes that modify the same lines in the same file. Flag and ask user to choose one or manually merge.
2. **Dependent edits**: Fix A changes a function signature that fix B calls. Flag the dependency and suggest application order.
3. **Cascading effects**: Fix A removes a function that fix B modifies. Flag and recommend applying only A.

Present conflicts before applying:

```text
CONFLICTS DETECTED:
  HR-S-003 and HR-S-007 both modify src/api/users.py:45-52
  → Choose one or merge manually: [HR-S-003 / HR-S-007 / merge / skip both]
```

## Rollback Safety

Before applying any fixes:

1. **Check git state**: run `git status --porcelain`. If uncommitted changes exist, warn user and ask to stash or commit first.
2. **Create checkpoint**: run `git stash push -m "honest-review-pre-fix"` or `git checkout -b honest-review/fix-$(date +%s)` based on user preference.
3. **Apply atomically**: apply all approved fixes, then commit as a single commit with message: `fix: apply honest-review findings [HR-S-001, HR-S-003, ...]`.
4. **On failure**: if any fix fails to apply cleanly, roll back all changes: `git checkout -- .` and report which fix failed.

## Post-Fix Verification

After applying fixes, run verification in order:

1. **Build/lint**: run project build and linter. Report any new errors.
2. **Tests**: run test suite. Report any new failures.
3. **Behavior spot-check**: describe what to manually verify (if applicable).
4. **Re-scan**: optionally re-run the review on fixed files to confirm findings are resolved.

```text
VERIFIED:
  Build/lint: clean ✓
  Tests: 42 passed, 0 failed ✓
  Behavior: token expiry now returns 401 ✓
  Findings resolved: HR-S-001 ✓, HR-S-003 ✓
```

Cross-references: references/output-formats.md (fix preview format), SKILL.md (approval gate rule).
