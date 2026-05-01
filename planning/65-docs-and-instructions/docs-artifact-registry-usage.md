# Docs Artifact Registry Usage

## Purpose

`config/docs-artifact-registry.json` is the canonical inventory for generated and curated documentation surfaces. C08 uses it to decide which docs are generated, which docs are hand-curated, and which validation command owns freshness.

## Rules

- Generated docs must identify their upstream registry, manifest, or generator.
- Curated docs must identify their source-of-truth fragments and the command that checks freshness.
- Child lanes must publish fragments or manifests instead of editing global docs directly.
- Support claims must reference a support-tier registry entry and a harness or artifact owner.
- Docs must not invent installed-skill or harness support claims when the registry lacks evidence.

## Required Fields For New Docs Artifacts

| field | requirement |
|---|---|
| artifact id | Stable kebab-case identifier. |
| output path | Repo-relative docs or instruction path. |
| source inputs | Registry, manifest, fragment, or generator inputs. |
| owner lane | Child OpenSpec lane responsible for updates. |
| generated/curated class | Whether the output is generated, curated, or local-only. |
| validation command | Command that detects stale output or invalid source data. |

## C08 Ownership

C08 owns the docs artifact registry contract and final consolidation pass. Other child lanes own their lane fragments until C08 explicitly schedules a generated-doc refresh.
