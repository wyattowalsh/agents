# Proposal

## Problem

`harness-master` can audit known local harness surfaces, but it does not yet have a structured read-only mode for discovering and comparing ecosystem improvements before an apply step. That makes config, plugin, extension, MCP, and Agent Skill recommendations depend too much on ad hoc source coverage and too little on reproducible programmatic evidence.

## Intent

Add a modular ecosystem research mode that can plan source access, gather evidence from official docs, local registries, GitHub, package registries, MCP registries, skill hubs, and security feeds, then score candidates before any install or config mutation is considered.

## Scope

- Extend `skills/harness-master/SKILL.md` with research, candidate, compare, and sources dispatch modes.
- Add source registry data, source-profile guidance, ecosystem workflow guidance, and output templates.
- Add read-only helper scripts for source probing and candidate scoring.
- Add eval fixtures for research routing, GitHub GraphQL enrichment, MCP registry cross-source comparison, third-party skill routing, degraded credentialed sources, community-only negative evidence, and blocked apply flows.

## Out Of Scope

- Installing external tools, packages, plugins, skills, or MCP servers.
- Editing repo-managed harness configs based on research findings.
- Generating public docs unless validation reports drift.
- Adding credential requirements for baseline research mode.

## Affected Users And Tools

- Maintainers using `harness-master` to evaluate harness config, plugin, extension, MCP, and skill improvements.
- Agents using `harness-master` as a progressive-disclosure decision workflow before applying changes.
- Evals and package validation that verify the skill remains portable and dry-run first.

## Risks

- Credentialed sources may be unavailable and must degrade confidence instead of failing.
- Community and social sources can overstate candidate quality unless the workflow prevents adoption from sentiment alone.
- GitHub GraphQL enrichment is useful for known candidates but cannot replace REST/code search for broad discovery.
- Source APIs may drift; the registry and source profiles must keep failure modes explicit.
