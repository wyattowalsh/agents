---
skill: netlify-deploy
source_type: curated-external
researched_at: '2026-06-16T08:37:32Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Deploy web projects to Netlify using the Netlify CLI (`npx netlify`). Use when the user asks to deploy, host, publish, or link a site/repo on Netlify, including preview and production deploys. Automates CLI auth check (npx netlify status/login), Git-based site linking or init, dep install, framework detection, and npx netlify deploy / --prod. Includes handling for netlify.toml, build/publish dirs, env vars, and error patterns. Factual reference from official Netlify.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.; evidence=Curated npx command in config/external-skills.md. Web-aug: Official netlify org (github.com/netlify/context-and-tools, MIT, ~18 stars, very active 2026 commits/workflows, plugin support for multiple harnesses incl. dedicated MCP server). Skills are read-only references + generated adapters; deploy flow requires user Netlify auth (OAuth or NETLIFY_AUTH_TOKEN) and network. Low risk for info skills; deploy steps surface creds to CLI only. Run `/review source` for script/hooks audit.

## Install Prerequisites

Install: `npx skills add netlify/context-and-tools --skill netlify-deploy --skill netlify-functions --skill netlify-edge-functions -y -g -a antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode` status=inspect-then-install; selector=named. Requires Netlify account/CLI auth for full use.

## Upstream Maintainer

[netlify/context-and-tools](https://github.com/netlify/context-and-tools) (official Netlify org, MIT license, active maintenance, cross-harness plugins + MCP).

## Comparable Alternatives

Official Netlify docs/CLI or vercel-labs equivalent deploy skills for other hosts; local netlify.toml knowledge; IaC tools (Pulumi/Terraform skills) for broader infra.

> Web-augmented from github.com/netlify/context-and-tools README + SKILL.md (fetched 2026). Sourced from curated config; use /review source for live evidence. Not an endorsement.
