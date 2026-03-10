# Routing Matrix

Expanded routing table, tie-breaking rules, example routings, and anti-patterns.

---

## 3-Axis Routing Table

Structure type (rows) crossed with complexity level (columns). Each cell: **primary** / fallback.

| Structure | Simple | Moderate | Complex | Wicked |
|-----------|--------|----------|---------|--------|
| **Sequential** (step-by-step, ordered) | aot-light / — | sequential-thinking / structured-thinking | sequential-thinking / think-strategies (chain_of_thought) | think-strategies (step_back) / cascade-thinking |
| **Decomposable** (break into parts) | aot-light / — | atom-of-thoughts / aot-light | atom-of-thoughts / think-strategies (tree_of_thoughts) | atom-of-thoughts → crash (per atom) / cascade-thinking |
| **Branching** (multiple perspectives) | aot-light / sequential-thinking | cascade-thinking / think-strategies (self_consistency) | cascade-thinking / think-strategies (tree_of_thoughts) | cascade-thinking → lotus-wisdom / deep-lucid-3d |
| **Investigative** (debugging, root-cause) | sequential-thinking / aot-light | crash / cascade-thinking | crash / atom-of-thoughts → crash | crash → cascade-thinking / think-strategies (react) |
| **Constrained** (formal requirements) | sequential-thinking / aot-light | shannon-thinking / structured-thinking | shannon-thinking / think-strategies (trilemma) | shannon-thinking → lotus-wisdom / deep-lucid-3d |
| **Creative** (ideation, reframing) | aot-light / sequential-thinking | creative-thinking (quick) / cascade-thinking | creative-thinking (thorough) / deep-lucid-3d | creative-thinking (comprehensive) / lotus-wisdom |
| **Contradictory** (paradox, tension) | sequential-thinking / aot-light | lotus-wisdom / cascade-thinking | lotus-wisdom / deep-lucid-3d | lotus-wisdom → cascade-thinking / deep-lucid-3d |
| **Interconnected** (dependency chains) | aot-light / sequential-thinking | structured-thinking / atom-of-thoughts | atom-of-thoughts / think-strategies (rewoo) | atom-of-thoughts → cascade-thinking / deep-lucid-3d |

**Efficiency override:** Any problem classified as Simple uses Tier 1 methods regardless of structure type. Do not deploy Tier 3-4 methods for simple problems.

**Arrow notation:** `→` means a composition chain (see composition-patterns.md). The first method feeds into the second.

**Reading the table:** Primary is the first-choice method for that cell. Fallback activates when the primary stalls (see stall-detection.md) or when the problem does not fit the primary as cleanly as initially classified.

---

## Tie-Breaking Rules

1. **Structure > domain** — HOW to think always outranks WHAT you are thinking about. A branching math problem routes to cascade-thinking, not shannon-thinking.
2. **Equal structure scores → prefer lower token tier** — Between two methods that fit equally well, choose the one with lower token cost.
3. **Equal everything → default to sequential-thinking** — Safest general-purpose fallback. Lowest overhead, widest applicability.
4. **User preference overrides** — If the user requests a specific method or style ("explore this from multiple angles"), honor that signal even if the classifier suggests otherwise.

---

## 15 Example Routings

| # | Prompt | Classification | Route | Rationale |
|---|--------|---------------|-------|-----------|
| 1 | "Break this problem into sub-parts and solve each" | decomposable + moderate | atom-of-thoughts | Explicit decomposition request maps directly to atomic reasoning. |
| 2 | "Walk me through debugging this error" | investigative + moderate | crash | Debugging workflow with tool-aware next-action planning. |
| 3 | "Brainstorm 10 creative names for this project" | creative + simple | aot-light | Efficiency override — simple creative task does not justify Tier 4 overhead. |
| 4 | "Given these constraints, design a database schema that satisfies all requirements" | constrained + complex | shannon-thinking | Formal constraints need proof + validation workflow. |
| 5 | "Explore this topic from multiple angles" | branching + moderate | cascade-thinking | Multi-perspective exploration is cascade's core strength. |
| 6 | "This seems contradictory — how can both be true?" | contradictory + moderate | lotus-wisdom | Genuine contradiction needs integration, not resolution. |
| 7 | "What's 2+2?" | sequential + simple | aot-light | Efficiency override — trivial question gets lightest method. |
| 8 | "Design a microservice architecture handling 100K req/s with <50ms latency, GDPR compliance, and multi-region failover" | constrained + complex | shannon-thinking | Multiple formal constraints require rigorous proof-based reasoning. |
| 9 | "Why did the test suite start failing after the migration?" | investigative + complex | crash | Complex debugging with branching investigation and tool integration. |
| 10 | "I'm stuck on this problem and need a fresh perspective" | creative + moderate | creative-thinking (quick) | Explicit reframing request. Run full discover→plan→execute with timeframe: quick. |
| 11 | "Compare these 3 architectural approaches" | branching + moderate | cascade-thinking | Each approach becomes a branch for parallel evaluation. |
| 12 | "Analyze the recursive dependency chain in this module" | interconnected + complex | atom-of-thoughts (full) | Dependency DAG with Markov property isolates each link in the chain. |
| 13 | "Plan the implementation steps for this feature" | sequential + moderate | sequential-thinking | Ordered step-by-step planning is sequential-thinking's core use case. |
| 14 | "Track this pattern I keep seeing across sessions" | patterns + moderate | structured-thinking | Cross-session memory with tag-based retrieval preserves pattern observations. |
| 15 | "This ethical dilemma has no clear answer" | contradictory + wicked | lotus-wisdom → cascade-thinking chain | Lotus-wisdom integrates the contradiction, then cascade explores implications from multiple stakeholder perspectives. |

---

## Anti-Patterns (Common Misroutes)

| Misroute | Why it fails | Correct route |
|----------|-------------|---------------|
| atom-of-thoughts for a simple question | Massive overhead for a problem with no decomposition structure. Atoms become trivial single-node graphs. | aot-light or sequential-thinking |
| sequential-thinking for multi-perspective exploration | Single linear path cannot genuinely explore parallel viewpoints. Perspectives get flattened into a sequence. | cascade-thinking |
| creative-thinking for a well-defined engineering problem | 3-step creative workflow adds overhead without value when the solution space is already constrained. | shannon-thinking or crash |
| shannon-thinking for brainstorming | Five-phase formal structure kills divergent thinking. Proof requirements prematurely close the solution space. | creative-thinking or cascade-thinking |
| lotus-wisdom for a debugging problem | Non-dual contemplation does not produce actionable debugging steps. Wrong frame entirely. | crash |
| cascade-thinking for a simple ordered task | Branch management overhead for a problem that has exactly one natural path. | sequential-thinking |
| think-strategies without a strategy rationale | Picking a strategy at random defeats the purpose. If you cannot articulate WHY a specific strategy fits, use a simpler method. | sequential-thinking (then upgrade if stuck) |

**Rule of thumb:** If the misroute involves using a higher-tier tool where a lower-tier tool suffices, the cost is wasted tokens. If it involves using the wrong shape (e.g., linear for branching), the cost is wrong conclusions. Shape mismatches are worse than tier mismatches.
