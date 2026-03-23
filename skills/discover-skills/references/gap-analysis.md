# Gap Analysis Reference

Domain taxonomy, coverage scoring, and gap prioritization for skill ecosystem audits.

---

## 1. Domain Taxonomy

18 domains with current skill mapping.

| Domain | Existing Skills | Coverage |
|--------|----------------|----------|
| Code Quality | honest-review, tech-debt-analyzer | Medium |
| Testing | test-architect, playwright-best-practices | Medium |
| DevOps/CI | devops-engineer, infrastructure-coder | Medium |
| API/Backend | api-designer, database-architect, mcp-creator | Good |
| Frontend | frontend-designer | Low |
| Documentation | docs-steward, changelog-writer, add-badges | Good |
| Research/Analysis | research, data-wizard, wargame, host-panel | Good |
| Workflow | orchestrator, git-workflow, shell-scripter | Good |
| AI/Prompting | prompt-engineer, skill-creator, reasoning-router | Good |
| Naming/Branding | namer, email-whiz | Medium |
| Language Conventions | python-conventions, javascript-conventions, agent-conventions | Medium |
| Security | security-scanner, codeql, semgrep | Good |
| Web Quality | — | None |
| Mobile | — | None |
| Observability | — | None |
| Marketing/Growth | — | None |
| i18n/l10n | — | None |
| Specific Services | supabase-postgres-best-practices | Low |

---

## 2. Coverage Scoring Rubric

| Score | Criteria |
|-------|----------|
| None | No skills in this domain |
| Low | 1 skill, narrow scope |
| Medium | 2-3 skills, moderate scope but notable gaps |
| Good | 3+ skills with broad coverage |
| Full | Comprehensive coverage, no significant gaps |

---

## 3. Gap Identification Heuristic

Evaluate each domain by checking:

1. **Sub-domain coverage** — Compare skill descriptions against known sub-domains within the category. List uncovered sub-domains.
2. **Generality** — Are existing skills framework-specific (e.g., React only) or general-purpose? Framework-specific skills leave gaps for other frameworks.
3. **Tool coverage** — Identify popular tools, libraries, and frameworks in the domain with no corresponding skill.
4. **External skill availability** — Check if high-install skills on agentskills.io or community registries cover the gap.
5. **Workflow frequency** — How often does a typical developer encounter this domain in daily work?

### Sub-domain examples for None/Low domains

| Domain | Key Sub-domains to Cover |
|--------|-------------------------|
| Web Quality | Lighthouse/Core Web Vitals, accessibility (WCAG), SEO, structured data |
| Mobile | React Native, Flutter, Swift/iOS, Kotlin/Android, responsive design |
| Observability | Logging, metrics, tracing, alerting, dashboards, error tracking |
| Marketing/Growth | Analytics, A/B testing, landing pages, conversion optimization |
| i18n/l10n | String extraction, locale management, RTL support, date/number formatting |
| Frontend | Component architecture, state management, CSS systems, design tokens |
| Specific Services | AWS, GCP, Azure, Vercel, Cloudflare, Stripe, Auth0 |

---

## 4. Gap Priority Formula

```
priority = gap_severity x domain_relevance x solution_availability
```

### Factor: gap_severity

Derived from coverage score:

| Coverage | gap_severity |
|----------|-------------|
| None | 5 |
| Low | 3 |
| Medium | 1 |
| Good | 0 |
| Full | 0 |

### Factor: domain_relevance

Assessed per-user based on workflow centrality:

| Value | Meaning |
|-------|---------|
| 3 | Core to daily workflow |
| 2 | Used regularly |
| 1 | Occasional or niche |

### Factor: solution_availability

| Value | Meaning |
|-------|---------|
| 3 | Known external skill exists and can be installed |
| 2 | Both external and custom options viable |
| 1 | Custom skill must be built from scratch |

### Priority Thresholds

| Priority Score | Classification | Action |
|---------------|---------------|--------|
| >= 9 | **High** | Recommend immediately; install or create |
| 4-8 | **Medium** | Surface as suggestion; user decides |
| 1-3 | **Low** | Note for future; no immediate action |

### Example Calculations

| Domain | Severity | Relevance | Availability | Priority | Class |
|--------|----------|-----------|-------------|----------|-------|
| Web Quality | 5 | 3 | 3 | 45 | High |
| Observability | 5 | 2 | 2 | 20 | High |
| Mobile | 5 | 1 | 1 | 5 | Medium |
| Frontend | 3 | 3 | 2 | 18 | High |
| i18n/l10n | 5 | 1 | 1 | 5 | Medium |

> Example relevance/availability values are illustrative. The auditor must assess per-user context.
