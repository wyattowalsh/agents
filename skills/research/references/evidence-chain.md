# Evidence Chain

Structure standards for research findings and their provenance. Read when structuring evidence at any wave.

## Finding Template

Every finding must include all required fields. Optional fields are included when applicable.

```
FINDING RR-{seq:03d}: [Claim statement — one clear declarative sentence]
  CONFIDENCE: [0.0-1.0]
  EVIDENCE:
    1. [source_tool] [url] [YYYY-MM-DD HH:MM UTC] — "[excerpt, max 100 words]"
    2. [source_tool] [url] [YYYY-MM-DD HH:MM UTC] — "[excerpt, max 100 words]"
  CROSS-VALIDATION: [agrees|contradicts|partial|unverified] across [N] independent sources
  BIAS MARKERS: [none | comma-separated list with category labels]
  GAPS: [none | what additional evidence would strengthen this finding]
```

### Required Fields

| Field | Description | Constraints |
|-------|------------|-------------|
| Finding ID | Unique identifier | `RR-{seq:03d}` format (e.g., RR-001, RR-002) |
| Claim | The assertion being reported | One declarative sentence; must be falsifiable |
| Confidence | Numeric score | 0.0-1.0 per confidence-rubric.md |
| Evidence | List of provenance items | Minimum 1; minimum 2 for confidence >= 0.7 |
| Cross-validation | Agreement status | One of: `agrees`, `contradicts`, `partial`, `unverified` |
| Bias markers | Detected biases | `none` or list from 10 bias categories |
| Gaps | Missing evidence | `none` or description of what would strengthen the finding |

### Finding ID Convention

- Format: `RR-{seq:03d}` (Research Result, zero-padded 3-digit sequential)
- Sequence is per-session, starting at RR-001
- IDs are never reused within a session, even if a finding is discarded
- Discarded findings retain their ID with `[DISCARDED]` prefix

## Provenance Format

Each evidence item carries full provenance to enable verification.

```
[tool_name] [url_or_identifier] [YYYY-MM-DD HH:MM UTC] — "[excerpt]"
```

| Component | Description | Example |
|-----------|------------|---------|
| tool_name | MCP tool that retrieved the evidence | `brave-search`, `context7`, `arxiv` |
| url_or_identifier | Source URL, DOI, or document path | `https://docs.python.org/3/...`, `doi:10.1234/...` |
| access_timestamp | When the evidence was retrieved | `2026-02-27 14:30 UTC` |
| excerpt | Relevant text from the source | Max 100 words, direct quote or faithful paraphrase |

**Rules for URLs:**
- Use the most stable URL available (permalink > search result)
- For academic papers, include DOI when available
- For context7 results, cite the library name and doc section
- For deepwiki results, cite the repository and topic path

## Excerpt Guidelines

Excerpts anchor findings to specific source text. Follow these rules:

1. **Maximum 100 words** — trim to the most relevant passage
2. **Direct quotes preferred** — wrap in quotation marks: `"exact text from source"`
3. **Paraphrases permitted** — prefix with `[paraphrase]`: `[paraphrase] The doc states that...`
4. **Never fabricate text** — if you cannot extract a relevant excerpt, write `[no direct excerpt; finding based on source structure/content]`
5. **Preserve technical terms** — do not simplify code, API names, or domain terminology in excerpts
6. **Include surrounding context** — if a sentence is ambiguous alone, include the preceding or following sentence

## Cross-Validation Status Values

| Status | Definition | Confidence Implication |
|--------|-----------|----------------------|
| `agrees` | 2+ independent sources support the same claim | Eligible for 0.7+ |
| `contradicts` | 1+ credible source asserts the opposite | Flag as contradiction; report both sides |
| `partial` | Sources agree on core claim but differ on details | Score core and details separately |
| `unverified` | Only one source found, or no cross-validation attempted | Cap at 0.6 |

## Citation Standards

Format citations in output as a numbered bibliography at the end of the synthesis.

### Bibliography Entry Format

```
[N] Author/Organization. "Title." Source/Publication. Date. URL
```

**Examples:**
```
[1] Python Software Foundation. "sqlite3 — DB-API 2.0 interface." Python 3.12 Documentation. 2026. https://docs.python.org/3/library/sqlite3.html
[2] Smith, J. et al. "Scaling Language Models." arXiv:2401.12345. 2024-01-15. https://arxiv.org/abs/2401.12345
[3] Mozilla Developer Network. "Fetch API." MDN Web Docs. 2026-01-10. https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
```

**Rules:**
- Number citations sequentially in order of first appearance in the text
- Use in-text references as `[N]` — e.g., "Python's sqlite3 module supports this pattern [1]."
- Include URL for every citation — if no URL exists, note the access method (e.g., "via context7 query")
- Omit author for organization-authored docs; use organization name instead
- For academic papers, include arXiv ID or DOI
- For web pages, include access date if content may change

## Finding Lifecycle

Findings progress through states as waves advance:

| State | Set During | Meaning |
|-------|-----------|---------|
| Draft | Wave 1 | Initial claim from broad sweep; not yet validated |
| Validated | Wave 2 | Deep dive confirmed with additional evidence |
| Verified | Wave 3 | Passed cross-validation and bias audit |
| Discarded | Any wave | Evidence insufficient or actively contradicted |
| Contested | Wave 3 | Cross-validation found contradicting sources; reported with both sides |
