# CI Failure Triage Protocol

## Error Category Taxonomy

| Category | Indicators | Typical Root Cause | First Action |
|----------|-----------|-------------------|--------------|
| **dependency** | `ERESOLVE`, `404`, `ResolutionImpossible` | Version conflict, package removed | Pin or retry |
| **build** | Compilation error, type error, linker error | Code bug, missing import | Fix code |
| **test** | Assertion failure, flaky pass/fail, timeout | Logic bug, race condition | Fix or quarantine |
| **lint** | Format violation, rule error | Style mismatch | Run formatter |
| **deploy** | Permission denied, health check fail | Config error, resource limit | Investigate |
| **infrastructure** | OOM killed, disk full, runner offline | Resource exhaustion, runner issue | Retry first |

## Root Cause Patterns (regex for log matching)

### Dependency

| Pattern | Root Cause |
|---------|-----------|
| `npm ERR! ERESOLVE` | Peer dependency conflict |
| `Could not find a version that satisfies` | Python version constraint mismatch |
| `ETIMEDOUT.*registry` | Registry network timeout |
| `404 Not Found.*(@[a-z]\|package)` | Package removed or renamed |

### Build

| Pattern | Root Cause |
|---------|-----------|
| `error TS\d+:` | TypeScript compilation error |
| `FATAL ERROR:.*heap limit` | Node.js out of memory |
| `Cannot find module '([^']+)'` | Missing import or package |
| `SyntaxError: Unexpected token` | Syntax error or wrong Node version |

### Test

| Pattern | Root Cause |
|---------|-----------|
| `Expected .* to (equal\|be\|match)` | Assertion failure |
| `Timeout of \d+ms exceeded` | Hung async operation |
| `ECONNREFUSED 127\.0\.0\.1` | Service not running in CI |

### Deploy / Infrastructure

| Pattern | Root Cause |
|---------|-----------|
| `AccessDenied\|403 Forbidden` | IAM/RBAC permission missing |
| `health check.*fail` | App not starting or wrong port |
| `ImagePullBackOff` | Wrong image tag or registry auth |
| `No space left on device` | Runner disk full |
| `Killed.*signal 9\|OOMKilled` | Process killed by OOM |

## Fix Recipes

**dependency:** Pin conflicting package to compatible range. Add retry with `nick-fields/retry@<sha>` (`max_attempts: 3`). For removed packages, find replacement or lock to last good version.

**build (type error):** Read the error file/line, check recent changes. For OOM, set `NODE_OPTIONS: --max-old-space-size=4096` or use a larger runner.

**test (flaky):** Add `retry: 2` to the step. Investigate race conditions and unmocked timers. For timeouts, check unresolved promises and missing `await`.

**lint:** Run formatter locally (`prettier --write`, `ruff format`), commit the result. For new rules, comply or disable inline with a tracking issue.

**deploy:** Verify OIDC trust policy and IAM roles. For health check failures, increase `initialDelaySeconds`, check app logs for startup crash, verify env vars.

**infrastructure:** For disk full, add cleanup step before build. For OOM, use `ubuntu-latest-4-core` or reduce parallelism (`--max-workers=2`). Retry once, then escalate.

## Escalation Criteria

| Situation | Action |
|-----------|--------|
| Same error on retry (deterministic) | Fix root cause -- do not retry again |
| Passes on second retry | Add retry logic, investigate root cause async |
| Failure in third-party action | Pin to last working SHA, open upstream issue |
| Infrastructure error repeated twice | Escalate to platform team |
| Failure only on fork PRs | Expected if secrets required -- restructure workflow |
| Cause unclear after 15 min | Reproduce locally with `act` or SSH debug (`action-tmate`) |

## Log Analysis Techniques

### Finding the first failure

1. Start at the **bottom** of the failed step -- final error is often the summary
2. Search **upward** for the originating error -- cascading failures mask root cause
3. Look for `error` before `warning` -- first error line is usually the trigger
4. Check exit codes: `Process completed with exit code 1` identifies the failed step

### Ignoring cascading errors

After a build failure, downstream steps (test, deploy) fail with unrelated messages. Always triage the **first failed step** in the job, not the last.

### Useful grep patterns for large logs

```bash
grep -n -i "error\|fatal\|failed" log.txt | head -20   # First errors
grep -n "ERR!\|Error:" log.txt                           # npm/node errors
grep -n "exit code\|exited with" log.txt                 # Exit codes
```

### Structured extraction for logs > 500 lines

Keep: first 50 lines (setup context), last 200 lines (errors/summary), lines matching error patterns above. Discard: verbose dependency install output, passing test output.
