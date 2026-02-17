# Research Validation Playbook

Validate review findings with live research instead of relying on static checklist review.

## Contents

- [Two-Phase Review Pattern](#two-phase-review-pattern)
- [Research Tools and When to Use](#research-tools-and-when-to-use)
- [Research Subagent Templates](#research-subagent-templates)
- [Parallelism Strategy](#parallelism-strategy)
- [Evidence Quality](#evidence-quality)

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

### Slopsquatting Detector

Spawn when: unfamiliar dependency names appear in imports or package manifest, or when code appears LLM-generated.

Prompt template:
- Input: list of package names from imports and dependency manifest, ecosystem (npm/PyPI/crates.io/Go)
- Steps: For each package name, WebFetch the package registry endpoint (npm: registry.npmjs.org/PKG, PyPI: pypi.org/pypi/PKG/json, crates.io: crates.io/api/v1/crates/PKG). If the package does not exist (404), flag as potential slopsquatting. If it exists but has very low download counts or was recently created, flag as suspicious.
- Output: list of {package, status (verified/not-found/suspicious), evidence}
- Model: haiku (structured registry lookups)

IMPORTANT: Prioritize this check — slopsquatting is a supply chain attack vector.
Non-existent packages in import statements indicate hallucinated dependencies.

### Test Quality Validator

Spawn when: a finding questions test coverage or test quality.

Prompt template:
- Input: test file paths, corresponding source file paths
- Steps: Read test files. List all public methods/functions in source files. Compare: which public APIs have no corresponding test? Check assertion density: flag test functions with zero assertions or only mock verifications. Check for common anti-patterns: tests that test implementation details, tests that never fail.
- Output: coverage gaps (list of untested public APIs), quality issues (list of anti-patterns found), assertion density score
- Model: sonnet (needs judgment to evaluate test quality)

## Parallelism Strategy

- Spawn ALL research subagents for a review pass in a single message
- Use haiku for simple lookups (doc extraction, version checks)
- Use sonnet for nuanced validation (security, architecture decisions)
- If more than 10 findings to validate, batch into groups of 5-6 parallel subagents
- Set reasonable scope: do not research-validate obvious issues (null deref, syntax error). Only validate assumptions and non-obvious concerns.
- Spawn lens subagents (Inversion, Deletion, Newcomer, Incident, Evolution) in parallel with checklist reviewers when applying creative lenses
- Prioritize slopsquatting detection — spawn slopsquatting detector subagents before other research, as non-existent packages are security-critical
- Use opus for lens-based analysis (requires creative reasoning); use haiku for slopsquatting detection (structured lookups)

## Evidence Quality

| Level | Criteria | Action |
|-------|----------|--------|
| Strong | Current official docs confirm the issue (Context7 citation) | Report with high confidence |
| Medium | Multiple web sources agree (WebSearch results) | Report with citation |
| Weak | Single blog post or outdated source | Flag as "unconfirmed" |
| None | No evidence found after research | Discard the finding |
