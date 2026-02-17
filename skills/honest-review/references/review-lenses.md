# Creative Review Lenses

Five techniques for finding issues that standard checklist review misses.
Apply at least 2 lenses per review scope. Pick based on code characteristics.

## Contents

- [Inversion Lens](#inversion-lens)
- [Deletion Lens](#deletion-lens)
- [Newcomer Lens](#newcomer-lens)
- [Incident Lens](#incident-lens)
- [Evolution Lens](#evolution-lens)

## Inversion Lens

"What if this assumption were false?"

**When to apply:** Code with implicit assumptions — config always present, network always available, user always authenticated, data always valid.

**Method:**
1. List every assumption the code makes (inputs, environment, ordering, availability).
2. For each assumption, invert it: the config is missing, the network is down, the user is unauthenticated, the data is malformed.
3. Ask: does the code handle the inverted case, or does it silently break?
4. Check for missing guards, missing defaults, and missing error paths.

**Expected output:** List of unhandled assumption violations with severity ratings.

**Cross-reference:** Security items in checklists.md (broken access control), resilience items (fallbacks, graceful degradation).

## Deletion Lens

"What if we deleted this code?"

**When to apply:** Mature codebases, code touched by many authors, code with unclear purpose.

**Method:**
1. For each function, class, or module in scope, ask: what breaks if this is deleted?
2. If nothing breaks (no tests fail, no callers exist), flag it as potentially dead code.
3. Check git blame for the last meaningful change. Stale code with no recent activity strengthens the dead-code signal.
4. Distinguish between truly dead code, likely dead code, and unclear-purpose code.

**Expected output:** Candidates for deletion with confidence level (dead, likely dead, unclear).

**Cross-reference:** Correctness simplification items in checklists.md (dead code, unused imports).

## Newcomer Lens

"Could a new team member understand this in 15 minutes?"

**When to apply:** All code — always useful. Prioritize complex modules, unclear naming, and sparse documentation.

**Method:**
1. Read the code as if encountering it for the first time. Forget all existing context.
2. Track every moment of confusion: unclear names, implicit context, non-obvious control flow, magic values, undocumented side effects.
3. Time yourself. If understanding takes more than 15 minutes for a single module, flag excessive cognitive load.
4. Note where you had to read other files to understand the current one — that is implicit coupling.

**Expected output:** Cognitive load hotspots with specific confusion points and suggested clarifications.

**Cross-reference:** Correctness items in checklists.md (readability), design items (cognitive complexity, naming).

## Incident Lens

"What would cause a 3am page?"

**When to apply:** Production services, data pipelines, anything with SLAs or uptime requirements.

**Method:**
1. Trace failure modes: what happens when external dependencies fail? When disk fills? When memory spikes? When a downstream service returns garbage?
2. Simulate a bad deploy: what happens if this code ships with a bug? Is rollback safe?
3. Identify missing circuit breakers, missing fallbacks, missing alerts, and missing graceful degradation paths.
4. Estimate likelihood and blast radius for each scenario.

**Expected output:** Incident scenarios ranked by likelihood and blast radius, with gaps in observability and resilience.

**Cross-reference:** Resilience and observability items in checklists.md.

## Evolution Lens

"How painful would common changes be?"

**When to apply:** Code expected to evolve — new features planned, growing team, scaling anticipated.

**Method:**
1. Imagine 3 likely future changes: add a new field, support a new provider, change a business rule.
2. For each change, count the files that must be touched. If a single-concept change requires editing 5+ files, flag change amplification.
3. Identify coupling hotspots: modules where unrelated changes collide.
4. Check for extension points. Determine whether the code supports addition without modification (open-closed alignment).

**Expected output:** Change amplification scores per scenario and a list of coupling hotspots with remediation suggestions.

**Cross-reference:** Design items in checklists.md (coupling, cohesion), backward compatibility items.
