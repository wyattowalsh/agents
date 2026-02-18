# Analysis Checklists

Full checklists for all review levels. SKILL.md has abbreviated versions.
Read during analysis (Step 3) or when building teammate prompts.

## Contents

- [Correctness Level](#correctness-level-lines-expressions-robustness)
- [Design Level](#design-level-modules-interfaces-flexibility)
- [Efficiency Level](#efficiency-level-algorithms-data-structures-performance)
- [Security](#context-dependent-security)
- [Observability](#context-dependent-observability)
- [AI Code Smells](#context-dependent-ai-code-smells)
- [Configuration and Secrets](#context-dependent-configuration-and-secrets)
- [Resilience](#context-dependent-resilience)
- [i18n and Accessibility](#context-dependent-i18n-and-accessibility)
- [Data Migration](#context-dependent-data-migration)
- [Backward Compatibility](#context-dependent-backward-compatibility)
- [Requirements Validation](#context-dependent-requirements-validation)

## Correctness Level (Lines, Expressions, Robustness)

### Defects

- Check correctness: return values, off-by-one, boundary conditions, null/undefined handling
- Check error handling: missing catches, swallowed errors, generic catch-all, missing finally/cleanup
- Check security: unsanitized input, injection vectors, hardcoded secrets, insecure defaults
- Check readability: misleading names, magic numbers, unclear control flow
- Check consistency: naming style, error patterns, logging patterns match rest of codebase
- Check resource leaks: unclosed connections, file handles, streams, timers
- Check concurrency: race conditions, missing locks, deadlock potential

### Simplification

- Remove dead code, unused imports, unreachable branches
- Remove defensive checks for impossible states (trust internal callers)
- Remove dead error paths — catch blocks that log and re-raise identically, error handling for conditions that cannot occur in context
- Remove comments that restate the code — keep only "why" comments
- Flatten complex conditionals into early returns or guard clauses
- Replace manual iteration with built-in/stdlib equivalents
- Replace hand-rolled logic with well-known library functions
- Flatten nested callbacks into async/await or promise chains

## Design Level (Modules, Interfaces, Flexibility)

### Defects

- Check test coverage: untested public API, missing edge cases, brittle mocks
- Check mutation resilience: would mutating key logic (flipping conditionals, changing boundaries) cause test failures? Flag tests that pass regardless of mutations.
- Check property-based testing opportunities: invariants, round-trip properties, commutativity. Flag hand-written examples where PBT would catch more.
- Check test naming: does each test name describe the scenario and expected outcome? Flag generic names ("test1", "testHelper").
- Check test isolation: shared mutable state between tests, order-dependent tests, time-dependent assertions
- Check boundary testing: off-by-one, empty collections, max values, unicode, null/undefined at boundaries
- Check coupling: module A depends on B's internals, circular dependencies
- Check interface contracts: unclear ownership, missing validation at boundaries
- Check cognitive complexity: functions exceeding cyclomatic complexity of 15
- Check generalizability: components tightly coupled to a single use case where a more general design costs nothing extra
- Check flexibility gaps: rigid interfaces that force callers into workarounds or copy-paste

### Simplification

- Remove wrappers that just delegate to a single implementation (1:1 pass-through)
- Remove abstractions with only one concrete use — inline them
- Remove config/feature flags for things that never vary in practice
- Remove extension points nobody extends — add when needed, not before
- Collapse unnecessary layers of indirection (A calls B calls C, B does nothing)
- Unify near-identical modules that differ only in minor details
- Merge over-decomposed files that should be one module
- Eliminate pass-through plumbing where data passes unchanged across layers
- Extract duplicate logic across branches into shared path
- Remove stale imports that no longer serve any purpose

## Efficiency Level (Algorithms, Data Structures, Performance)

### Defects

- Check complexity class: O(n^2) or worse where better algorithms exist
- Check N+1 patterns: queries/calls in loops, missing batching
- Check backpressure: unbounded queues, missing rate limiting, memory growth
- Check wrong data structure: using a data structure mismatched for the access pattern (map vs. list, set vs. array)

### Simplification

- Replace O(n^2) with O(n) or O(n log n) where possible
- Remove unnecessary serialization/deserialization round-trips
- Consolidate multi-pass operations into single pass where data allows
- Replace reimplemented logic with stdlib or existing dependency equivalents
- Add or remove caching/memoization based on actual access patterns
- Switch between polling and push based on actual requirements
- Simplify complex state machines where a simpler model handles all cases
- Reduce distributed complexity where a simpler topology suffices

## Context-Dependent: Security

Apply when code touches auth, payments, user data, network I/O, or file operations.

- Check broken access control: missing authorization checks, privilege escalation paths
- Check security misconfiguration: debug mode in prod, permissive CORS, default credentials
- Check injection vectors: SQL injection, command injection, XSS, template injection
- Check cryptographic failures: weak algorithms, hardcoded keys, insufficient entropy
- Check supply chain: unpinned dependency versions, missing lockfile integrity
- Check auth boundaries: session management, token validation, CSRF protection
- Check exception info leakage: stack traces, internal paths, or DB schemas in error responses
- Check SSRF: unvalidated URLs in server-side requests

IMPORTANT: Research-validate security findings against current OWASP guidance
and library-specific security docs via WebSearch and Context7.

## Context-Dependent: Observability

Apply when code is a service, API, or long-running process.

- Check structured logging: log levels appropriate, context included, PII excluded
- Check metrics: RED metrics (rate, errors, duration) instrumented for key paths
- Check distributed tracing: trace/span IDs propagated across service boundaries
- Check silent failures: background jobs, event handlers, async operations that fail quietly
- Check health check completeness: covers dependencies, not just process liveness

## Context-Dependent: AI Code Smells

Apply when code appears LLM-generated or when unfamiliar dependencies are used.

- Check slopsquatting: verify every import and dependency name exists in the relevant package registry (npm, PyPI, crates.io). Flag names that look plausible but do not exist — these may be hallucinated by an LLM.
- Check over-engineering: look for abstraction layers, design patterns, or configuration systems disproportionate to the problem size. Flag "enterprise patterns" in simple scripts.
- Check sycophantic comments: remove comments that praise the code ("elegant solution", "clever approach") or explain obvious operations ("increment counter by 1"). Keep only comments that explain non-obvious "why."
- Check phantom error handling: catch blocks that log and re-raise identically, error handling for conditions that cannot occur in context, defensive checks against the function's own contract.
- Check hallucinated APIs: verify that method names, function signatures, and parameter names match actual library documentation. Flag APIs that look correct but do not exist.
- Check copy-paste artifacts: duplicated code blocks with minor variations, inconsistent naming suggesting multiple generation passes, TODO comments referencing non-existent features.
- Check model-specific patterns: code with verbose variable names (`user_authentication_result_status`), excessive type annotations on trivial functions, unnecessary docstrings on obvious methods, overly defensive validation. These suggest code generated by an LLM and not reviewed by a human.
- Check test-implementation mismatch: tests that were generated alongside the implementation and only cover the happy path. Flag: tests that mirror the implementation logic exactly, tests with zero edge cases, tests that would pass even if the function returned a constant.

IMPORTANT: Research-validate slopsquatting and hallucinated APIs with highest priority —
these are security-critical. Use WebFetch against package registries and Context7 for API verification.

## Context-Dependent: Configuration and Secrets

Apply when code handles environment config, credentials, or deployment settings.

- Check 12-factor compliance: configuration via environment variables, not hardcoded values. Flag config embedded in code.
- Check secrets in source: scan for API keys, tokens, passwords, connection strings in code or committed config files. Check .gitignore covers sensitive files.
- Check config coupling: configuration that requires coordinated changes across multiple files or services. Flag hidden dependencies between config values.
- Check default security: default config values must be secure (no debug mode, no open CORS, no default passwords). Flag insecure defaults.
- Check environment parity: configuration that silently differs between dev/staging/production. Flag environment-specific code paths without explicit guards.

## Context-Dependent: Resilience

Apply when code calls external services, databases, or shared resources.

- Check timeouts: every external call must have an explicit timeout. Flag calls with implicit or no timeout.
- Check circuit breaking: repeated failures to an external dependency must trigger a circuit breaker or fallback. Flag unbounded retry loops.
- Check fallback behavior: what happens when a dependency is unavailable? Flag code that crashes instead of degrading gracefully.
- Check retry policy: retries must use exponential backoff with jitter. Flag fixed-interval retries or immediate retries that amplify failures.
- Check single points of failure: identify dependencies where failure means total system failure. Flag missing redundancy for critical paths.
- Check idempotency: operations that may be retried must be idempotent. Flag non-idempotent operations in retry paths.

## Context-Dependent: i18n and Accessibility

Apply when code produces user-facing UI or localized content.

- Check hardcoded strings: user-visible text must use i18n keys, not hardcoded strings. Flag literals in UI components.
- Check locale assumptions: date formats, number formats, currency, sorting order. Flag code that assumes a single locale.
- Check semantic HTML: use semantic elements (nav, main, article, button) instead of generic divs with click handlers. Flag accessibility anti-patterns.
- Check right-to-left support: layout must not break with RTL text. Flag hardcoded directional values (left/right padding, text-align).

## Context-Dependent: Data Migration

Apply when code changes database schemas, data formats, or storage structures.

- Check backward compatibility: new schema must work with old code during rolling deploys. Flag breaking changes without migration paths.
- Check migration ordering: migrations must be idempotent and order-independent where possible. Flag migrations that assume prior state.
- Check data validation: migration must validate data before and after transformation. Flag migrations that silently corrupt invalid records.
- Check zero-downtime: migration must not lock tables or block reads for extended periods. Flag operations that require downtime.

## Context-Dependent: Backward Compatibility

Apply when code changes public APIs, library interfaces, or shared contracts.

- Check breaking changes: identify removed or renamed public methods, changed signatures, altered return types. Flag any change that breaks existing callers.
- Check deprecation path: breaking changes must go through deprecation (warn for 1+ versions, then remove). Flag immediate removals.
- Check semver compliance: breaking changes require a major version bump. Flag breaking changes in minor or patch releases.
- Check changelog: every breaking change must be documented with migration instructions. Flag undocumented breaking changes.

## Context-Dependent: Requirements Validation

Apply when reviewing changes against stated intent (PR description, ticket, session goal).

- Check implementation matches stated intent: does the code do what was requested?
- Check edge cases from requirements are handled: boundary conditions, error states, empty inputs
- Check acceptance criteria are met: if criteria were specified, verify each one
- Check nothing was silently dropped: compare requirements list against implementation, flag omissions
- Check scope creep: flag code that goes beyond what was requested without justification
