# Self-Verification Protocol

Devil's advocate protocol for anti-hallucination verification. Load during Wave 3 after cross-validation, when 3 or more findings survive with confidence >= 0.5. This is the final quality gate before synthesis.

## When to Run

- **Trigger:** 3+ findings with confidence >= 0.5 survive cross-validation
- **Target selection:** Top 5-10 findings ranked by confidence score (highest first)
- **Tier requirement:** Mandatory for Standard, Deep, and Exhaustive tiers. Skip for Quick tier.
- **Timing:** After Wave 3 cross-validation and bias sweep, before Wave 4 synthesis

## Devil's Advocate Subagent

Spawn a dedicated verification subagent with this prompt:

> You are the Self-Verification Judge. Your sole purpose is to attempt to disprove each finding below. You succeed by finding flaws, not by confirming claims. For each finding:
>
> 1. **Currency check.** Is the evidence current? Flag sources older than 1 year for evolving topics, older than 3 years for stable topics.
> 2. **Inferential validity.** Does the claim actually follow from the cited evidence, or is it an overreach? Check if the source says exactly what the finding claims.
> 3. **Counter-search.** Search for counterarguments or contradicting sources using a DIFFERENT search engine than the one that found the original evidence. Use at least 2 counter-queries per finding.
> 4. **Confabulation check.** Could this be an LLM confabulation -- a claim that sounds authoritative but matches training data rather than current reality? Flag claims with no URL evidence that "feel obvious."
> 5. **Citation anchor verification.** Fetch the cited URL and confirm the claimed content actually appears on that page. If the URL is inaccessible, note it. If the content does not match the excerpt, flag as CITATION_MISMATCH.
>
> For each finding, classify as: **SURVIVES** | **WEAKENED** | **DISPROVEN** | **HALLUCINATED**

## Verdict Definitions

| Verdict | Meaning | Criteria |
|---------|---------|----------|
| **SURVIVES** | Finding withstands adversarial scrutiny | Counter-search found no contradicting evidence; citation verified; inference is sound |
| **WEAKENED** | Finding partially valid but overstated or under-supported | Counter-evidence exists but does not fully refute; or citation is partially mismatched; or inference is a stretch |
| **DISPROVEN** | Finding contradicted by stronger evidence | Counter-search found credible sources that directly refute the claim; or citation content does not support the finding |
| **HALLUCINATED** | Finding has no real-world basis | No URL evidence exists; claim matches LLM training patterns but live search returns nothing; or cited URL does not contain the claimed content |

## Confidence Adjustments

Apply these adjustments to the finding's confidence score after verification:

| Verdict | Adjustment |
|---------|-----------|
| SURVIVES | +0.05 (reward for surviving adversarial check) |
| WEAKENED | -0.10 (evidence is less solid than initially scored) |
| DISPROVEN | Set to 0.0 (exclude from synthesis or present as refuted) |
| HALLUCINATED | Set to 0.0; add bias marker "LLM confabulation" |

After adjustment, re-apply the hard cap: no single-source claim above 0.6, no claim above 0.7 without 2+ independent sources.

## Citation Anchor Verification

For every finding that cites a specific URL:

1. Fetch the URL using the same tool that originally retrieved it (or fetcher/trafilatura as fallback).
2. Search the page content for the key phrases from the finding's excerpt.
3. Classify the result:

| Result | Action |
|--------|--------|
| Content matches excerpt | Mark as CITATION_VERIFIED |
| Content partially matches (paraphrased or adjacent) | Mark as CITATION_APPROXIMATE; reduce confidence by 0.05 |
| Content does not match or URL returns 404 | Mark as CITATION_MISMATCH; downgrade finding to DISPROVEN |
| URL inaccessible (timeout, auth-wall, rate limit) | Mark as CITATION_UNVERIFIABLE; note in finding metadata |

## Counter-Search Protocol

For each major claim in the target findings:

1. Formulate the OPPOSITE of the claim as a search query. Example: if the finding says "Rust is memory-safe," search for "Rust memory safety limitations" or "Rust unsafe code vulnerabilities."
2. Use a different search engine than the one that originally found the supporting evidence. If the original used brave-search, use duckduckgo or exa.
3. Evaluate the counter-evidence:

| Counter-Evidence Found | Action |
|------------------------|--------|
| Strong refutation from credible source | Classify finding as DISPROVEN or WEAKENED depending on strength |
| Partial counter-evidence or edge cases | Classify as WEAKENED; add nuance to the finding |
| No counter-evidence after 2+ queries | Classify as SURVIVES; the claim held up under adversarial scrutiny |

## Output Format

The self-verification subagent returns results in this structure:

```
VERIFICATION V-{seq:02d}: Finding RR-{finding_id}
  CLAIM: [the finding's claim statement]
  VERDICT: [SURVIVES|WEAKENED|DISPROVEN|HALLUCINATED]
  COUNTER-EVIDENCE: [summary of counter-search results, or "none found"]
  CITATION CHECK: [VERIFIED|APPROXIMATE|MISMATCH|UNVERIFIABLE]
  CONFIDENCE ADJUSTMENT: [old] -> [new]
  NOTES: [any additional observations]
```

## Integration with Wave 4

Pass all verification results to the synthesis phase. In the final output:

- SURVIVES findings appear with their adjusted (slightly higher) confidence
- WEAKENED findings appear with caveats and reduced confidence
- DISPROVEN findings appear in a "Refuted Claims" section (if relevant to the query) or are excluded
- HALLUCINATED findings are excluded from the synthesis entirely; record in the journal for auditability
