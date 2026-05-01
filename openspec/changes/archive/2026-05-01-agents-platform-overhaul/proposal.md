# Proposal: Agents Platform Overhaul

## Summary

Refactor the agents repository into a skills-first, OpenSpec-governed, multi-harness agent asset and control-plane repository with canonical registries, transaction-safe config sync, curated MCP live-system support, streamlined CLI/UX automation, and generated documentation truth.

## Problem

The repository already spans portable Agent Skills, MCP configuration, platform bridge files, plugin manifests, generated docs, and downstream harness setup. Without an explicit registry and governance layer, support claims, MCP usage, skill packaging, generated instructions, and docs can drift independently.

## Goals

- Prefer Agent Skills for portable deterministic capabilities.
- Use MCP only for live external state, browser/runtime state, authenticated SaaS, current docs/search, database/cloud/vector state, telemetry streams, or other interactive systems.
- Treat native plugins as projections from canonical skills, MCP profiles, and config manifests.
- Freeze canonical support tiers: `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, and `quarantine`.
- Add canonical registries for harnesses, skills, MCP servers, plugins/extensions, docs artifacts, and external repo evaluations.
- Add a repo-sync inventory and drift ledger before implementation waves begin.
- Establish child OpenSpec changes and dispatch prompts for parallel implementation lanes.
- Preserve existing unrelated worktree changes and avoid generated-doc merge conflicts.

## Non-Goals

- Do not implement the full overhaul in one run.
- Do not install external repositories, skills, MCP servers, or plugins by default.
- Do not promote external repositories without pinned source, license review, security/provenance review, and conformance fixtures.
- Do not let child teams edit shared generated docs or instruction truth directly.
- Do not rewrite existing active OpenSpec changes outside this overhaul.

## Source Inputs

- `agents-overhaul-planning/openspec/changes/agents-platform-overhaul/`
- `agents-overhaul-planning/planning/`
- `agents-overhaul-planning/planning/manifests/external-repo-evaluation-final.json`
- `agents-overhaul-planning/planning/manifests/subagent-graph-final.json`
- Current root repository files and OpenSpec assets.
