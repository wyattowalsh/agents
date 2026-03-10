# Composition Patterns

6 multi-tool sequences for problems that benefit from chaining reasoning methods.

---

## Context Transfer Protocol

Apply this protocol at every method transition:

1. Produce a **<=100 word summary** of key findings from the current method.
2. **Include:** Top claims with confidence, unresolved questions, constraints discovered.
3. **Exclude:** Method-specific scaffolding, low-confidence tangents, exploration dead-ends.
4. Feed the summary as initial context to the next method.

---

## Pattern 1: Sketch-Detail

**Sequence:** `aot-light` → `atom-of-thoughts` (full)

**When to use:**
- Problem is clearly decomposable but scope is unclear.
- You need a quick structural overview before committing to deep analysis.
- Initial decomposition might reveal the problem is simpler (or harder) than expected.

**Signals:** "Analyze", "break down", "understand the structure of" + large/unclear scope.

**How to transfer context:**
- Carry forward the atom structure and top-level decomposition from aot-light.
- Carry any atoms with confidence >= 0.7.
- Discard low-confidence atoms and tentative branches — they will be re-derived with more depth.
- The aot-light structure becomes the initial skeleton for full aot's dependency DAG.

**Expected token budget:** Medium (Tier 1 + Tier 3)

**Example:** "Analyze the full dependency chain of our authentication system" — sketch the top-level components with aot-light, then drill into each with full atom-of-thoughts.

---

## Pattern 2: Diverge-Converge

**Sequence:** `creative-thinking` → `sequential-thinking`

**When to use:**
- Stuck on a design problem with no obvious solution.
- Need novel options first, then systematic evaluation and planning.
- The solution space is too wide for direct analytical attack.

**Signals:** "I'm stuck", "we need a new approach", "how else could we" + a problem that has been attempted before.

**How to transfer context:**
- Run creative-thinking with timeframe: quick or thorough.
- Carry the **top 3-5 creative options** as numbered candidates.
- For each candidate, carry: one-sentence description + key insight + feasibility note.
- Discard technique-specific scaffolding (hat colors, SCAMPER verbs, TRIZ principles).
- Sequential-thinking evaluates each candidate systematically, then plans the winner.

**Expected token budget:** High (Tier 4 + Tier 1)

**Example:** "We need a new caching strategy — current one doesn't scale" — diverge with creative techniques to generate novel approaches, then converge with sequential evaluation.

---

## Pattern 3: Explore-Formalize

**Sequence:** `cascade-thinking` → `shannon-thinking`

**When to use:**
- Requirements are unclear or ambiguous.
- Need to survey the landscape before committing to a formal approach.
- Multiple stakeholders or perspectives must be considered before formalizing constraints.

**Signals:** "Design", "architect", "define the requirements for" + unclear constraints or multiple stakeholders.

**How to transfer context:**
- Cascade explores the problem from multiple perspectives/branches.
- Carry: key findings, discovered constraints, points of agreement across branches.
- Carry: unresolved tensions (these become constraints or trade-offs in shannon).
- Discard: exploration branches that yielded no useful constraints or insights.
- Shannon receives a curated constraint set derived from exploration, not guessed upfront.

**Expected token budget:** High (Tier 2 + Tier 3)

**Example:** "Design an API versioning strategy for our public API" — explore from consumer, provider, ops, and backward-compatibility perspectives, then formalize the best approach with proof.

---

## Pattern 4: Decompose-Investigate

**Sequence:** `atom-of-thoughts` → `crash` (per unresolved atom)

**When to use:**
- Complex system has multiple potential failure points.
- Need to decompose the system first, then investigate each suspicious component.
- One-shot debugging would miss interactions between subsystems.

**Signals:** "Intermittent failure", "multiple services involved", "it works sometimes" + complex system.

**How to transfer context:**
- Atom-of-thoughts decomposes the system into atoms with dependency edges.
- Each **unresolved or low-confidence atom** becomes a separate crash investigation.
- Carry: atom context, declared dependencies, and parent atom findings.
- Carry: the dependency DAG so crash can reason about interaction effects.
- Discard: verified atoms (already confirmed working).
- Crash investigations can reference each other's findings via session_id.

**Expected token budget:** High (Tier 3 + Tier 2 x N atoms) — scales with number of unresolved atoms.

**Example:** "The payment pipeline is failing intermittently — it touches auth, billing, and notification services" — decompose the pipeline into atoms, then crash-investigate each suspect component.

---

## Pattern 5: Analyze-Integrate

**Sequence:** `cascade-thinking` → `lotus-wisdom`

**When to use:**
- Multi-perspective exploration surfaced genuine contradictions.
- The contradictions cannot be resolved by picking a winner — both sides have valid evidence.
- The problem involves values, trade-offs, or fundamental tensions (not just missing information).

**Signals:** "Both options have merit", "this is a real trade-off", "we can't have both" + evidence on both sides.

**How to transfer context:**
- Cascade surfaces the specific contradictions with evidence for each side.
- Carry: the **specific contradictions** as pairs — claim A (evidence) vs claim B (evidence).
- Carry: any constraints that apply to both sides.
- Discard: perspectives that agree (already resolved, not contradictory).
- Discard: branch scaffolding and exploration mechanics.
- Lotus-wisdom receives focused contradictions, not a broad exploration dump.

**Expected token budget:** High (Tier 2 + Tier 4)

**Example:** "Our architecture needs to be both highly consistent AND highly available — how do we think about this?" — cascade explores both sides with evidence, lotus-wisdom integrates the tension.

---

## Pattern 6: Strategize-Plan

**Sequence:** `think-strategies` (step_back) → `sequential-thinking`

**When to use:**
- Need big-picture perspective before tactical planning.
- Risk of getting lost in details without a strategic frame.
- Migration, refactoring, or multi-phase project planning.

**Signals:** "Plan the migration", "how should we approach", "what's the right strategy for" + large-scope effort.

**How to transfer context:**
- Think-strategies (step_back) produces a strategic frame: goals, constraints, phases, risks.
- Carry: the strategic frame, key principles, phase boundaries, and identified risks.
- Carry: any strategic decisions made (e.g., "big bang vs incremental" resolved to "incremental").
- Discard: strategy scaffolding (session mechanics, quality ratings, strategy metadata).
- Sequential-thinking receives the strategic frame and produces a concrete step-by-step plan within it.

**Expected token budget:** Medium (Tier 3 + Tier 1)

**Example:** "Plan our migration from monolith to microservices" — step back for strategic framing (what to split, what order, what risks), then plan detailed implementation steps.

---

## When NOT to Compose

Composition is overhead. Use a single method when:

- The problem fits cleanly into one method's sweet spot.
- Complexity is simple or moderate — composition is for complex and wicked problems.
- Time pressure is high — composition doubles (or more) the token budget.
- The first method is converging well — do not switch methods that are working.
