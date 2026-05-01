# Proposal: Agents Platform Overhaul

## Summary

Refactor the agents repository into a skills-first, OpenSpec-governed, multi-harness agent platform with canonical registries, transaction-safe config sync, curated MCP live-systems layer, streamlined UX, and generated documentation truth.

## Problem

The repository already spans many harnesses and capability types. Without a canonical registry and governance model, support claims, generated configs, MCP choices, skill packaging, docs, and AI instructions can drift.

## Goals

- Prefer Agent Skills for portable reusable capabilities.
- Use MCP only for live external state and dynamic runtime capabilities.
- Add canonical registries for harnesses, skills, MCPs, plugins, docs, and external capabilities.
- Add transaction-safe config preview/apply/rollback.
- Add conformance gates and generated documentation truth.
- Add granular parallel task graph for implementation.
- Preserve and integrate existing OpenSpec assets.

## Non-goals

- No big-bang rewrite.
- No blind adoption of MCP servers from directories.
- No claims of validated support without fixtures and tests.
- No direct overwrite of existing OpenSpec content before reconciliation.
