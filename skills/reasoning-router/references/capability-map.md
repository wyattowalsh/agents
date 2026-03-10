# Thinking MCP Tool Capability Map

Complete reference for all 11 reasoning MCP tools available for routing.

---

## Tier 1 — Lightweight (~500-1500 tokens)

### 1. sequential-thinking

- **MCP tool:** `mcp__sequential-thinking__sequentialthinking`
- **Token cost:** Tier 1 (lightest)
- **Best for:** Linear step-by-step reasoning with optional revision and branching.
- **Required workflow:** None — single tool call per thought.
- **Key parameters:** `thought`, `thoughtNumber`, `totalThoughts`, `nextThoughtNeeded`, `isRevision`, `revisesThought`, `branchFromThought`, `branchId`, `needsMoreThoughts`
- **Unique strength:** Simplest mental model — natural progressive reasoning with built-in revision. Zero framework overhead.
- **Blind spot:** Single linear path. No parallel exploration, no dependency tracking, no memory. Branching exists but is manual and shallow.

### 2. aot-light

- **MCP tool:** `mcp__atom-of-thoughts__aot-light`
- **Token cost:** Tier 1 (lightest)
- **Best for:** Quick atomic decomposition with depth capped at 3 levels.
- **Required workflow:** None — same interface as full `aot` but automatically depth-limited.
- **Key parameters:** Same as `aot` — `atomId`, `content`, `atomType`, `dependencies`, `confidence`, `isVerified`, `depth` — but max depth is 3.
- **Unique strength:** 70% token reduction vs full atom-of-thoughts. Fast structural sketching without deep recursion.
- **Blind spot:** Shallow analysis ceiling. Cannot follow dependency chains beyond 3 hops. Insufficient for genuinely complex decomposition.

---

## Tier 2 — Moderate (~1500-4000 tokens)

### 3. structured-thinking

- **MCP tools:** `mcp__structured-thinking__capture_thought`, `clear_thinking_history`, `get_thinking_summary`, `retrieve_relevant_thoughts`, `revise_thought`
- **Token cost:** Tier 2
- **Best for:** Reasoning that benefits from persistent memory, tagging, and cross-session retrieval.
- **Required workflow:** None strict, but best results come from using `capture_thought` → `retrieve_relevant_thoughts` → `revise_thought` cycle.
- **Key parameters:** `thought`, `thought_number`, `total_thoughts`, `next_thought_needed`, `stage`, `tags`, `score`, `is_revision`, `revises_thought`, `needs_more_thoughts`
- **Unique strength:** Cross-session memory with auto-retrieval by tags. Metacognitive feedback via scoring. Persistent thought history survives context resets.
- **Blind spot:** Memory management overhead. Tags must be chosen well or retrieval degrades. Not suited to problems that need parallel exploration.

### 4. cascade-thinking

- **MCP tool:** `mcp__cascade-thinking__cascade_thinking`
- **Token cost:** Tier 2
- **Best for:** Multi-perspective parallel exploration with branching and cross-connection discovery.
- **Required workflow:** None — single tool with branching built in.
- **Key parameters:** `thought`, `thoughtNumber`, `totalThoughts`, `nextThoughtNeeded`, `branchFromThought`, `branchId`, `branchDescription`, `revisesThought`, `isRevision`, `startNewSequence`, `sequenceDescription`, `retrieveThoughts`, `recentThoughtsLimit`, `responseMode`, `isolatedContext`, `toolSource`
- **Unique strength:** Dual indexing (A{n} absolute + S{n} sequence-relative) enables true parallel branches with cross-connection discovery between them.
- **Blind spot:** Requires active coordination to manage branches. Without discipline, branches proliferate without convergence. No built-in convergence mechanism.

### 5. crash

- **MCP tool:** `mcp__crash__crash`
- **Token cost:** Tier 2
- **Best for:** Multi-branch debugging and investigation with tool integration and structured next-action planning.
- **Required workflow:** None — single tool, but designed for iterative investigation loops.
- **Key parameters:** `step_number`, `estimated_total`, `purpose` (analysis/action/reflection/decision/summary/validation/exploration/hypothesis/correction/planning), `context`, `thought`, `outcome`, `next_action` (string or `{action, tool, parameters, expectedOutput}`), `rationale`, `session_id`, `branch_from`, `branch_id`, `branch_name`, `revises_step`, `revision_reason`, `uncertainty_notes`, `dependencies`, `tools_used`, `external_context`, `confidence`, `is_final_step`
- **Unique strength:** Built for debugging — `next_action` can specify actual tool calls with expected outputs. Purpose taxonomy covers the full investigation lifecycle.
- **Blind spot:** Verbose parameter set creates overhead for simple reasoning. Overkill for non-investigative problems.

---

## Tier 3 — Heavy (~4000-8000 tokens)

### 6. shannon-thinking

- **MCP tool:** `mcp__shannon-thinking__shannonthinking`
- **Token cost:** Tier 3
- **Best for:** Formal problem-solving requiring rigorous proof and experimental validation under constraints.
- **Required workflow:** Five-phase progression: problem_definition → constraints → model → proof → implementation.
- **Key parameters:** `thought`, `thoughtType`, `thoughtNumber`, `totalThoughts`, `uncertainty`, `dependencies`, `assumptions`, `isRevision`, `revisesThought`, `recheckStep`, `proofElements`, `experimentalElements`, `implementationNotes`, `nextThoughtNeeded`
- **Unique strength:** Demands both formal proof AND experimental validation. Explicit uncertainty tracking. Forces rigorous constraint articulation.
- **Blind spot:** Heavy — requires formal problem structure to be effective. Poorly suited to exploratory or creative problems. The five-phase sequence is rigid.

### 7. atom-of-thoughts (full)

- **MCP tools:** `mcp__atom-of-thoughts__aot`, `mcp__atom-of-thoughts__atomcommands`
- **Token cost:** Tier 3
- **Best for:** Deep decomposition with explicit dependency DAG, up to 5 levels.
- **Required workflow:** Use `aot` for individual atoms and `atomcommands` for meta-operations (decompose, complete_decomposition, termination_status, best_conclusion, set_max_depth).
- **Key parameters:** `atomId`, `content`, `atomType` (premise/reasoning/hypothesis/verification/conclusion), `dependencies`, `confidence`, `isVerified`, `depth`. Commands: `command`, plus command-specific params.
- **Unique strength:** Explicit dependency graph with Markov property — each atom depends only on declared parents, eliminating context pollution across branches.
- **Blind spot:** Atom management overhead. Requires disciplined ID tracking. Poor fit for problems without clear decomposition boundaries.

### 8. think-strategies

- **MCP tools:** `mcp__think-strategies__think-strategies`, `think-tools`, `think-session-manager`
- **Token cost:** Tier 3
- **Best for:** Selecting and applying named reasoning strategies with explicit framework scaffolding.
- **Required workflow:** Choose a strategy, then follow its protocol. 10 strategies: linear, chain_of_thought, react, rewoo, scratchpad, self_ask, self_consistency, step_back, tree_of_thoughts, trilemma.
- **Key parameters:** `strategy`, `thought`, `thoughtNumber`, `totalThoughts`, `nextThoughtNeeded`, `action`, `observation`, `plannedActions`, `actionResults`, `finalAnswer`, `sessionPurpose`, `sessionId`, `qualityRating`
- **Unique strength:** Strategy comparison — can run the same problem through multiple strategies. ReAct and ReWOO workflows for tool-integrated reasoning.
- **Blind spot:** Requires knowing which strategy to pick upfront (meta-reasoning problem). Strategy scaffolding adds overhead even when the strategy is straightforward.

---

## Tier 4 — Heavyweight (~8000+ tokens)

### 9. creative-thinking

- **MCP tools:** `mcp__creative-thinking__discover_techniques`, `plan_thinking_session`, `execute_thinking_step`
- **Token cost:** Tier 4 (heaviest workflow)
- **Best for:** Lateral thinking, reframing, and novel ideation using structured creativity techniques.
- **Required workflow:** **MANDATORY 3-step sequence** — `discover_techniques` → `plan_thinking_session` (returns `planId`) → `execute_thinking_step` (must execute EVERY step, no skipping).
- **Key parameters:** Vary per step. Key: `executionMode` (sequential/parallel/auto), `timeframe` (quick/thorough/comprehensive), `maxParallelism` (1-10). 21 techniques including six_hats, scamper, triz, first_principles, quantum_superposition, biomimetic_path, neuro_computational.
- **Unique strength:** 21 lateral thinking techniques with structured execution. Parallel technique execution. Forced perspective shifts.
- **Blind spot:** Highest overhead — 3-step workflow is mandatory and cannot be shortcut. Overkill for well-defined engineering problems. Every planned step must be executed.

### 10. deep-lucid-3d

- **MCP tools:** `mcp__deep-lucid-3d__analyze_problem`, `creative_exploration`, `manage_state`
- **Token cost:** Tier 4
- **Best for:** Holistic analysis combining critical, parametric, and creative dimensions (UCPF framework).
- **Required workflow:** None strict — `analyze_problem` is self-contained. Use `creative_exploration` for divergent phase, `manage_state` for session persistence.
- **Key parameters:** `problem`, `detailed`, `enable_state`, `session_id`. Creative exploration: `topic`, `perspective_count`, `constraints`, `include_metaphors`.
- **Unique strength:** Three-dimensional analysis (critical + parametric + creative) provides holistic coverage. Built-in metaphor generation.
- **Blind spot:** Complex framework produces less structured output. Hard to extract actionable next steps. Better for understanding than for deciding.

### 11. lotus-wisdom

- **MCP tools:** `mcp__lotus-wisdom-mcp__lotuswisdom`, `lotuswisdom_summary`
- **Token cost:** Tier 4 (slowest)
- **Best for:** Paradoxes, contradictions, ethical dilemmas, and problems where conventional logic cannot resolve tensions.
- **Required workflow:** **MUST start with `tag: begin`**. Tags organized by category — Processing: open/engage/express; Meta-cognitive: examine/reflect/verify/refine/complete; Non-dual: recognize/transform/integrate/transcend/embody; Skillful-means: upaya/expedient/direct/gradual/sudden; Special: meditate.
- **Key parameters:** `tag`, `content`, `stepNumber`, `totalSteps`, `nextStepNeeded`, `isMeditation`, `meditationDuration` (1-10)
- **Unique strength:** Handles genuine paradox by integrating contradictions rather than resolving them. Non-dual perspective reveals false dichotomies.
- **Blind spot:** Not suited for analytical or debugging problems. Slowest method. Output requires interpretation — does not produce conventional conclusions.
