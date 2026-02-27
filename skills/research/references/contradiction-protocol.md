# Contradiction Protocol

Detect, classify, and present contradictions between sources. Load during Wave 3 cross-validation when sources disagree, or during synthesis when integrating conflicting evidence.

## Contradiction Types

| Type | Definition | Classification Criteria | Resolution Approach |
|------|-----------|------------------------|---------------------|
| **Factual** | Source A says X, Source B says not-X. Both cannot be true. | Mutually exclusive claims about the same observable fact. | Report both with evidence. Note which source is more authoritative and more recent. Do NOT pick a winner without justification. |
| **Methodological** | Different approaches yield different results on the same question. | Studies or analyses using different methods, datasets, or assumptions reach different conclusions. | Explain why results differ. Identify the underlying assumptions. Assess which method is more appropriate for the specific context. |
| **Temporal** | Claim was true at time T1, no longer true at T2. | A fact or recommendation changed over time; both sources were correct in their respective periods. | Identify when the change occurred. Mark the older claim as SUPERSEDED with a timeline. Verify the newer claim is current. |
| **Scope** | True in context A, false in context B. | Claim holds under certain conditions (scale, platform, use case) but not others. | Clarify the contexts where each holds. Mark as CONTEXT_DEPENDENT. Specify the boundary conditions. |

## Detection Triggers

Flag a potential contradiction when any of these occur:

- Two sources make directly opposing claims about the same subject
- A benchmark or statistic differs by more than 30% between sources
- A "best practice" recommendation in one source is called an "anti-pattern" in another
- A feature or behavior described in one source is described differently in another
- A timeline or date conflicts between sources

## Resolution Framework

Contradictions are NOT resolved by majority vote. They are surfaced explicitly in the synthesis with:

1. **Both sides presented with equal evidence** -- quote or summarize each side with its source, access date, and confidence score.
2. **Assessment of which side has stronger evidence and why** -- consider: source authority, recency, methodology quality, sample size, specificity to the query context.
3. **Conditions under which each side would be correct** -- many contradictions resolve when the scope or context is narrowed.

Do not suppress contradictions to present a cleaner narrative. Contradictions are a feature of rigorous research, not a defect.

## Output Format

Use this format for every detected contradiction in the synthesis:

```
CONTRADICTION C-{seq:02d}: [topic]
  TYPE: [factual|methodological|temporal|scope]
  SIDE A: [claim] -- [source URL, tool, access date, confidence]
  SIDE B: [claim] -- [source URL, tool, access date, confidence]
  ASSESSMENT: [which side has stronger evidence and why]
  CONDITIONS: [under what conditions each side holds]
```

### Numbering

Assign sequential IDs (C-01, C-02, ...) within a single research session. Reference these IDs in findings that touch the same contradiction.

### Integration with Findings

When a finding overlaps with a contradiction:
- Add `CONTRADICTION: C-{id}` to the finding's metadata
- Adjust the finding's confidence downward by 0.05 to reflect genuine uncertainty
- In the synthesis, link the finding to the contradiction section

## Escalation Rules

| Situation | Action |
|-----------|--------|
| 2 high-confidence sources directly contradict | Escalate: run targeted counter-search on both claims using a third search engine |
| Contradiction on the query's central question | Must appear in the synthesis executive summary, not just the details section |
| 3+ sources on each side | Likely a genuine open debate; present as such with "the field is divided" framing |
| Contradiction involves a safety or security claim | Flag as HIGH priority; present both sides prominently regardless of confidence |
