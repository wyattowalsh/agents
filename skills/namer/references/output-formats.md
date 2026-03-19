# Output Formats

Templates for ranked views, name cards, variant tables, and next steps. Read during Phase 4 (presentation).

---

## Structured Output Schema

After all ranked views and cards are produced, assemble a single JSON object matching this schema. Inject it into `templates/dashboard.html` (replace `{}` in `<script id="data" type="application/json">{}</script>`), write the result to `~/.claude/namer/{session-slug}-dashboard.html`, then print the path for the user.

```json
{
  "query": "terminal file manager in Rust",
  "context": "CLI Tool",
  "preset": "cli-tool",
  "generated": "2025-01-15",
  "weights": {
    "intrinsic_split": 0.30,
    "extrinsic_split": 0.70,
    "intrinsic": {
      "memorability": 0.25, "phonetic_quality": 0.10,
      "semantic_fit": 0.15, "morphological_flexibility": 0.10,
      "visual_quality": 0.40
    },
    "extrinsic": {
      "domain_availability": 0.10, "registry_availability": 0.35,
      "handle_consistency": 0.05, "search_distinctiveness": 0.20,
      "typeability": 0.30
    }
  },
  "candidates": [
    {
      "name": "neon",
      "archetype": "Evocative Fragment",
      "rank_composite": 1,
      "rank_intrinsic": 2,
      "composite_score": 87,
      "intrinsic_score": 82,
      "extrinsic_score": 90,
      "rationale": "Short, vivid, high recall. Strong .com + dev registry coverage.",
      "dimensions": {
        "memorability": 9, "phonetic_quality": 8, "semantic_fit": 7,
        "morphological_flexibility": 7, "visual_quality": 8,
        "domain_availability": 10, "registry_availability": 7,
        "handle_consistency": 6, "search_distinctiveness": 6,
        "typeability": 9
      },
      "availability": {
        "domain_com": true, "domain_dev": true, "domain_net": false,
        "github": true, "npm": false, "pypi": true, "crates": true,
        "bluesky": true, "reddit": false, "x_twitter": "parked"
      },
      "domain_prices": { "domain_com": "~$12/yr", "domain_dev": "~$14/yr" },
      "strengths": [
        "4 letters, single syllable — exceptional memorability",
        ".com available — rare for a real English word",
        "Strong metaphor for energy and innovation"
      ],
      "risks": [
        "npm package taken — use scoped @neon/core or neon-cli",
        "~800 search results for \"neon software\" — moderate collision"
      ],
      "next_steps": [
        "Register neon.com (~$12/yr) and neon.dev (~$14/yr)",
        "Claim @neon on GitHub and Bluesky",
        "Use `@neon/core` or `neon-cli` for npm",
        "Run `pip install neon` check on PyPI before claiming"
      ],
      "variants": [
        {
          "name": "neonkit", "type": "Suffix (-kit)",
          "availability": { "domain_com": true, "github": true, "npm": true, "pypi": true },
          "note": "Fully available — suggests toolkit"
        }
      ]
    }
  ],
  "views": {
    "best_names": [0, 2, 1],
    "best_available": [0, 1, 2],
    "best_with_variants": [0, 2]
  }
}
```

**Key rules:**

- `views.*` are arrays of indices into `candidates[]`, pre-sorted for each view
- `availability` values: `true` = available, `false` = taken, `"parked"` = uncertain, `null` = not checked
- All 10 `dimensions` scores are 0–10 scale (matches `score.py` output)
- `domain_prices` only populated for available domains where pricing was looked up

---

## Contents

- [Ranked Table Template](#ranked-table-template)
- [Name Card Template](#name-card-template)
- [Variant Table Template](#variant-table-template)
- [Availability Matrix Template](#availability-matrix-template)
- [Next Steps Template](#next-steps-template)
- [Interactive Refinement Prompts](#interactive-refinement-prompts)

---

## Ranked Table Template

Use for all three views: Best Names, Best Available, Best with Variants.

### Header

Print the view title and description before the table:

```
## Best Available Names

Ranked by composite score (intrinsic quality + availability). Default recommendation.
```

### Table Format

```markdown
| Rank | Name | Archetype | Score | .com | GH | npm | PyPI | X | Rationale |
|------|------|-----------|-------|------|----|-----|------|---|-----------|
| 1 | neon | Evocative Fragment | 87 | ✅ | ✅ | ❌ | ✅ | ⚠️ | Short, vivid, high recall. Strong .com + dev registry coverage. |
| 2 | luminar | Classical Root | 82 | ❌ | ✅ | ✅ | ✅ | ✅ | Latin root suggests illumination. All dev registries clear. |
| 3 | dashkit | Compound Blend | 79 | ✅ | ✅ | ✅ | ✅ | ✅ | Descriptive + memorable. Full availability across all platforms. |
```

### Cell Icons

| Icon | Meaning |
|------|---------|
| ✅ | Available (confirmed via direct API or RDAP) |
| ❌ | Taken (confirmed via direct API or RDAP) |
| ⚠️ | Parked, inactive, or uncertain (search heuristic) |
| ❓ | Unknown (check failed, rate limited, or not attempted) |

### Column Rules

- **Score**: Integer 0-100. Composite for "Best Available", intrinsic-only for "Best Names".
- **Rationale**: 1-2 sentences. Lead with the strongest attribute. Mention key risks if any.
- **Platform columns**: Adapt to context. CLI Tool shows GH/npm/PyPI/Crates/Homebrew. Brand shows .com/X/IG/LinkedIn/YT. Show 5-7 most relevant platforms.

### View-Specific Headers

| View | Title | Sorting | Score Type |
|------|-------|---------|------------|
| Best Names | `## Best Names (by intrinsic quality)` | Intrinsic score descending | Intrinsic only |
| Best Available | `## Best Available Names` | Composite score descending | Composite |
| Best with Variants | `## Best Names with Available Variants` | Intrinsic score descending | Intrinsic (original) |

---

## Name Card Template

Produce one card for the top 3 candidates in each view (9 cards max, deduplicate across views).

```markdown
### #1: neon (Evocative Fragment)

**Composite Score:** 87/100 (Intrinsic: 82 | Extrinsic: 90)

**Scoring Breakdown:**

| Dimension | Score | Weight | Weighted | Notes |
|-----------|-------|--------|----------|-------|
| Memorability | 9 | 20% | 1.80 | 4 letters, single syllable, strong imagery |
| Phonetic quality | 8 | 15% | 1.20 | Open vowels, nasal onset, pleasant cadence |
| Semantic fit | 7 | 20% | 1.40 | Evokes energy/glow — fits dev tools |
| Typeability | 9 | 5% | 0.45 | 4 chars, home row adjacent |
| Search distinct. | 6 | 15% | 0.90 | ~800 results for "neon software" |
| Morphological flex. | 7 | 5% | 0.35 | neon-cli, neonkit, neonjs viable |
| Visual quality | 8 | 5% | 0.40 | Balanced ascenders, clean URL |
| Domain avail. | 10 | — | — | .com ✅ .dev ✅ |
| Registry avail. | 7 | — | — | GitHub ✅ npm ❌ PyPI ✅ |
| Handle consistency | 6 | — | — | Reddit ✅ X ⚠️ Bluesky ✅ |

**Availability:**

| Platform | Status | Notes |
|----------|--------|-------|
| neon.com | ✅ Available | ~$12/yr at Namecheap |
| neon.dev | ✅ Available | ~$14/yr at Google Domains |
| GitHub @neon | ✅ Available | — |
| npm neon | ❌ Taken | neon-cli ✅, @neon/core ✅ |
| PyPI neon | ✅ Available | — |
| X @neon | ⚠️ Inactive | Last post 2019, may be reclaimable |
| Reddit u/neon | ❌ Taken | r/neon available |
| Bluesky @neon | ✅ Available | — |

**Strengths:**
- Exceptional memorability — 4 letters, single syllable, universal recognition
- .com available — rare for a real English word
- Strong metaphor for energy/innovation

**Risks:**
- npm package taken — must use variant or scoped name
- ~800 search results for "neon software" — moderate collision
- Noble gas association may confuse in chemistry contexts

**Next Steps:**
1. Register neon.com (~$12/yr) and neon.dev (~$14/yr)
2. Claim @neon on GitHub, Bluesky, Reddit (r/neon)
3. Use `@neon/core` or `neon-cli` for npm
4. Run `pip install neon` check — PyPI shows available but verify PEP 503 normalization
```

### Card Sizing Rules

| Section | Length |
|---------|--------|
| Scoring breakdown | All 10 dimensions, always |
| Availability table | All checked platforms (skip unchecked) |
| Strengths | 2-4 bullets |
| Risks | 1-3 bullets (omit section if zero risks) |
| Next steps | 2-5 numbered items |

---

## Variant Table Template

Show after the "Best with Variants" ranked table. One section per original candidate.

```markdown
### Variants of "neon"

| Variant | Type | .com | GH | npm | PyPI | X | Notes |
|---------|------|------|----|-----|------|---|-------|
| neonkit | Suffix (-kit) | ✅ | ✅ | ✅ | ✅ | ✅ | Fully available, suggests toolkit |
| neonjs | Suffix (-js) | ✅ | ✅ | ✅ | — | — | Good for JS ecosystem project |
| goneon | Prefix (go-) | ✅ | ✅ | — | — | ✅ | Go ecosystem convention |
| neonlab | Suffix (-lab) | ✅ | ✅ | ✅ | ✅ | ✅ | Suggests experimentation |
| neonr | Vowel drop | ❌ | ✅ | ✅ | ✅ | ✅ | Trendy but less readable |
```

### Variant Type Taxonomy

| Type | Pattern | Examples |
|------|---------|---------|
| Suffix | `{name}-kit`, `-lab`, `-ify`, `-ly`, `-io`, `-js`, `-py` | neonkit, neonify |
| Prefix | `go-`, `un-`, `re-`, `open-`, `use-` | goneon, useneon |
| Vowel drop | Remove vowels or terminal vowel | neonr, neøn → neon |
| Respelling | Phonetic alternative spelling | nomar, noemer |
| Scoped | `@scope/{name}` (npm) or `{org}/{name}` (GitHub) | @neon/core |
| Compound | Combine with second word | neonflow, neonspark |

---

## Availability Matrix Template

Full namespace report. Use when the user runs `check <name>` or asks for a detailed availability audit.

```markdown
## Namespace Report

Generated: {date} | Candidates: {count} | Platforms: {count}

| Name | .com | .dev | .io | GH | npm | PyPI | Crates | X | Reddit | Bluesky | LinkedIn | Search Collision |
|------|------|------|-----|----|-----|------|--------|---|--------|---------|----------|------------------|
| neon | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ⚠️ | ❌ | ✅ | ✅ | Medium (800) |
| luminar | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | Low (120) |
| dashkit | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Low (30) |

**Legend:** ✅ Available | ❌ Taken | ⚠️ Parked/Uncertain | ❓ Unknown/Not Checked
**Search Collision:** Low (<200) | Medium (200-2000) | High (>2000)
```

### Column Selection by Context

| Context | Always Show | Show if Relevant | Skip |
|---------|-------------|------------------|------|
| CLI Tool | .com, .dev, GH, npm/PyPI/Crates, Homebrew | X, Reddit | IG, LinkedIn, YT |
| OSS Library | .com, .dev, GH, npm/PyPI/Crates | X, Discord | IG, LinkedIn, YT |
| Product | .com, .dev, GH, X, LinkedIn | npm/PyPI, IG, YT | Crates, Homebrew |
| Brand | .com, X, IG, LinkedIn, YT | .dev, GH | npm, PyPI, Crates |
| Creative | .com, X, YT, IG, Reddit | .dev, LinkedIn | npm, PyPI, Crates |

---

## Next Steps Template

Produce after the ranked tables and name cards. Group by action type.

```markdown
## Next Steps for "{recommended_name}"

### Domain Registration
- Register **{name}.com** at Namecheap/Porkbun (~${price}/yr)
- Register **{name}.dev** at Google Domains (~${price}/yr)
- Consider **{name}.io** as secondary (~${price}/yr)

### Handle Claiming
- Claim **@{name}** on GitHub → https://github.com/signup
- Claim **@{name}** on X/Twitter → https://x.com/i/flow/signup
- Claim **@{name}.bsky.social** on Bluesky → https://bsky.app
- Claim **u/{name}** and **r/{name}** on Reddit

### Package Initialization
- npm: `npm init {name}` or `npm init @{name}/core`
- PyPI: `uv init {name} && uv build && uv publish`
- Crates: `cargo init {name} && cargo publish`
- Go: `go mod init github.com/{org}/{name}`

### Trademark (if commercial)
- Search USPTO TESS: https://tmsearch.uspto.gov
- File in **Class 9** (software) and/or **Class 42** (SaaS)
- Budget: ~$250-350 per class for TEAS Plus filing
- Timeline: 8-12 months for registration

### Immediate Priority
1. Register domain(s) — domains expire quickly once discovered
2. Claim GitHub handle — needed for code hosting
3. Claim social handles — consistency across platforms
4. Initialize package — publish a placeholder to hold the name
```

### Conditional Sections

| Section | Show When |
|---------|-----------|
| Domain Registration | Always |
| Handle Claiming | Always (include only platforms checked) |
| Package Initialization | CLI Tool, OSS Library, OSS Project contexts |
| Trademark | Product, Brand contexts; or when `--thorough` is set |
| Immediate Priority | Always (reorder items by context priority) |

---

## Interactive Refinement Prompts

Present after the full output. Allow the user to steer follow-up iterations.

```markdown
## Refine Results

- **"More like #N"** — generate new candidates similar to the indicated name
- **"Shorter"** / **"Longer"** — adjust length constraints (e.g., max 5 chars / min 8 chars)
- **"More technical"** / **"More playful"** — shift naming style
- **"Avoid {sounds}"** — exclude phonemes (e.g., "avoid hard K sounds")
- **"Focus on {platform}"** — reprioritize availability for a specific platform
- **"Check {name1} {name2}"** — run availability audit on specific names
- **"Expand {name}"** — generate variants of a specific candidate
- **"Compare {name1} vs {name2}"** — side-by-side detailed comparison
```

### Refinement Dispatch

| User Input | Action |
|------------|--------|
| `more like #3` | Extract archetype + phonetic profile of #3, regenerate 20 candidates with similar traits, re-run Phase 1-4 |
| `shorter` | Set max length to 5, regenerate, re-run full pipeline |
| `longer` | Set min length to 8, regenerate, re-run full pipeline |
| `more technical` | Shift style weights: Classical Roots +20%, Descriptive-Creative +10%, Evocative -10% |
| `more playful` | Shift style weights: Invented Words +20%, Evocative Fragments +10%, Classical -10% |
| `avoid {sounds}` | Add phoneme filter to Phase 1 hard filters, regenerate |
| `focus on {platform}` | Reweight extrinsic scoring: target platform = 40% of extrinsic, others split remainder |
| `check {names}` | Skip Phase 0-1, jump to Phase 2 with provided names |
| `expand {name}` | Skip Phase 0-1, run Phase 2.5 variant generation for the given name |
| `compare {names}` | Skip Phase 0-1, run Phase 2-4 for provided names only, produce side-by-side cards |
