---
skill: langsmith-dataset
source_type: curated-external
researched_at: '2026-06-16T08:41:53Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Official from langchain-ai/langsmith-skills (early dev, 131 stars). Generate evaluation datasets from traces (with helper scripts). Requires LANGSMITH_API_KEY + cloud access per README. Part of observability for LLM apps. Complements langchain-skills.

## Harness Coverage

antigravity,claude-code,... group targets.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; requires secret API key (user provisioned); early dev; scripts included may exec. Official LangChain but scoped to LangSmith tracing/eval.

## Install Prerequisites

npx skills add langchain-ai/langsmith-skills --skill ... -y -g -a [..]; set LANGSMITH_API_KEY; status=inspect-then-install.

## Upstream Maintainer

[langchain-ai/langsmith-skills](https://github.com/langchain-ai/langsmith-skills)

## Comparable Alternatives

Other trace/eval skills (e.g. langfuse, phoenix).

> Evidence from public web sources, GitHub (official orgs 2026), curated catalog; research evidence, not authority. External audit advised.
