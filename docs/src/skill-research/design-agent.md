---
skill: design-agent
source_type: curated-external
researched_at: '2026-06-16T08:46:52Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

design-agent (CrewAI) covers agent design using the Role-Goal-Backstory framework, LLM selection (including cheap function-calling models), tool assignment, execution tuning (max_iter, max_rpm, max_execution_time), memory/knowledge sources, guardrails, YAML vs code config, planning modes, and delegation. Strongly recommends spending 80% effort on task design first and defaulting to a single agent unless clear persona/tool/LLM splits exist.

## Harness Coverage

Target agents from the crewaiinc bundle. Used when creating or debugging CrewAI agents.

## Trust And Risks

inspect-then-install / needs-inspection. Official CrewAI Inc. skill (MIT). The skill itself is advisory. Risks come from the generated CrewAI code (cost from extra agents/iterations, guardrail bypasses, delegation loops, code-execution mode). The skill explicitly warns about over-splitting into agents and cost of planning modes.

## Install Prerequisites

`npx skills add crewaiinc/skills --skill design-agent --skill design-task --skill getting-started -y -g -a ...`

Requires CrewAI installed in the target project; Docker for safe code execution if used.

## Upstream Maintainer

CrewAI Inc. (https://github.com/crewAIInc/skills). Docs: https://docs.crewai.com

## Comparable Alternatives

Other multi-agent frameworks (LangGraph, AutoGen, Semantic Kernel) and their design guides; direct LLM orchestration without framework ceremony for simple cases.

> Evidence from public GitHub (raw skill) and repo README. Summarizes risks; do not endorse installation without inspection. Not authority.
