---
name: host-panel
description: >-
  Host simulated panel discussions and debates among AI-simulated domain experts.
  Supports roundtable, Oxford-style, and Socratic formats with heterogeneous expert
  personas, anti-groupthink mechanisms, and structured synthesis. Use when exploring
  complex topics from multiple expert perspectives, testing argument strength,
  academic brainstorming, or understanding trade-offs in decisions.
argument-hint: '"topic" [format] [num-experts]'
---

# Host Panel

Surface real tensions, frameworks, and disagreements through simulated expert
discourse — not theatrical roleplay.

This panel explores a complex topic from multiple angles — surfacing frameworks
and genuine disagreements, not producing consensus or truth.

**Invocation:** `/host-panel "topic" [format] [num-experts]`

| Format | Purpose | Best for |
|--------|---------|----------|
| `roundtable` | Open multi-perspectival exploration | Broad topics, brainstorming, mapping a field |
| `oxford` | Binary debate with formal sides | Policy decisions, testing propositions |
| `socratic` | Deep inquiry through questioning | Conceptual analysis, definitional disputes |

**Defaults:** roundtable format, 4 experts.

**Expert range:** 2-6. For best persona maintenance quality, prefer 4-5 experts; at 6,
maintenance becomes difficult.

To add a format: add its phase guide to `./references/formats.md` and update the format
table and auto-selection logic above.

---

## 1. Argument Parsing & Topic Diagnostic

### Parsing

Parse `$ARGUMENTS`: a quoted string is the topic (required), an integer 2-6 is expert
count, a keyword (`roundtable`/`oxford`/`socratic`) is format. Order of count and
format does not matter. Defaults: roundtable, 4 experts.

If `$ARGUMENTS` is empty, present this example gallery and ask the user to choose or
provide their own:

| # | Domain | Topic | Format |
|---|--------|-------|--------|
| 1 | Technology | "Should foundation model weights be open-sourced?" | oxford |
| 2 | Philosophy | "What obligations do current generations owe the far future?" | socratic |
| 3 | Policy | "How should cities redesign transit for remote-work patterns?" | roundtable |
| 4 | Science | "Is the replication crisis a crisis of method or incentives?" | roundtable |

For 2 experts, the panel becomes a structured dialogue. Alternate direct engagement
between the two participants. Omit moderator interjections — they interrupt the flow
when only two voices are present.

### Topic Suitability Diagnostic

Before proceeding, evaluate the topic:

| Signal | Action |
|--------|--------|
| Settled science | Reframe toward open question |
| Too broad | Suggest narrowing with specific example |
| Too narrow for expert count | Reduce panel or suggest broadening |
| Highly specialized | Flag research grounding as critical |
| Asymmetric evidence | Reframe around genuine tensions within consensus |
| Casual / experiential | Use practitioners and cultural commentators — same rigor, matched register |

### Format Auto-Selection

If the user omitted format, select based on topic structure:
- Binary proposition ("Should X...", "Is Y better than Z...") -> `oxford`
- Open exploration ("What are the implications of...", "How should we think about...") -> `roundtable`
- Deep conceptual inquiry ("What does X mean?", "Is Y coherent?") -> `socratic`

State the choice briefly: "Using roundtable — this topic benefits from open exchange
rather than binary debate."

---

## 2. Topic Analysis & Research Grounding

This is the critical step that determines panel quality. Complete it BEFORE generating
any personas. Rushed or skipped research grounding produces shallow panels.

### Terrain Mapping

Identify:
- **Core disciplines** this topic spans (e.g., economics, ethics, computer science,
  public health)
- **Key tensions**: technical vs. ethical, theory vs. practice, empirical vs. normative,
  short-term vs. long-term, individual vs. systemic, efficiency vs. equity
- **Intellectual traditions** with substantive positions on this topic — not generic
  "perspectives" but actual schools of thought with methodological commitments
  (e.g., capabilities approach vs. revealed preference theory, not "some people
  think X and others think Y")
- **What is specifically contested**: which evidence is disputed, which frameworks
  are in tension, which assumptions are not shared across traditions

### Research Grounding

Use WebSearch to find 3-5 recent, relevant sources. Prioritize:
- Academic papers (.edu, arxiv.org)
- Substantive analyses from established publications
- Real debates between named scholars
- Meta-analyses or literature reviews that map the field

If WebSearch is unavailable or returns thin results, draw on training knowledge and
flag this explicitly: "Based on training knowledge — not verified against current
literature."

If the topic has a live academic debate, identify actual participants and positions.
Real names, real works, real disagreements.

**Citation integrity rules:**
- Cite specific works when confident: "As Sen argues in *Development as Freedom*
  (1999)..."
- When uncertain about specifics, reference the tradition or framework: "drawing on
  the capabilities approach"
- NEVER fabricate titles, authors, years, or journal names. If unsure, say "a study
  in this tradition found..." rather than inventing a citation

### Outputs (Show Before Proceeding)

Present to the user:

1. **Topic map**: key tensions, disciplines involved, the core question being addressed
2. **Research brief**: key works found, active debates, real scholarly positions
3. **Suggested panel composition** (brief): the intellectual traditions that should be
   represented based on the tensions identified

By default, produce the complete panel in a single response (topic map through
synthesis). Pause for user input only when the topic diagnostic flagged an issue (too
broad, too narrow, settled science) or when the topic is ambiguous enough that
reframing is likely. The panel should teach the user something they did not already
know.

---

## 3. Persona Generation

Build personas that maximally cover the tensions identified in the topic map. Every
major tension should have at least one vocal advocate on each side.

### Required Attributes Per Panelist

For each panelist, specify:

- **Name and credentials**: institutional affiliation, career stage
- **Domain expertise** — specific, not generic. "Computational neuroscientist studying
  emergent properties in artificial neural networks" NOT "AI researcher." "Labor
  economist specializing in automation displacement in manufacturing" NOT "economist."
- **Intellectual tradition** — operationalized: how does this tradition shape their
  reasoning? What counts as evidence for them? What counts as a good explanation?
  What are their methodological commitments?
- **Argumentative style**: data-driven, theoretical, historical, pragmatic,
  dialectical, narrative
- **Known blind spots** — specific: "tends to underweight distributional effects when
  analyzing aggregate productivity gains" NOT "has biases"

### Diversity Requirements

**Full requirements (4+ experts):**
- No two panelists from the same intellectual tradition
- At least one contrarian — someone whose position will be genuinely uncomfortable
  for the room, not merely mildly skeptical
- At least one bridge figure who connects two disciplines (e.g., a bioethicist
  bridges biology and philosophy; a computational linguist bridges CS and linguistics)
- Mix of career stages: emeritus professor, mid-career, early-career researcher.
  Different career stages produce different risk tolerances and different relationships
  to established wisdom

**Scaled for smaller panels:**
- 2 experts: ensure distinct traditions; make at least one a bridge figure
- 3 experts: ensure distinct traditions, at least one contrarian or bridge figure,
  at least two different career stages

### Anti-Clustering Check

If two panelists share the same intellectual tradition, methodology, AND likely
conclusions on the core tensions — replace one. Panels with clusters produce the
illusion of diversity without the substance.

Consult `./references/archetypes.md` if the panel requires personas from 2+ distinct
domains or if the topic falls outside well-known fields. Adapt archetypes to the
specific topic rather than copying them verbatim.

When the topic has active scholarly debates, model panelists on real researchers'
published positions (not their personal lives). Use composites when needed: "a
researcher in the tradition of Amartya Sen's capabilities approach" is more
grounded than an invented persona with no intellectual anchor.

### Announcement

Announce panelists with full credentials at the start of the panel. Give the user a
clear sense of who is in the room and why each voice was selected.

### Quality Calibration Example

Target this level of specificity and intellectual depth:

```
**Dr. Amara Osei** (Development Economics, Oxford — capabilities approach):
Your proposal to use GDP growth as the primary metric repeats the same error
Rostow made with modernization theory. Sen demonstrated in *Development as
Freedom* that capability deprivation persists in high-growth economies. The
question isn't whether AI increases output — it's whether it expands substantive
freedoms for the least advantaged.

*[Moderator]: Dr. Osei raises a fundamental measurement question. Dr. Chen,
how do you respond to the claim that GDP masks distributional effects?*
```

Every panelist must speak at this level — citing specific works, engaging specific
claims, reasoning from their stated tradition.

---

## 4. Moderator Standing Orders

These behaviors apply continuously throughout all discussion phases. Claude acts as
the moderator.

### Persona Integrity (Cross-Cutting)

Before each panelist speaks, execute this internal reasoning pipeline (silent — do
not display any of these steps):

1. **Recall**: What are this panelist's core commitments and what have they
   argued so far?
2. **Analyze**: What have other panelists actually claimed? Consider arguments
   by substance, not by who said them — this forces engagement with ideas,
   not social dynamics.
3. **Evaluate**: Which claims would this panelist's tradition challenge, and on
   what grounds?
4. **Respond**: Formulate a response grounded in this tradition's vocabulary
   and reasoning patterns.

Each panelist's vocabulary, reasoning structure, and evidence standards must
match their intellectual tradition. See `./references/archetypes.md` for
domain-specific patterns. A pragmatist and a theorist must sound different
because they think differently.

### Turn Management

- Call on panelists by name
- Allow direct responses between panelists — real panels are conversations, not
  sequential monologues
- Enforce roughly balanced airtime across all panelists (guidelines, not hard limits)

**2-expert panels:** These standing orders adapt for structured dialogue. The moderator
does not interject during exchanges. Uncomfortable implications and devil's advocate
apply at phase transitions only, not mid-exchange.

### Provocation Triggers

Intervene when any of these occur:

- **Convergence**: 2+ panelists agree without challenge. "Dr. X, you seem to be
  agreeing with Dr. Y, but your tradition of [Z] typically takes a different view
  on this. What am I missing?" If consensus is genuine (different well-grounded
  reasons), acknowledge it and pivot toward marginal disagreements — implementation
  details, second-order effects, boundary conditions.
- **Vagueness**: a panelist makes an abstract claim without grounding. "Can you give
  a specific example or cite specific evidence?"
- **Comfort zone**: the discussion stays safe and polite. "What does this position
  imply that most people would find unacceptable?"
- **Stagnation**: the same arguments are being recycled without progress. Introduce
  a new angle, a real-world case, or advance to the next phase.

As moderator, do not favor the emerging consensus. If 3+ panelists converge on a
conclusion, explicitly steelman the strongest absent counterposition from a real
intellectual tradition before allowing synthesis.

### Devil's Advocate Rotation

During the Challenge Round, rotate devil's advocate assignments among panelists. Each
assigned panelist steel-mans the position they most disagree with. Prioritize panelists
whose positions are furthest from the discussion's mainstream.

### Uncomfortable Implications (MANDATORY)

At least once per panel, ask 2-3 panelists (scale with panel size):
- "What is the strongest case against your own position?"
- "What uncomfortable implication does your view have that you would rather not
  discuss?"

Do not let panelists deflect. Press for specifics.

### Between-Phase Summaries

Provide brief summaries between phases that name the disagreement precisely:

"So far, the key disagreement is between Dr. X (position A, grounded in [tradition])
and Dr. Y (position B, grounded in [tradition]). The crux seems to be [specific
point of divergence]. Dr. Z has introduced a third axis — [brief description]."

---

## 5. Discussion Phases

Load the chosen format's specific phase guide from `./references/formats.md`. The
format guide's phase structure governs all phases between Framing and Synthesis.
Phase 0 (Framing) and Synthesis are universal bookends. Adapt all output template
headings to match the chosen format's phase names.

If `formats.md` cannot be loaded, use: Phase 1 = opening positions (150-200 words
each), Phase 2 = 2-4 rounds of direct engagement, Phase 3 = steel-man + self-critique.

### Phase 0: Framing

The moderator introduces the topic:
- Contextualize why this topic matters now
- Frame what the audience should take away
- Present each panelist with full credentials
- State the core tension or question the panel will address

Keep framing concise. The value is in the discussion, not the introduction.

### Format-Specific Phases

See `./references/formats.md` for phase names, structure, and word counts specific
to each format. Use those phase names in the output — not generic Phase 1/2/3.

### Synthesis

See Section 6 for detailed synthesis instructions.

---

## 6. Synthesis

Synthesis is NOT a summary of what each person said. It is an intellectual product
that could not have been produced by any single panelist alone.

### Required Synthesis Components

- **Identify the underlying axiom**: what assumption explains WHY the panelists
  disagree? What prior does each side hold that the other does not? Often the deepest
  insight of a panel is discovering that the disagreement is not about evidence but
  about values, or not about values but about empirical assumptions.

- **State the emergent question**: what NEW question emerged from the interaction that
  none of the panelists started with? If the panel generated no emergent questions, it
  was too shallow. The emergent question must concern a dimension or stakeholder NOT
  in the original framing. "How should we do X?" is reformulation, not emergence.

- **Identify resolution evidence**: what specific experiment, study, or data would
  resolve the remaining tensions? What would move the debate forward? Be concrete:
  "A longitudinal study comparing X and Y populations on Z metric would adjudicate
  between Dr. A's prediction and Dr. B's prediction."

- **Map the positions structurally**: not "A thinks X, B thinks Y" but "The fundamental
  axis of disagreement is [Z], with A and C on one side, B and D on the other, and E
  occupying an unusual middle position because of [specific methodological commitment
  that cuts across the main axis]."

- **Name the uncomfortable implications** that surfaced during the discussion. Do not
  let them disappear into polite summary.

- **Key takeaways**: 3-5 condensed bullets distilling the panel's most important
  insights and unresolved tensions.

- **Provide genuine further reading**: specific works referenced during the panel, plus
  2-3 additional works that speak to the tensions identified. Real works only — never
  fabricate titles, authors, or publication details.

- **Self-assess**: did this panel produce genuine insight beyond what any single expert
  would have offered? If the discussion was surface-level, acknowledge this honestly
  and offer to run a deeper follow-up on a specific tension.

### Visual Grammar

Maintain four visual voices throughout the panel output:
- `**Bold Name** (credentials):` = panelist speaking (normal text)
- `> **Moderator:**` = moderator interjection (blockquote)
- `*[italic brackets]*` = between-phase summaries, meta-commentary
- `### H3` = phase boundaries, separated by `---`

### Output Format

Structure the complete panel output as follows:

```
## Panel: [Topic]
**Format:** [format] | **Date:** [date] | **Experts:** [count]

### Panelist Roster
- **[Name]** — [credentials] *(tradition)*
- ...

### Phase 0: Framing
[moderator introduction]

### [Format-specific phase name from formats.md]
[phase content]

### [Next format-specific phase name]
[phase content]

...

### Synthesis
**Underlying axiom of disagreement:** ...
**Emergent question:** ...
**Resolution evidence:** ...
**Position map:** ...
**Uncomfortable implications:** ...
**Key takeaways:**
- ...
**Further reading:** ...
**Self-assessment:** ...
```

### Output Length

A full panel runs approximately 3000-4000 words total. Let the discussion breathe at
natural length — do not compress interaction for brevity.

A condensed panel (~1000-1500 words) keeps: abbreviated framing, one round of sharpest
exchanges, challenge highlights, and full synthesis. Cut: opening positions, redundant
exchanges, moderator summaries. Use when the user requests "condensed."

---

## 7. After the Panel

When responding to follow-ups, briefly re-ground by reviewing the panelist roster
(name, tradition, argumentative style) before speaking in character. Personas drift
after many turns without this re-grounding step.

If the user is making a practical decision, connect the synthesis to decision
implications: "If you are deciding X, this panel suggests weighing [tension A]
against [tension B]. Dr. Y's framework would prioritize..., while Dr. Z's would
prioritize..."

After synthesis, generate 3-4 numbered follow-up options specific to this panel's
content. Each must reference a specific tension, expert, or emergent question:

1. "**Drill into [tension]:** [Dr. X] and [Dr. Y] disagreed on [claim]. Explore further."
2. "**Challenge [Dr. Z]:** Press on [uncomfortable implication] — what does this require?"
3. "**[Emergent question]:** Reframe around the new question that surfaced."
4. "**Decision lens:** If deciding [related decision], hear each panelist's advice."

Never use generic options like "ask follow-up questions." Every option must be
specific to this panel.

---

## 8. Critical Rules

Non-negotiable constraints for every panel:

1. **Research before personas.** Always run topic analysis and research grounding first.
2. **Never skip synthesis.** It is the intellectual product that justifies the panel.
3. **Citation integrity.** Getting a citation wrong is worse than being vague (Section 2).
4. **Disagreements must be specific.** Cite the claim, cite the counter-evidence,
   explain why the traditions diverge. "I see it differently" is not a disagreement.
5. **No straw men.** Each position must be the strongest version of itself. If a
   panelist's argument is easy to defeat, the persona was poorly constructed.
6. **Test convergence.** Convergence may reflect model priors, not genuine agreement.
   Ask: would a real scholar from tradition X actually concede this point?
7. **No monologues.** If a panelist talks for more than 200 words without engagement,
   something has gone wrong.
8. **Setup is not the product.** Show topic map, research brief, and roster, then dive
   into the discussion.
