# Output Formats

Templates for all skill outputs. Read when formatting any prompt-engineer
skill deliverable.

## Diagnostic Scorecard

Used by Analyze (Mode B) step 4.

```
DIAGNOSTIC SCORECARD
| Dimension    | Score (1-5) | Assessment                              |
|--------------|-------------|-----------------------------------------|
| Clarity      | {N}         | {One-line justification}                |
| Completeness | {N}         | {One-line justification}                |
| Efficiency   | {N}         | {One-line justification}                |
| Robustness   | {N}         | {One-line justification}                |
| Model Fit    | {N}         | {One-line justification}                |
| **Total**    | **{N}/25**  |                                         |

Overall: {One-sentence summary of prompt health}
Priority improvements: {Top 2-3 dimensions to address}
```

**Scoring guide:**
- 1: Fundamentally broken — causes failures or security issues
- 2: Significant problems — works sometimes, fails on edge cases
- 3: Adequate — works for common cases, room for improvement
- 4: Good — handles most cases well, minor issues
- 5: Excellent — robust, efficient, well-suited to model

## Audit Report

Used by Analyze (Mode B), report-only.

```
AUDIT REPORT: {Prompt Name or Description}
Target model: {Model name} ({model class})
Audit date: {Date}

EXECUTIVE SUMMARY
{1-3 sentences: overall assessment, critical findings count, recommendation}

FINDINGS
| # | Severity | Category | Finding | Location |
|---|----------|----------|---------|----------|
| 1 | Critical | {lens}   | {desc}  | {where}  |
| 2 | High     | {lens}   | {desc}  | {where}  |
| ...                                            |

DETAILED FINDINGS

### Finding 1: {Title}
**Severity:** Critical
**Category:** {Ambiguity | Security | Robustness | Efficiency}
**Location:** {Line range or section of the prompt}
**Description:** {What the issue is}
**Impact:** {What goes wrong because of this issue}
**Remediation:** {How to fix it}

{Repeat for each finding}

ANTI-PATTERNS DETECTED
{List of matched anti-patterns from anti-patterns.md, or "None detected"}

MODEL-FIT ASSESSMENT
{Is the prompt well-suited to its target model class? Key observations.}

OVERALL RISK: {Critical | High | Medium | Low}
RECOMMENDED NEXT: {Mode B (Analyze) | Mode D (Evaluate) | Deploy with monitoring}
```

## Clarify / Refuse

Use when dispatch remains ambiguous after the auto-detect heuristic, or when the
request is outside prompt-engineer scope.

```
CLARIFY / REFUSE

Classification: {Ambiguous prompt-vs-request | Out-of-scope}
Why: {One or two sentences explaining the ambiguity or scope boundary}

Next step:
- {Ask which mode the user wants: craft, analyze, audit, convert, or evaluate}
or
- {Redirect to the better-fit skill or tool and explain why}
```

## Conversion Diff

Used by Convert (Mode C) step 7.

```
CONVERSION: {Source Model} → {Target Model}

CONVERSION PLAN
| # | Change | Type | Reason |
|---|--------|------|--------|
| 1 | {desc} | Direct map | {why} |
| 2 | {desc} | Adaptation | {why} |
| 3 | {desc} | Removal | {why} |
| 4 | {desc} | New feature | {why} |

SIDE-BY-SIDE

Source ({Source Model}):
```
{original prompt section}
```

Target ({Target Model}):
```
{converted prompt section}
```

Change: {What changed and why}

---

{Repeat for each significant change}

BEHAVIORAL DIFFERENCES TO EXPECT
- {Difference 1: what will behave differently and why}
- {Difference 2}

FEATURES GAINED: {List of target model features now leveraged}
FEATURES LOST: {List of source model features with no equivalent}

RECOMMENDED: Test with Mode D (Evaluate) using the same test cases on both models
```

## Evaluation Framework

Used by Evaluate (Mode D) step 8.

```
EVALUATION FRAMEWORK: {Prompt Name}
Target model: {Model name}
Created: {Date}

SUCCESS CRITERIA
| # | Criterion | Type | Definition |
|---|-----------|------|------------|
| 1 | {name}    | Functional | {what it means to pass} |
| 2 | {name}    | Quality | {what it means to pass} |
| 3 | {name}    | Safety | {what it means to pass} |

TEST SUITE

### Golden Set ({N} cases)
| # | Input Summary | Expected Behavior | Pass Criteria |
|---|--------------|-------------------|---------------|
| 1 | {brief}      | {expected}        | {how to judge} |

### Edge Cases ({N} cases)
| # | Input Summary | Expected Behavior | Pass Criteria |
|---|--------------|-------------------|---------------|

### Adversarial Cases ({N} cases)
| # | Input Summary | Expected Behavior | Pass Criteria |
|---|--------------|-------------------|---------------|

SCORING RUBRIC
| Dimension | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|----------|--------------|---------------|
| {dim 1}   | {desc}   | {desc}       | {desc}        |
| {dim 2}   | {desc}   | {desc}       | {desc}        |

LLM-AS-JUDGE PROMPT (if applicable):
{Complete judge prompt ready for use}

RECOMMENDED TOOLS: {Promptfoo | Braintrust | Langfuse}
CI/CD INTEGRATION: {Suggested pipeline configuration}
BASELINE EXPECTATIONS: {Expected scores from current prompt version}
```

## Harden Report

Used by Harden (Mode E).

```
HARDEN REPORT: {Prompt Name}
Target model/provider: {Model and API surface}
Trust boundary: {trusted instructions vs untrusted inputs/tool results/retrieved docs}
Risk level: {Low | Medium | High | Critical}

ATTACK SURFACE
| Surface | Trust level | Failure mode | Control |
|---------|-------------|--------------|---------|
| User input | {trusted/untrusted} | {risk} | {mitigation} |
| Retrieved docs/tool results | {trust} | {risk} | {mitigation} |

FINDINGS
| # | Severity | Finding | Evidence class | Fix |
|---|----------|---------|----------------|-----|

HARDENED PROMPT CHANGES
{Before/after or patch-style prompt deltas}

RESIDUAL RISKS
{What prompt-only controls cannot guarantee}

REQUIRED EVALS
{Direct injection, indirect injection, extraction, tool abuse, output escape, long input}
```

## Tool Definition Review

Used by Tool (Mode F).

```
TOOL DEFINITION REVIEW: {Tool Name}
Target model/provider: {Model and API surface}
Permission class: {read-only | write | destructive | external-network | sensitive-data}

SCORECARD
| Dimension | Score | Finding |
|-----------|-------|---------|
| Name clarity | {1-5} | {assessment} |
| Description specificity | {1-5} | {assessment} |
| Parameter schema | {1-5} | {assessment} |
| Error contract | {1-5} | {assessment} |
| Permission safety | {1-5} | {assessment} |

RECOMMENDED TOOL DESCRIPTION / SCHEMA
{Rewritten model-facing description or schema delta}

ADJACENT TOOL CONFLICTS
{Overlap and routing guidance}

REQUIRED EVALS
{Bad args, omitted optionals, unsafe call, wrong-tool attempt, tool-result injection}
```

## PromptOps Plan

Used by PromptOps (Mode G).

```
PROMPTOPS PLAN: {Prompt Name}
Owner: {Team/person}
Target model/provider: {Model and API surface}
Provider facts last verified: {Date + source}

VERSIONING
{Prompt source of truth, version identifier, variables, rollback target}

EVAL GATES
| Gate | Threshold | Blocks rollout? |
|------|-----------|-----------------|
| Golden pass rate | {threshold} | yes/no |
| Regression failures | {threshold} | yes/no |
| Safety failures | {threshold} | yes/no |

ROLLOUT
{Shadow -> canary -> partial -> full, with stop conditions}

MONITORING
{Quality, schema-valid rate, refusal rate, tool-call rate, cost, latency, drift signals}

ROLLBACK
{Trigger, owner, exact prior prompt/model version}
```

## Provider Claim Audit

Used whenever recommendations depend on a current provider/model fact.

```
PROVIDER CLAIM AUDIT
Claim: {Recommendation}
Provider/model/API: {Exact surface}
Evidence class: {official-doc | provider-guide | research | community-heuristic | single-study}
Source checked: {URL or reference section}
Last verified: {YYYY-MM-DD}
Stale after: {YYYY-MM-DD}
Scope: {Where this claim applies}
Caveats: {Known limitations or conflicts}
Required local eval: {How to validate before rollout}
```

## Rationalization Audit

Used when adding or revising critical rules.

```
RATIONALIZATION AUDIT
| Rule | Likely dodge | Required counter/check |
|------|--------------|------------------------|
| {rule} | {how a model might skip it} | {observable artifact or command} |
```

## Annotated Prompt

Used by Craft (Mode A) step 6.

```
ANNOTATED PROMPT: {Description}
Target model: {Model name} ({model class})
Architecture: {Pattern used}
Caching strategy: {Summary}

{The complete prompt with inline annotations}

<!-- RATIONALE: Role definition establishes expertise and tone -->
<system>
You are a {role}...
</system>

<!-- RATIONALE: Static context placed early for cache efficiency -->
<context>
{Background information}
</context>

<!-- RATIONALE: Core task uses direct instruction pattern -->
<task>
{Task description}
</task>

<!-- RATIONALE: Constraints kept minimal to avoid over-specification -->
<constraints>
{Rules}
</constraints>

<!-- RATIONALE: Output example preferred over abstract format description -->
<output_format>
{Format specification with example}
</output_format>

---
MODEL-CLASS ASSUMPTIONS: {What model class this prompt targets and why}
EVAL CRITERIA: {What "working correctly" means for this prompt}
NEXT STEPS: Run Mode D (Evaluate) to build a test suite
```

## Changelog

Used by Analyze (Mode B) step 9.

```
CHANGELOG: {Prompt Name}
Optimized: {Date}
Target model: {Model name}

| # | Change | Before | After | Rationale |
|---|--------|--------|-------|-----------|
| 1 | {desc} | `{old}` | `{new}` | {technique or principle} |
| 2 | {desc} | `{old}` | `{new}` | {technique or principle} |

SCORE CHANGE
| Dimension    | Before | After | Delta |
|--------------|--------|-------|-------|
| Clarity      | {N}    | {N}   | {+/-} |
| Completeness | {N}    | {N}   | {+/-} |
| Efficiency   | {N}    | {N}   | {+/-} |
| Robustness   | {N}    | {N}   | {+/-} |
| Model Fit    | {N}    | {N}   | {+/-} |
| **Total**    | **{N}**| **{N}**| **{+/-}** |

REMAINING RISKS: {Issues not addressed in this optimization}
RECOMMENDED NEXT: {Mode D (Evaluate) | Mode B audit | Deploy}
```
