---
name: grill-me
description: >-
  Deep user interview for pivotal plan/design uncertainties. Auto-suggest when
  user judgment would materially change scope, approach, or success criteria.
  Scoped mid-task grilling for subtask-pivotal forks. NOT for micro-reversible
  questions or codebase-discoverable facts.
---

Repo overlay for Grok Build. Canonical routing policy lives in `instructions/global.md` Depth routing.

Interview relentlessly about every aspect of the scoped branch (or full plan when upfront) until we reach a shared understanding. Walk down each branch of the design tree within scope, resolving dependencies between decisions one-by-one. Do not re-grill settled plan areas listed in resolved context.

For each question, provide your recommended answer. Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

**Mid-task triggers:** subagent returns `blocked-user-pivotal`; orchestrator re-enters Uncertainty Gate; mid-wave fork classified as `subtask-pivotal`.