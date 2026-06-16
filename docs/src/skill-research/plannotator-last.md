---
skill: plannotator-last
source_type: curated-external
researched_at: '2026-06-16T08:45:57Z'
research_tier: standard
mean_confidence: 0.74
---

## Purpose

Plannotator-last opens Plannotator on the latest rendered assistant message so the user can annotate it visually. The skill invokes `plannotator last`, suppresses an initial status preamble (to avoid annotating the preamble itself), waits for feedback, and incorporates annotations into the next response. Useful for targeted revision of the most recent agent output without re-specifying context.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. `disable-model-invocation: true`; purely a launcher for the external CLI + UI session.

## Trust And Risks

Same provenance as sibling plannotator skills: install-now-after-trust-gate, curated-trust-gated. Relies on the plannotator binary and local browser UI. Risks center on external process execution and the ability of the UI to receive and return annotations derived from recent chat context. The implementation intentionally avoids sending commentary before launch. Open-source project with local-first operation; review the binary provenance and any sidecar hooks.

## Install Prerequisites

Plannotator CLI must be present (`curl -fsSL https://plannotator.ai/install.sh | bash`). Install the core skill bundle with the same npx skills add command used for plannotator-annotate / plannotator-review, targeting the listed agents.

## Upstream Maintainer

backnotprop (https://github.com/backnotprop/plannotator); https://plannotator.ai/

## Comparable Alternatives

Direct chat follow-ups with pasted excerpts; other annotation or diff-review skills; visual tools such as Excalidraw diagram skills for higher-level overviews.

> Evidence gathered from public GitHub sources, raw SKILL.md, and project site (plannotator.ai). Not an endorsement or authority; inspect the CLI binary, hooks, and network behavior before use.
