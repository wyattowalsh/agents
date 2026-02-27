# Bias Detection and Mitigation

Comprehensive bias catalog for research findings. Check every finding against all 10 categories during the Wave 3 bias sweep. Load during Wave 3 or when bias markers appear in evidence chains.

## Core Bias Categories

| # | Bias | Detection Signal | Mitigation | Research Example |
|---|------|-----------------|------------|------------------|
| 1 | **LLM prior** | Finding aligns with common training patterns but lacks fresh evidence; claim feels "obvious" yet no URL supports it | Flag finding; require fresh source confirmation before confidence > 0.4 | "React is the most popular framework" stated without current survey data |
| 2 | **Recency** | Only recent results cited; foundational or historical context absent; no sources older than 1 year on an established topic | Explicitly search for historical perspective; add temporal range to queries | Citing only 2025-2026 benchmarks for a database comparison while ignoring decade-long production track records |
| 3 | **Authority** | Claim accepted solely because source is prestigious; no independent verification attempted | Cross-validate even authoritative claims with a second independent source | Accepting a Google blog post claim without checking if independent benchmarks reproduce the result |
| 4 | **Confirmation** | Search queries constructed to confirm initial hypothesis; only affirmative results retained | Use neutral queries; explicitly search for counterarguments; rephrase queries with opposite framing | Searching "benefits of microservices" instead of "microservices tradeoffs" |
| 5 | **Survivorship** | Only successful examples found; failures, shutdowns, and negative outcomes absent | Search for failures and counterexamples; add "failed", "shutdown", "postmortem" to queries | Listing only successful Rust rewrites while ignoring abandoned rewrite attempts |
| 6 | **Selection** | Results limited to English-language or Western sources; single search engine used; one ecosystem dominates | Use multiple search engines; note coverage limitations in output; search in domain-specific databases | Evaluating a global technology trend using only English Stack Overflow data |
| 7 | **Anchoring** | First source found disproportionately shapes all subsequent interpretation; later sources only confirm the first | Document first source separately; actively seek contrasting viewpoints before synthesizing | First article claims "Kubernetes is overkill for small teams" and all subsequent analysis adopts that frame |

## LLM-Specific Biases

| # | Bias | Detection Signal | Mitigation |
|---|------|-----------------|------------|
| 8 | **Training data recency** | Model knowledge frozen at cutoff; claim involves dates, versions, or events beyond training data | Always verify with live search for evolving topics; flag any claim about events after the model's training cutoff |
| 9 | **Consensus hallucination** | Model generates plausible-sounding claims with no real source; claim has authoritative tone but search returns nothing | Require URL evidence for every non-trivial claim; if no source found after 2 search engines, mark as "unverified LLM output" |
| 10 | **False precision** | Model assigns specific numbers, dates, percentages, or statistics without evidence; precision exceeds what sources actually state | Flag any numerical claim without a cited source; check if the original source actually states the specific number or a range |

## Bias Sweep Protocol

Run after Wave 3 cross-validation, before synthesis (Wave 4). This is a mandatory checkpoint for Standard, Deep, and Exhaustive tiers.

### Procedure

1. For each surviving finding (confidence >= 0.3), iterate through all 10 bias categories above.
2. For each category, ask: "Does this finding exhibit this bias signal?"
3. If yes, record the bias in the finding's `BIAS MARKERS` field using the format: `[category_name]: [brief explanation]`.
4. Apply mitigation: execute the mitigation strategy (e.g., run a counter-search, add historical query). Update the finding based on results.
5. After mitigation, re-assess confidence. If the bias is confirmed and unmitigated, reduce confidence by 0.10.

### Quick Reference Checklist

For each finding, answer these questions:

- Does this claim feel "obvious" without fresh evidence? (LLM prior)
- Are all sources from the last 12 months? (Recency)
- Is the claim supported only by a single prestigious source? (Authority)
- Were search queries phrased to confirm the hypothesis? (Confirmation)
- Are only success stories represented? (Survivorship)
- Did all evidence come from one search engine or one language? (Selection)
- Did the first source found dominate the interpretation? (Anchoring)
- Could the model's training data be stale on this topic? (Training data recency)
- Does the claim lack any URL evidence? (Consensus hallucination)
- Does the claim include suspiciously precise numbers? (False precision)

### Severity Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **Critical** | Consensus hallucination or false precision with no source | Set confidence to 0.0; exclude from synthesis unless re-verified |
| **High** | LLM prior or confirmation bias on a key finding | Reduce confidence by 0.15; run counter-search before including |
| **Medium** | Recency, authority, survivorship, or selection bias detected | Reduce confidence by 0.10; note bias in output |
| **Low** | Anchoring detected but multiple perspectives already included | Note bias marker; no confidence adjustment needed |
