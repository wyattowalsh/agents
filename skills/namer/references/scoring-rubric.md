# Scoring Rubric

All 10 scoring dimensions, hard filters, context presets, and composite formula for Phase 3 ranking.

---

## Contents

1. [Hard Filters](#hard-filters) | 2. [Intrinsic Dimensions](#intrinsic-dimensions) | 3. [Extrinsic Dimensions](#extrinsic-dimensions) | 4. [Context Presets](#context-presets) | 5. [Composite Score Formula](#composite-score-formula) | 6. [Score Interpretation](#score-interpretation)

---

## Hard Filters

Binary disqualifiers. Apply BEFORE scoring. A single failure eliminates the candidate.

### 1. Profanity Check

English profanity, racial slurs, sexual terms, drug slang. Include Leet-speak variants (sh1t, f4ck) and words that sound profane aloud. Zero tolerance.

### 2. Cross-Linguistic Safety

Check against top 10 languages for offensive/embarrassing meanings:

| Language | Common Traps |
|----------|-------------|
| Mandarin | "si" = death; "ji" can mean genitalia |
| Spanish | "culo" = ass; "pedo" = fart/drunk |
| Hindi | "chut" = vulgar anatomy; "lund" = penis |
| Arabic | "kus" = vulgar; "sharmuta" adjacency |
| Portuguese | "pinto" = penis (Brazilian) |
| Bengali | "boka" = fool; "magi" = prostitute |
| Russian | "hui" = vulgar; "suka" = bitch |
| Japanese | "chin" = penis; "shi" = death |
| French | "bite" = penis; "con" = vulgar idiot |
| German | "Fahrt" = journey (English ears); "dick" = fat |

When in doubt: `brave_web_search "<name> meaning <language>"`.

### 3. Brand Collision

- Exact match in same category (same function + same audience) = disqualify
- Phonetic match when spoken = treat as exact match
- Different category = flag as risk, do not disqualify
- Check: `brave_web_search '"<name>" <category>'` — top 5 results are existing product = disqualify

### 4. Length Limits

| Context | Hard Max | Recommended |
|---------|----------|-------------|
| CLI tool | 8 | 3-6 |
| OSS library | 12 | 4-8 |
| Product / Brand / Creative | 15 | 5-12 |

Exceeding hard max = disqualify. Between recommended and max = score penalty on Memorability.

### 5. Pronounceability

- Max 3 consonants in a cluster ("str" OK, "ngths" = fail)
- No word-initial clusters absent from English ("ng-", "ts-" = fail)
- At least one vowel per syllable
- No ambiguous pronunciation with two significantly different readings
- Test: say it confidently without being corrected

### 6. Reserved Words

Disqualify exact matches against: Python/JS/Rust/Go reserved words (`import`, `class`, `def`, `new`, `fn`, `type`, `map`, `range`, `null`, `true`, `false`, `self`, `super`) AND common Unix commands (`ls`, `cd`, `rm`, `cp`, `mv`, `cat`, `grep`, `find`, `test`, `time`, `sort`, `make`, `curl`).

### 7. Special Characters

- Package/library names: no hyphens, underscores, dots, spaces
- CLI tools: lowercase alphanumeric only; single hyphen acceptable for multi-word
- All contexts: no emoji, no unicode beyond ASCII, no leading numbers

---

## Intrinsic Dimensions

Score 0-10. Measure name quality without I/O.

### 1. Phonetic Quality

| Score | Criteria |
|-------|----------|
| 9-10 | Effortless flow; natural stress; sound symbolism aligned; pronounceable in 5+ languages |
| 7-8 | Good flow, minor roughness; clear stress; English + 2-3 languages |
| 5-6 | Unremarkable; stress may be ambiguous; English-only pronunciation |
| 3-4 | Awkward clusters; unclear stress; sound conflicts with meaning |
| 1-2 | Difficult to say; unpleasant sounds |

**Test:** Say aloud 5 times fast. "Have you tried [name]?" Does it flow?

### 2. Semantic Fit

| Score | Criteria |
|-------|----------|
| 9-10 | Immediate conceptual click; rich metaphorical layers; invites storytelling |
| 7-8 | Clear relevance; one strong metaphor; some narrative potential |
| 5-6 | Loose association; requires brief explanation |
| 3-4 | Tangential; meaning misleads; tone mismatch |
| 1-2 | No connection; actively confusing |

Literal descriptions cap at 5 — clear but no resonance.

### 3. Memorability

| Score | Criteria |
|-------|----------|
| 9-10 | 1-2 syllables; strong hook; unique combination; remember after hearing once |
| 7-8 | 2 syllables; good rhythm; remember after hearing twice |
| 5-6 | 2-3 syllables; no hook; might confuse with similar names |
| 3-4 | 3+ syllables; generic; blends into noise |
| 1-2 | Long, forgettable, confusable |

**Length bonus:** 3-4 chars = +2, 5-6 = +1, 7-8 = 0, 9-10 = -1, 11+ = -2 (cap at 10).

### 4. Morphological Flexibility

| Score | Criteria |
|-------|----------|
| 9-10 | Verbs naturally ("Slack me"); nouns cleanly; compounds work ("Stripe Atlas"); supports product family |
| 7-8 | Works as noun and modifier; some compound potential |
| 5-6 | Noun only; awkward as verb; limited compounds |
| 3-4 | Locked to one role; compounds forced |
| 1-2 | Grammatically rigid; cannot extend |

**Tests:** "I'll [name] it" (verb?). "[Name] Pro" (family?). "The [name] ecosystem" (platform?).

### 5. Visual Quality

| Score | Criteria |
|-------|----------|
| 9-10 | Balanced letter heights; good ascender/descender mix; clean URL; strong logo potential |
| 7-8 | Mostly balanced; clean URL; reasonable logo potential |
| 5-6 | Acceptable; some visual monotony |
| 3-4 | Visually awkward; repeated letters stutter |
| 1-2 | Hard to read at small sizes; confusing letterforms |

**Watch for:** "rn" looking like "m"; "cl" like "d"; all-lowercase ambiguity (Ill/ill/III).

---

## Extrinsic Dimensions

Score 0-10. Require I/O (API calls, searches).

### 6. Domain Availability

| Score | Criteria |
|-------|----------|
| 10 | .com available, standard price (<$20/yr) |
| 9 | .com available, premium ($20-200/yr) |
| 7 | .dev/.io available; .com parked under $5K |
| 5 | .ai/.app available; .com parked under $20K |
| 3 | Obscure TLDs only; .com parked $20K+ |
| 1 | Only long-form domain (getname.com) |
| 0 | No reasonable domain at any TLD |

### 7. Registry Availability

| Score | Criteria |
|-------|----------|
| 10 | Available on all target registries |
| 8 | Primary registry + GitHub; 1 secondary taken |
| 6 | Primary registry available; GitHub taken |
| 4 | Primary taken; scoped name available |
| 2 | Primary taken; prefix/suffix variant needed |
| 0 | All registries taken |

**Targets:** CLI = GitHub + Homebrew + language registry. OSS = language registry + GitHub. Product = GitHub. Brand = skip dimension.

### 8. Handle Consistency

| Score | Criteria |
|-------|----------|
| 10 | Available on all target platforms (5+) |
| 8 | 80%+ of targets |
| 6 | 60% of targets; major ones covered |
| 4 | ~40%; prefix/suffix needed on majors |
| 2 | 1-2 platforms only |
| 0 | None available |

**Targets:** CLI = GitHub, Discord. OSS = GitHub, Discord, X. Product = X, LinkedIn, GitHub. Brand = X, Instagram, LinkedIn, YouTube. Creative = YouTube, TikTok, X, Reddit.

### 9. Search Distinctiveness

| Score | Criteria |
|-------|----------|
| 9-10 | <10K results for `"<name>" software`; first page claimable |
| 7-8 | <100K results; first page achievable |
| 5-6 | <1M results; requires sustained SEO |
| 3-4 | >1M results; needs qualifier ("name app") |
| 1-2 | >10M results; essentially unsearchable |

**Penalties:** Common English word = score x0.5. Celebrity/city collision = x0.3. Overloaded acronym = x0.4.

### 10. Typeability

| Score | Criteria |
|-------|----------|
| 9-10 | Home-row keys; 3-5 chars; no stretches; clean tab-completion |
| 7-8 | Comfortable keys; 5-7 chars; one stretch |
| 5-6 | Standard typing; 7-9 chars |
| 3-4 | Awkward reaches; 9-11 chars |
| 1-2 | Special characters or >11 chars |

**Tab-completion test:** Is the 2-3 char prefix unique among common CLI tools? If yes, +1 bonus.

---

## Context Presets

### Intrinsic Weights

| Dimension | CLI | OSS | Product | Brand | Creative | Side Project |
|-----------|-----|-----|---------|-------|----------|-------------|
| Phonetic quality | 10% | 15% | 25% | 30% | 35% | 10% |
| Semantic fit | 15% | 25% | 30% | 30% | 15% | 15% |
| Memorability | 25% | 20% | 25% | 20% | 35% | 20% |
| Morphological flexibility | 10% | 15% | 15% | 15% | 5% | 5% |
| Visual quality | 40% | 25% | 5% | 5% | 10% | 50% |

### Extrinsic Weights

| Dimension | CLI | OSS | Product | Brand | Creative | Side Project |
|-----------|-----|-----|---------|-------|----------|-------------|
| Domain availability | 10% | 15% | 35% | 35% | 25% | 15% |
| Registry availability | 35% | 35% | 5% | 0% | 0% | 20% |
| Handle consistency | 5% | 10% | 20% | 30% | 35% | 5% |
| Search distinctiveness | 20% | 25% | 25% | 25% | 30% | 20% |
| Typeability | 30% | 15% | 15% | 10% | 10% | 40% |

### Intrinsic/Extrinsic Split

| Context | Intrinsic | Extrinsic | Rationale |
|---------|-----------|-----------|-----------|
| CLI Tool | 30% | 70% | Availability and typeability are existential |
| OSS Library | 35% | 65% | Registry availability is #1 blocker |
| Product | 45% | 55% | Brand quality matters; availability still critical |
| Brand | 50% | 50% | Beautiful + unavailable = worthless |
| Creative | 55% | 45% | Memorability and phonetics drive discovery |
| Side Project | 25% | 75% | Find something available and ship |

---

## Composite Score Formula

### Calculation

```text
intrinsic_avg = sum(w_i × score_i) for all 5 intrinsic dimensions
extrinsic_avg = sum(w_i × score_i) for all 5 extrinsic dimensions
composite     = (intrinsic_split × intrinsic_avg) + (extrinsic_split × extrinsic_avg)
final_score   = composite × 10    (normalize to 0-100)
```

Weights `w_i` from context preset tables. Split from Intrinsic/Extrinsic Split table.

### Worked Example (CLI Tool)

Scores: phonetic=7, semantic=6, memorability=8, morphological=5, visual=7, domain=3, registry=9, handle=6, search=8, typeability=9.

```text
intrinsic = (0.10×7) + (0.15×6) + (0.25×8) + (0.10×5) + (0.40×7) = 6.90
extrinsic = (0.10×3) + (0.35×9) + (0.05×6) + (0.20×8) + (0.30×9) = 8.05
composite = (0.30 × 6.90) + (0.70 × 8.05) = 7.71
final     = 77
```

### User Overrides

- Adjust individual dimension weights (must sum to 100% within group)
- Adjust intrinsic/extrinsic split (must sum to 100%)
- Set minimum thresholds per dimension — scores below become soft flags, not eliminations

---

## Score Interpretation

### Composite Score Bands

| Range | Grade | Meaning | Action |
|-------|-------|---------|--------|
| 90-100 | Exceptional | Strong across all dimensions | Register immediately |
| 75-89 | Strong | Minor gaps in 1-2 dimensions | Recommend with noted trade-offs |
| 60-74 | Viable | Compromised in 2-3 dimensions | Present with clear caveats |
| 40-59 | Weak | Significant gaps | Recommend variants or new candidates |
| 0-39 | Not recommended | Fundamental problems | Eliminate from shortlist |

### Dimension Flags

| Condition | Flag |
|-----------|------|
| Any intrinsic < 3 | "Intrinsic weakness: [dimension]" |
| Any extrinsic = 0 | "Availability blocker: [dimension]" |
| Domain = 0 AND product/brand | "Critical: no domain path" |
| Registry = 0 AND CLI/OSS | "Critical: registry taken" |
| Search < 3 | "SEO risk: competes with established terms" |
| Typeability < 4 AND CLI | "Typing friction: consider shorter alternative" |

### Comparison Rules

- 5+ point gap = significant; prefer higher scorer
- <3 point gap = essentially tied; let user's gut decide
- Always show intrinsic and extrinsic sub-scores separately
- Highlight highest dimension as "superpower", lowest as "risk"
