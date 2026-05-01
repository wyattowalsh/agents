# Terms Glossary

## Agent Skill

A portable deterministic capability packaged as `skills/<name>/SKILL.md` with optional `references/`, `assets/`, `scripts/`, and eval fixtures. Skills are the default extension model.

## MCP Live-System Layer

Model Context Protocol servers used only when a capability needs live external state, browser/runtime state, authenticated SaaS, current search/docs, database/cloud/vector state, telemetry streams, or interactive systems.

## Native Plugin

A harness-specific projection that exposes canonical repo skills, MCP profiles, config, or UX into a native plugin/extension surface. Plugins are not canonical source of truth.

## Registry

A canonical machine-readable manifest that drives validation, docs generation, support matrices, and harness projection.

## Support Tier

One of `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, or `quarantine`.

## Quarantine

A support tier for assets blocked from default installation or promotion because they involve auth bridging, proxying, credential sharing, offensive security, or unresolved supply-chain risk.

## Dispatch Prompt

A child-agent execution contract that names the child OpenSpec change, allowed paths, forbidden shared files, dependencies, validation commands, expected artifacts, commit requirement, and final response format.
