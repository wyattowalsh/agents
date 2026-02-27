# Confidence Rubric

Scoring system for research findings. Read during Wave 3 when assigning confidence to cross-validated claims.

## Scoring Bands

| Band | Score | Criteria | Typical Evidence |
|------|-------|----------|-----------------|
| **Authoritative** | 0.90-0.99 | Official docs + 2 independent sources agree; no contradictions; current | Context7 confirms API + 2 web sources corroborate |
| **Strong** | 0.70-0.89 | 2+ independent sources agree; minor qualifications only | Two independent articles from different authors agree on the claim |
| **Moderate** | 0.50-0.69 | Single authoritative source, or 2 sources with partial agreement | Official blog post confirms; one other source partially agrees |
| **Weak** | 0.30-0.49 | Single non-authoritative source, or conflicting evidence | One blog post supports but another contradicts |
| **Speculative** | 0.10-0.29 | LLM reasoning only; no external evidence found | Pattern matches training knowledge but no live source confirms |
| **Contradicted** | 0.00-0.09 | Actively contradicted by credible evidence | Official docs explicitly state the opposite of the claim |

## Cross-Validation Rules

Cross-validation is the core anti-hallucination mechanism. Apply these rules when multiple sources address the same claim.

| Source Agreement | Effect on Score |
|-----------------|----------------|
| 2 independent sources agree | Eligible for 0.7+ |
| 3+ independent sources agree | Eligible for 0.9+ |
| Sources agree but from same original | Treat as single source; cap at 0.6 |
| Sources partially agree (agree on core, differ on details) | Score the core claim separately from details |
| Sources contradict | Flag as contradiction; do not average scores; report both sides |
| One source agrees, one is silent | No boost; score based on the confirming source alone |

## Independence Checks

Two sources are independent only if they have no shared derivation. Apply these checks before counting sources toward cross-validation.

1. **Citation chain check** — if Source B cites Source A, they are NOT independent. Trace to the primary source.
2. **Author overlap** — same author across publications is a single perspective, not independent confirmation.
3. **Syndication check** — identical text across sites indicates syndication. Count as one source.
4. **Data source check** — two analyses of the same dataset are not independent on the dataset's claims.
5. **Press release check** — multiple news articles covering the same press release are one source.

**Rule of thumb:** Ask "If Source A were wrong, would Source B also be wrong for the same reason?" If yes, they are not independent.

## Score Adjustments

Apply adjustments after the base score is assigned. Adjustments are cumulative but the final score must stay within 0.0-0.99.

### Positive Adjustments

| Adjustment | Amount | Condition |
|-----------|--------|-----------|
| Recency boost | +0.05 to +0.10 | Time-sensitive topic; sources published within last 6 months |
| Authority boost | +0.10 | Source is official documentation, peer-reviewed paper, or RFC |
| Reproduction boost | +0.10 | Claim verified by running code, executing query, or direct observation |
| Triangulation boost | +0.05 | 3+ methodologically diverse sources (e.g., docs + empirical + academic) |

### Negative Adjustments

| Adjustment | Amount | Condition |
|-----------|--------|-----------|
| Stale penalty | -0.10 | Sources >1 year old on evolving topic (frameworks, security, APIs) |
| Single-engine penalty | -0.05 | All supporting evidence from same search engine |
| Blog-only penalty | -0.05 | All evidence from blog posts with no official docs or papers |
| LLM-prior flag | -0.10 | Claim matches common LLM training patterns but lacks fresh evidence |
| Translation penalty | -0.05 | Key sources in different language from query; nuance may be lost |

## Merged Confidence Formula

When multiple independent sources support the same claim, merge their individual confidence scores:

```
c_merged = 1 - (1-c1)(1-c2)...(1-cN)
```

Cap at **0.99** — no claim reaches 1.0 without direct reproduction.

**Example:** Three sources with confidence 0.5, 0.6, and 0.4:
```
c_merged = 1 - (1-0.5)(1-0.6)(1-0.4) = 1 - (0.5)(0.4)(0.6) = 1 - 0.12 = 0.88
```

Apply the formula only to truly independent sources (pass independence checks above). Dependent sources contribute their highest individual score, not a merged score.

## Hard Rules

These rules override all other scoring logic. Violating any hard rule is a critical error.

1. **No claim >= 0.7 without 2+ independent sources.** A single source, no matter how authoritative, caps at 0.6.
2. **Single-source ceiling: 0.6.** Even official docs alone cap at 0.6 — require at least one independent corroboration for 0.7+.
3. **Degraded mode ceiling: 0.4.** When all research tools are unavailable, every finding is capped at 0.4 and labeled "unverified."
4. **Contradicted claims floor: report at actual score.** Do not suppress contradicted claims; report them at 0.0-0.1 with the contradicting evidence.
5. **LLM-only claims ceiling: 0.29.** Claims supported only by LLM reasoning with no external evidence never exceed 0.29.
6. **Never round up to cross a threshold.** A score of 0.69 is not 0.7. Thresholds are strict.
7. **Confidence must decrease if counter-evidence is found.** Finding counter-evidence always reduces confidence, even if the counter-source is weaker than the supporting source.
