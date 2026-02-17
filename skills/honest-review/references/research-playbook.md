# Research Validation Playbook

How to validate review findings with live research. This is what separates honest-review from static checklist review.

## Two-Phase Review Pattern

Phase 1 (Flag): Analyze code using LLM knowledge. Generate hypotheses.
Phase 2 (Validate): For each hypothesis, spawn research subagent(s). Only report findings with evidence.

## Research Tools and When to Use

| Tool | Use When | Example |
|------|----------|---------|
| Context7 (resolve-library-id, then query-docs) | Verifying API usage, checking for deprecation, confirming method signatures | "Is React.createClass still valid in React 18?" |
| WebSearch | Checking current best practices, security advisories, known issues | "JWT storage best practices 2026" |
| WebFetch | Querying package registries, reading changelogs, checking CVE databases | "https://registry.npmjs.org/express/latest" |
| gh (GitHub CLI) | Checking open issues, security advisories, PR discussions | "gh api repos/expressjs/express/security-advisories" |

## Research Subagent Templates

### API Correctness Validator

Spawn when: a finding claims an API is used incorrectly or is deprecated.

Prompt template:
- Input: library name, method/API being used, code snippet
- Steps: Resolve library ID via Context7 (resolve-library-id tool), then query docs for the specific API (query-docs tool). Compare usage in code against current documentation.
- Output: validated (bool), evidence (string), citation (URL or doc section)
- Model: sonnet (needs judgment to compare usage against docs)

### Security Pattern Validator

Spawn when: a finding identifies a potential security concern.

Prompt template:
- Input: security-sensitive code snippet, pattern type (auth, crypto, SQL, etc.)
- Steps: WebSearch for current best practices for this pattern type. Check OWASP guidance. Compare code against recommendations.
- Output: validated (bool), severity (critical/high/medium/low), evidence, citation
- Model: sonnet (needs nuance for security assessment)

### Dependency Health Checker

Spawn when: a finding concerns dependency version, vulnerability, or deprecation.

Prompt template:
- Input: package name, installed version, language/ecosystem
- Steps: WebFetch the package registry for latest version and advisories (npm: registry.npmjs.org, PyPI: pypi.org/pypi/PKG/json, crates.io: crates.io/api/v1/crates/PKG). WebSearch for known issues. Check for deprecation notices.
- Output: status (healthy/outdated/vulnerable/deprecated), details, citation
- Model: haiku (structured data extraction)

### Performance Assumption Validator

Spawn when: a finding questions a performance assumption or pattern.

Prompt template:
- Input: code snippet with performance assumption (from comments or patterns)
- Steps: Context7 for library performance characteristics. WebSearch for benchmarks or known performance issues with this pattern.
- Output: validated (bool), actual characteristics, evidence
- Model: haiku

## Parallelism Strategy

- Spawn ALL research subagents for a review pass in a single message
- Use haiku for simple lookups (doc extraction, version checks)
- Use sonnet for nuanced validation (security, architecture decisions)
- If more than 10 findings to validate, batch into groups of 5-6 parallel subagents
- Set reasonable scope: do not research-validate obvious issues (null deref, syntax error). Only validate assumptions and non-obvious concerns.

## Evidence Quality

| Level | Criteria | Action |
|-------|----------|--------|
| Strong | Current official docs confirm the issue (Context7 citation) | Report with high confidence |
| Medium | Multiple web sources agree (WebSearch results) | Report with citation |
| Weak | Single blog post or outdated source | Flag as "unconfirmed" |
| None | No evidence found after research | Discard the finding |
