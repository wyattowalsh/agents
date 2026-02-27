# Output Formats

Templates for all 5 output formats. Read during Wave 4 (synthesis) to format the final research product.

## Quick Answer (Quick Tier)

```
## Research: [query]
**Confidence:** [0.0-1.0] | **Sources:** [N]

[Direct answer in 2-5 sentences]

**Sources:**
1. [url] — [brief description]
2. [url] — [brief description]

> Quick lookup. For deeper investigation, re-run with `--depth standard`.
```

## Research Brief (Standard Tier, 1-2 Pages)

```
# Research Brief
**Query:** [query]
**Tier:** Standard | **Sources:** [N] | **Findings:** [N] | **Mean Confidence:** [0.XX]

## Key Findings
1. [finding] (confidence: [0.X]) — [citation]
2. [finding] (confidence: [0.X]) — [citation]
3. [finding] (confidence: [0.X]) — [citation]

## Contradictions
- [source A] says X; [source B] says Y. Assessment: [analysis of why they disagree and which is more credible]

## Gaps
- [what is not yet known or could not be verified]

## Synthesis
[3-5 paragraph integrated analysis — NOT a summary of findings but a novel integration
identifying patterns, emergent insights, and connections across sources]

## Sources
1. [author/org]. "[title]." [url]. Accessed [YYYY-MM-DD].
2. [author/org]. "[title]." [url]. Accessed [YYYY-MM-DD].
```

## Deep Report (Deep/Exhaustive Tier)

```
# Deep Research Report
**Query:** [query]
**Tier:** [Deep|Exhaustive] | **Sources:** [N] | **Findings:** [N] | **Mean Confidence:** [0.XX]
**Date:** [YYYY-MM-DD]

## Executive Summary
[3-5 sentence direct answer to the research question]

## Sub-Questions Investigated
1. [sub-question] → [answer summary, confidence: 0.X]
2. [sub-question] → [answer summary, confidence: 0.X]
3. [sub-question] → [answer summary, confidence: 0.X]

## Detailed Findings

FINDING RR-001: [claim statement]
  CONFIDENCE: [0.0-1.0]
  EVIDENCE:
    1. [source_tool] [url] [access_timestamp] — [relevant excerpt, max 100 words]
    2. [source_tool] [url] [access_timestamp] — [relevant excerpt, max 100 words]
  CROSS-VALIDATION: [agrees|contradicts|partial] across [N] independent sources
  BIAS MARKERS: [none | list of detected biases with category]
  GAPS: [none | what additional evidence would strengthen this finding]

FINDING RR-002: [claim statement]
  ...

## Contradictions
| ID | Topic | Type | Side A | Side B | Assessment |
|----|-------|------|--------|--------|------------|
| C-01 | [topic] | [factual|methodological|temporal|scope] | [claim + source] | [claim + source] | [analysis] |

## Evidence Landscape
| Confidence Band | Count | Findings |
|----------------|-------|----------|
| High (0.8-1.0) | N | RR-001, RR-003 |
| Medium (0.5-0.7) | N | RR-002, RR-005 |
| Low (0.3-0.4) | N | RR-004 |
| Uncertain (<0.3) | N | RR-006 |

## Bias Audit
| Bias Category | Detected In | Mitigation Applied |
|--------------|-------------|-------------------|
| [bias type] | RR-[NNN] | [what was done to counter it] |

## Gap Analysis
- [knowledge gap]: [why it matters, what further research would help]
- [knowledge gap]: [why it matters, what further research would help]

## Synthesis
[Multi-paragraph novel integration of findings. Identify patterns across sources,
surface emergent insights not present in any single source, and connect findings
to the broader context. This is analysis, not summary.]

## Key Takeaways
1. [takeaway with confidence level]
2. [takeaway with confidence level]
3. [takeaway with confidence level]

## Sources
1. [author/org]. "[title]." [url]. Accessed [YYYY-MM-DD]. Referenced by: RR-001, RR-003.
2. [author/org]. "[title]." [url]. Accessed [YYYY-MM-DD]. Referenced by: RR-002.

## Methodology
- **Tier:** [Deep|Exhaustive]
- **Waves completed:** [N]
- **Tools used:** [list of MCP tools and search engines]
- **Search queries:** [key queries executed]
- **Team structure:** [agents spawned and their roles]
- **Cross-validation:** [N] findings verified across [M] independent sources
- **Time span:** [research duration]
```

## Annotated Bibliography (Survey Mode)

```
# Annotated Bibliography: [field/topic]
**Sources Reviewed:** [N] | **Date:** [YYYY-MM-DD]

## Landscape Map
[Overview of the field's current state: key themes, active debates, dominant voices,
emerging trends, and where consensus exists vs. where it does not]

## Sources

### [Source 1 Title]
- **URL:** [url]
- **Author/Org:** [attribution]
- **Date:** [publication date]
- **Relevance:** [high|medium|low]
- **Key Contribution:** [what this source uniquely adds to the field]
- **Limitations:** [scope restrictions, potential bias, staleness]

### [Source 2 Title]
- **URL:** [url]
- **Author/Org:** [attribution]
- **Date:** [publication date]
- **Relevance:** [high|medium|low]
- **Key Contribution:** [unique addition]
- **Limitations:** [scope, bias, date]

## Thematic Clusters
### [Theme 1]
Sources: [list]. [Summary of what these sources collectively say about this theme.]

### [Theme 2]
Sources: [list]. [Summary.]

## Gaps in the Literature
- [underresearched area]: [why it matters, what questions remain open]
- [underresearched area]: [why it matters]

## Field Trajectory
[Where the field appears to be heading based on recent publications and trends]
```

## Decision Matrix (Compare Mode)

```
# Comparison: [A] vs [B] [vs [C]...]
**Criteria:** [N] | **Sources:** [N] | **Date:** [YYYY-MM-DD]

## Summary Verdict
[1-2 sentence bottom-line comparison]

| Criterion | [A] | [B] | Winner | Confidence |
|-----------|-----|-----|--------|------------|
| [criterion 1] | [assessment] | [assessment] | [A|B|tie] | [0.X] |
| [criterion 2] | [assessment] | [assessment] | [A|B|tie] | [0.X] |
| [criterion 3] | [assessment] | [assessment] | [A|B|tie] | [0.X] |
| **Overall** | | | **[A|B|depends]** | **[0.X]** |

## Detailed Analysis
### [Criterion 1]
[Per-criterion breakdown with evidence from sources. Include specific data points,
benchmarks, or expert opinions supporting each assessment.]

### [Criterion 2]
[Breakdown with evidence.]

## Trade-Offs
- **[A] wins when:** [conditions favoring A]
- **[B] wins when:** [conditions favoring B]
- **Deciding factors:** [what tips the balance]

## Synthesis
[Integrated recommendation with caveats. State which option suits which use case.
Avoid false equivalence — if one is clearly better for the user's context, say so.]

## Sources
1. [author/org]. "[title]." [url]. Accessed [YYYY-MM-DD].
2. [author/org]. "[title]." [url]. Accessed [YYYY-MM-DD].
```

## Format Selection

| Mode | Default Format | Override With |
|------|---------------|---------------|
| Investigate (Quick) | Quick Answer | — |
| Investigate (Standard) | Research Brief | `--format deep` |
| Investigate (Deep/Exhaustive) | Deep Report | `--format brief` |
| Fact-check | Quick Answer with verdict | `--format deep` |
| Compare | Decision Matrix | `--format deep` |
| Survey | Annotated Bibliography | `--format deep` |

User can always override with `--format brief|deep|bib|matrix`.
