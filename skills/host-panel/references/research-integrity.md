# Research Integrity

Research grounding prevents fake expertise. Use this file before naming any
source, work, author, year, venue, organization, affiliation, or empirical claim.

## Source Status

Every panel has one source status:

| Status | Meaning | Required Label |
|---|---|---|
| `verified` | Current tools found inspectable sources that support the claims being used | "Verified against current sources." |
| `thin` | Sources exist but are sparse, indirect, dated, or one-sided | "Evidence is thin; claims are provisional." |
| `unverified-training-knowledge` | Search/docs are unavailable or not used | "Based on training knowledge - not verified against current literature." |

Do not hide source limitations inside the synthesis. Put the label near the top.

## Source Ladder

Prefer sources in this order:

1. Peer-reviewed papers, official proceedings, official technical reports, standards, laws, and primary documents.
2. Literature reviews, meta-analyses, systematic surveys, and official docs.
3. Established analyses by domain experts with transparent methods.
4. News or commentary only for current events or public-position mapping.
5. General web summaries only for lead discovery, not for final claims.

## Source Ledger

When sources are available, include a compact ledger:

| Field | Meaning |
|---|---|
| `id` | Stable label such as `S1`, `S2`, `S3` |
| `source` | Title or page name plus URL when available |
| `status` | `primary`, `review`, `expert-analysis`, `news`, or `lead-only` |
| `claim_supported` | The exact claim the source supports |
| `viewpoint_represented` | Which tradition, side, or uncertainty this source informs |
| `independence` | `independent`, `same-lineage`, or `unknown` |
| `confidence` | `high`, `medium`, or `low` |

Use sources as citable units: the cited page, paper, or section must be stable,
inspectable, and specific enough to support the claim. Do not cite a broad source
for a narrow claim it does not make.

## Citation Rules

- Cite specific works only when title, author, year, and venue/source are verified.
- If a source is known only from model memory, cite the tradition or research area instead.
- Never fabricate authors, paper titles, publication years, journals, conferences, affiliations, or URLs.
- Do not cite a source merely because it sounds like it belongs in the debate.
- If two sources are not independent, say so and avoid treating them as corroboration.
- If sources disagree, preserve the disagreement in the source ledger and synthesis.
- If no current source is available, write at the tradition level: "research in this area often argues..." rather than naming a fake paper.

## Research Brief

Before personas, produce a brief containing:

1. The source status.
2. The 3-5 strongest sources or the reason sources are unavailable.
3. What is actually contested.
4. Which claims are factual and which are interpretive.
5. Which perspectives are underrepresented or missing.

## Live Debate Handling

For live or fast-moving topics:

- Prioritize recent primary sources and official statements.
- State the date or freshness boundary if it matters.
- Avoid claims like "the current consensus is..." unless the sources support it.
- Separate "this source says" from "the field agrees."

## Integrity Failures

Stop and repair the output if any occur:

- A named work appears without verification.
- A panelist uses "studies show" without a source or scope.
- A rhetorical claim is treated as evidence.
- A source is used for a claim it does not support.
- The final synthesis implies more certainty than the source ledger supports.
