# Generated Doc Ownership Plan

## Ownership Model

Generated docs are derived outputs. Their owner is the generator plus the registry or manifest that feeds it, not the last child lane that changed an input.

| doc class | owner | update trigger |
|---|---|---|
| README tables and support summaries | `wagents readme` plus registries/manifests | Registry or public asset metadata changes. |
| Docs site generated skill pages | `wagents docs generate` plus `skills/` metadata | Skill metadata or docs generator changes. |
| Docs site generated indexes/data | `wagents docs generate` plus registry/site model inputs | Registry, skill, or site model changes. |
| AI instruction bridge files | instruction sync tooling plus canonical instruction sources | Global/platform instruction changes. |
| Support matrices | support-tier and harness registries | Harness registry or support-tier changes. |

## Conflict Control

- Generated docs must not be refreshed opportunistically while they are dirty from unrelated work.
- Child lanes should stage source manifests and fragments, not generated output, unless generated-doc refresh is explicitly part of that lane.
- Final C08 consolidation should happen after active child fragments stabilize and the worktree conflict surface is coordinated.

## Freshness Contract

Each generated artifact must have a check command. If a check cannot run because a shared generated file is dirty, the blocker must be recorded rather than hidden by manual edits.
