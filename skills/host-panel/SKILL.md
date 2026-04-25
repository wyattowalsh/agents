---
name: host-panel
description: >-
  Facilitate research-grounded panels in roundtable, Oxford, and Socratic
  formats. Use when exploring contested topics from multiple angles. NOT for
  Q&A, code review, or real human opinion simulation.
argument-hint: '"topic" [format] [num-experts]'
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Host Panel

Facilitate research-grounded deliberation across simulated intellectual positions. Surface tensions, source-grounded claims, and disagreement cruxes; never present the panel as evidence of real human group behavior.

**Invocation:** `/host-panel "topic" [format] [num-experts]`

## Dispatch Table

| `$ARGUMENTS` shape | Dispatch | Action |
|---|---|---|
| empty | `empty-help-gallery` | Show the gallery, defaults, supported formats, and ask for a topic. |
| quoted topic + optional format/count | `parse-diagnose-ground` | Parse arguments, run topic diagnostic, then research before personas. |
| unquoted or malformed topic | `clarify-topic` | Ask for a quoted topic; do not infer a panel from ambiguous fragments. |
| format omitted | `auto-select-format` | Select `roundtable`, `oxford`, or `socratic` using `references/topic-diagnostic.md`. |
| invalid format or count outside 2-6 | `argument-error` | Explain supported formats/count range and ask for a corrected invocation. |
| loaded premise or preferred answer | `premise-check` | Challenge the framing before accepting it as the debate motion. |
| settled factual or false-balance topic | `reframe-false-balance` | Reframe toward open implementation, values, uncertainty, or boundary questions. |
| Q&A, code review, one-on-one chat, or real opinion simulation | `redirect-out-of-scope` | Decline the panel framing and redirect to the appropriate interaction style or skill. |

## Empty/Help Gallery

If `$ARGUMENTS` is empty, present this gallery and wait:

| # | Domain | Topic | Format |
|---|---|---|---|
| 1 | Technology | "Should foundation model weights be open-sourced?" | oxford |
| 2 | Philosophy | "What obligations do current generations owe the far future?" | socratic |
| 3 | Policy | "How should cities redesign transit for remote-work patterns?" | roundtable |
| 4 | Science | "Is the replication crisis a crisis of method or incentives?" | roundtable |

Defaults: `roundtable`, 4 experts. Expert range: 2-6. Prefer 4-5; 6 is harder to maintain.

Format-count notes:
- Oxford with 2 experts is direct proposition-vs-opposition.
- Oxford with 3 experts uses one swing panelist.
- Socratic with 2 experts becomes paired inquiry with phase-transition moderation.
- Roundtable with 2 experts becomes structured dialogue, not a faux crowd.

## Progressive Disclosure

Load only what the invocation requires:

1. Always load `references/topic-diagnostic.md`, `references/research-integrity.md`, and `references/debate-research.md` before personas.
2. Load `references/archetypes.md` only after the topic gate identifies the needed traditions.
3. Load `references/moderator-rules.md` and `references/formats.md` immediately before running the panel.
4. Load `references/synthesis.md` before the final product.
5. Do not load every reference up front for weak, malformed, or out-of-scope topics.

Optional parser: run `uv run python skills/host-panel/scripts/parse_args.py $ARGUMENTS` when shell access is available. Use the JSON result for topic, format, and count; if scripts are unavailable, parse manually with the same public contract.

## Classification Gate

### Topic Classes

| Class | Meaning | Default Action |
|---|---|---|
| `settled-factual` | Mostly closed empirical question | Reframe or decline false balance |
| `open-value` | Normative, policy, rights, incentives, or goals | Proceed |
| `controversial-factual` | Live empirical disagreement with credible sources on multiple sides | Proceed with source ledger |
| `speculative` | Future-facing or theory-building | Proceed with uncertainty labels |
| `thin-evidence` | Sparse or indirect literature | Proceed only with explicit gaps |
| `decision-critical` | User is making a practical choice | Proceed with decision implications |

### Gate Actions

| Action | Use When |
|---|---|
| `proceed` | Topic is specific, contestable, and sourceable enough for a panel |
| `reframe` | Topic is too broad, loaded, asymmetric, or better posed another way |
| `clarify` | Topic cannot be parsed or has too little detail |
| `decline-false-balance` | Debate would stage denial of a settled factual matter |

## Pipeline

1. **Parse.** Preserve the public invocation contract. Reject invalid formats, invalid counts, and malformed topics before research.
2. **Diagnose.** Classify topic type, false-balance risk, evidence status, format fit, and whether the user's premise should be challenged.
3. **Ground.** Build a source ledger with 3-5 relevant sources when tools are available. If current sources are unavailable, label the panel as unverified training-knowledge synthesis.
4. **Map perspectives.** Discover traditions from the topic and sources before personas. Prefer methodology diversity over theatrical variety.
5. **Run independent first positions.** Each panelist states an initial position before seeing other panelists' claims. Subsequent rounds critique claims, not people.
6. **Moderate against collapse.** Test convergence, persuasive unsupported claims, majority pressure, and sycophantic acceptance of the user's framing.
7. **Synthesize by trajectory.** The final product maps factual claims, interpretive disagreements, cruxes, evidence gaps, and decision implications. It is not a vote.

## Output Contract

Structure complete outputs with these sections:

- `Topic Gate` - topic class, format choice, false-balance decision, and any premise challenge.
- `Research Status` - verified/thin/unverified status and evidence limits.
- `Source Ledger` - stable source IDs, supported claims, viewpoints, independence, and confidence.
- `Terrain Map` - disciplines, traditions, live tensions, and unresolved uncertainty.
- `Panelist Roster` - methodology cards, not theatrical character sheets.
- `Panel Phases` - format-specific phases from `references/formats.md`.
- `Final Synthesis` - trajectory-aware synthesis from `references/synthesis.md`.
- `Follow-up Options` - 3-4 concrete next moves tied to this panel's cruxes.

For condensed panels, keep abbreviated framing, one sharp exchange, challenge highlights, and full final synthesis. Cut redundant opening positions and repeated back-and-forth.

## Critical Rules

1. Research before personas. Always run topic analysis and source grounding before building the roster.
2. Never stage fake balance. Settled factual claims must be reframed or declined as debate motions.
3. Never claim the panel simulates real human group behavior, polling, consensus, or prediction.
4. Cite real works only. If a title, author, year, venue, or affiliation is not verified, stay at the tradition/framework level.
5. Show source status. Label source grounding as `verified`, `thin`, or `unverified-training-knowledge`.
6. Require independent first positions before cross-talk so later convergence can be inspected.
7. Treat rhetorical confidence as non-evidence. Persuasive claims need sources, logic, or explicit uncertainty.
8. Test convergence. Agreement can reflect model priors, sycophancy, majority pressure, or persuasive falsehood.
9. No straw men. Each position must be the strongest version of its tradition and must include its strongest self-objection.
10. Never skip final synthesis. The synthesis is the intellectual product and must separate facts, interpretations, cruxes, and uncertainty.

## Reference File Index

| File | Content | Read When |
|------|---------|-----------|
| `references/topic-diagnostic.md` | Topic classification, false-balance gate, format selection, and reframe rules | Before personas for every non-empty invocation |
| `references/research-integrity.md` | Source ledger, citation integrity, confidence labels, and provenance rules | Before naming sources or works |
| `references/debate-research.md` | AI debate, role-play, sycophancy, and synthesis research mapped to host-panel rules | Before choosing panel mechanics |
| `references/archetypes.md` | Methodology-card construction and anti-clustering guidance | After topic gate identifies needed traditions |
| `references/moderator-rules.md` | Independent first positions, anti-conformity, turn-taking, and provocation rules | Before the first panel phase |
| `references/formats.md` | Roundtable, Oxford, and Socratic phase structures with stop and failure conditions | After format selection |
| `references/synthesis.md` | Trajectory-aware final synthesis requirements and follow-up options | Before final synthesis |

## Canonical Vocabulary

| Canonical Term | Meaning |
|----------------|---------|
| panel | A simulated deliberation across intellectual positions on a topic |
| expert / panelist | An AI-simulated domain specialist with a defined methodology and evidence standard |
| format | The discussion structure: `roundtable`, `oxford`, or `socratic` |
| source ledger | Stable list of sources, supported claims, viewpoints, independence, and confidence |
| topic gate | Pre-panel classification deciding proceed, reframe, clarify, or decline |
| terrain map | Pre-discussion map of disciplines, traditions, tensions, and uncertainty |
| tradition | Intellectual school, profession, or research program with methodological commitments |
| crux | A claim or assumption that would change the disagreement if resolved |
| convergence | Panelist agreement that must be tested for model-prior collapse or majority pressure |
| anti-conformity | Deliberate protection against consensus pressure and persuasive unsupported claims |
| final synthesis | Trajectory-aware product separating facts, interpretations, uncertainty, and implications |

## After the Panel

For follow-ups, briefly re-ground by reviewing the roster, source status, and central crux before speaking in character or extending the analysis.

If the user is making a practical decision, connect the final synthesis to the decision: weigh trade-offs, evidence gaps, and what would change the recommendation.
