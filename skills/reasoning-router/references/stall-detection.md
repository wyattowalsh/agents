# Stall Detection and Re-Routing Protocol

Detect when reasoning has stalled and re-route to a better method.

---

## 4 Stall Signals

### 1. Confidence Plateau
Confidence score has not increased by >0.05 in 3+ consecutive steps. The method is producing output but not making progress toward higher-confidence conclusions.

### 2. Circular Reasoning
Same claim or conclusion restated with different wording in consecutive outputs. Detected by semantic similarity — if step N and step N+2 make essentially the same assertion, reasoning is looping.

### 3. Step Overrun
Steps exceed 2x the initial `totalThoughts` estimate without convergence toward a conclusion. The method is exploring indefinitely without narrowing.

### 4. User Signal
User says "this isn't working", "try something else", "switch", or uses `/think switch <method>`. Explicit human override — always honor immediately.

---

## Re-Routing Decision Matrix

| Block Type | Signal | New Method | Why |
|-----------|--------|------------|-----|
| Stuck in depth | Confidence plateau on decomposition | cascade-thinking | Broaden perspective — depth is not yielding progress, width might |
| Too broad | Step overrun with no convergence | atom-of-thoughts | Force decomposition — wandering exploration needs structural anchoring |
| Too formal | Confidence plateau on constrained problem | creative-thinking (quick) | Reframe the problem — formal structure may be hiding the real question |
| Too abstract | Circular reasoning on theoretical concepts | crash | Ground in concrete tools and evidence — theory needs contact with reality |
| Contradictions unresolved | Multiple claims at ~0.5 confidence, none advancing | lotus-wisdom | Integrate rather than resolve — the contradiction may be genuine |
| Wrong method entirely | User signal or very low confidence after 5+ steps | Reclassify from scratch | Original classification was wrong — re-run the routing analysis |

---

## Context Transfer on Re-Route

1. **Summarize** current findings in <=100 words.
2. **List** key claims with confidence scores.
3. **Identify** what specifically is blocking progress (the stall signal and block type).
4. **Feed** summary + block diagnosis to the new method as initial context.
5. **Do NOT restart from scratch** — build on what was learned. The stalled method produced partial progress; preserve it.

---

## Hard Limits

- **Maximum 3 re-routes per session.** After 3 re-routes, stop and present findings to the user.
- **Maximum 3x initial step estimate before forced re-route.** If totalThoughts was 8, force re-route at step 24.
- **No ping-pong.** If a method is re-routed FROM, it cannot be re-routed TO in the same session. Prevents A → B → A oscillation.

---

## Recovery Protocol (After 3 Re-Routes)

When the re-route limit is reached, present the following to the user:

> I have tried [list methods attempted]. Key findings so far: [<=100 word summary]. I am stuck on: [specific block description].
>
> How would you like to proceed?
>
> 1. **Continue** with [best-performing method so far, identified by highest peak confidence]
> 2. **Try a composition pattern**: [suggest the most relevant pattern from composition-patterns.md based on the problem structure]
> 3. **Provide additional context** to refine the problem — [specific question about what information would unblock progress]

Wait for user input before proceeding. Do not auto-select an option.
