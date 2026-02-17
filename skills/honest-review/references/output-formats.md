# Output Formats

Report templates for final output. Read when producing the final report.

## Compact Format (5 or fewer findings, small reviews)

Use for quick reviews of 1-2 files with few findings.

```
HONEST REVIEW (N files)

P1: [file:line] description — evidence: [citation]. Fix: approach. (Level)
S0: [module] description — evidence: [citation]. Fix: approach. (Level)

Verified: build clean, tests pass.
```

## Session Review Format (6+ findings)

Use for session reviews with multiple findings across files.

```
======================================
HONEST REVIEW
======================================

FILES REVIEWED:
- path/to/file1.ts (created)
- path/to/file2.ts (modified)

DEFECTS:

P0 - MUST FIX:
1. [file:line] Missing null check
   Level: Surface
   Evidence: [research result — doc citation, advisory URL, etc.]
   Impact: Can crash when user not found
   Fix: Add guard clause

P1 - SHOULD FIX:
2. [file:line] Query in loop
   Level: Algorithmic
   Evidence: [research result]
   Impact: N+1 pattern, O(n) queries where 1 suffices
   Fix: Batch fetch

SIMPLIFICATIONS:

S0 - SHOULD SIMPLIFY:
3. [module] Service layer wraps repository 1:1
   Level: Structural
   Evidence: [codebase analysis — N files, M lines of pure delegation]
   Impact: Removes 2 files, 1 layer of indirection, ~80 lines
   Fix: Inline repository calls

CROSS-LEVEL NOTES:
- [conflicts resolved, symptoms elevated to root causes]

IMPROVEMENTS MADE:
- #1: Added null check [x]
- #2: Refactored to batch [x]

VERIFIED:
- Build: clean [x]
- Tests: all passing [x]
- Behavior: [how confirmed] [x]
======================================
```

## Full Codebase Audit Format

Use for Mode 2 full audit reports.

```
======================================
FULL CODEBASE AUDIT
======================================

PROJECT: [name] ([language/framework])
SCOPE: [N files across M directories]
TEAM: [list of reviewers and their domains]

CRITICAL (P0/S0):
1. [file:line or module] [category] description
   Level: [Surface/Structural/Algorithmic]
   Evidence: [research citation]
   Impact: [what breaks or what complexity it removes]
   Fix: [recommended approach]

SIGNIFICANT (P1/S1):
2. ...

MINOR (P2/S2):
3. ...

CROSS-DOMAIN FINDINGS:
- [architectural or systemic observations with evidence]

DEPENDENCY HEALTH:
- [package]: [status] — [details, citation]

HEALTH SUMMARY:
- Correctness: [overall assessment]
- Security: [overall assessment]
- Performance: [overall assessment]
- Simplicity: [where is unnecessary complexity concentrated?]
- Test coverage: [overall assessment]
- Technical debt: [overall assessment]

TOP RECOMMENDATIONS:
1. [highest-impact improvement]
2. [second highest]
3. [third highest]
======================================
```

## Individual Finding Format

Use this structure for each finding in any report format:

```
[priority] — [file:line or module] [category]
  Level: [Surface/Structural/Algorithmic]
  Description: [what is wrong or unnecessarily complex]
  Evidence: [research validation result — doc citation, advisory URL, etc.]
  Impact: [consequence or complexity cost]
  Fix: [recommended approach]
```

## Verification Summary

Append to every report after implementing fixes:

```
VERIFIED:
- Build/lint: [status]
- Tests: [status]
- Behavior: [what was checked]
```
