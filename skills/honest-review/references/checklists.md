# Analysis Checklists

Full checklists for all review levels. SKILL.md has abbreviated versions.
Read during analysis (Step 3) or when building teammate prompts.

## Surface Level (Lines, Expressions, Functions)

### Defects

- Check correctness: return values, off-by-one, boundary conditions, null/undefined handling
- Check error handling: missing catches, swallowed errors, generic catch-all, missing finally/cleanup
- Check security: unsanitized input, injection vectors, hardcoded secrets, insecure defaults
- Check readability: misleading names, magic numbers, unclear control flow
- Check consistency: naming style, error patterns, logging patterns match rest of codebase

### Simplification

- Remove dead code, unused imports, unreachable branches
- Remove defensive checks for impossible states (trust internal callers)
- Remove comments that restate the code — keep only "why" comments
- Flatten complex conditionals into early returns or guard clauses
- Replace manual iteration with built-in/stdlib equivalents
- Replace hand-rolled logic with well-known library functions
- Flatten nested callbacks into async/await or promise chains
- Extract duplicate logic across branches into shared path

## Structural Level (Modules, Classes, Boundaries)

### Defects

- Check test coverage: untested public API, missing edge cases, brittle mocks
- Check coupling: module A depends on B's internals, circular dependencies
- Check interface contracts: unclear ownership, missing validation at boundaries
- Check cognitive complexity: functions exceeding cyclomatic complexity of 15

### Simplification

- Remove wrappers that just delegate to a single implementation (1:1 pass-through)
- Remove abstractions with only one concrete use — inline them
- Remove config/feature flags for things that never vary in practice
- Remove extension points nobody extends — add when needed, not before
- Collapse unnecessary layers of indirection (A calls B calls C, B does nothing)
- Unify near-identical modules that differ only in minor details
- Merge over-decomposed files that should be one module
- Eliminate pass-through plumbing where data passes unchanged across layers

## Algorithmic Level (Algorithms, Data Structures, System Design)

### Defects

- Check complexity class: O(n^2) or worse where better algorithms exist
- Check N+1 patterns: queries/calls in loops, missing batching
- Check resource leaks: unclosed connections, file handles, streams, timers
- Check concurrency: race conditions, missing locks, deadlock potential
- Check backpressure: unbounded queues, missing rate limiting, memory growth

### Simplification

- Replace O(n^2) with O(n) or O(n log n) where possible
- Use the right data structure for the access pattern (map vs. list, set vs. array)
- Replace reimplemented logic with stdlib or existing dependency equivalents
- Consolidate multi-pass operations into single pass where data allows
- Remove unnecessary serialization/deserialization round-trips
- Simplify complex state machines where a simpler model handles all cases
- Reduce distributed complexity where a simpler topology suffices
- Add or remove caching/memoization based on actual access patterns
- Switch between polling and push based on actual requirements

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
