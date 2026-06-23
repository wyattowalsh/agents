---
skill: expo-deployment
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Streamlines deployment and release processes for Expo apps to stores and EAS. Covers build, submit, update, and production rollout topics for mobile/web Expo projects.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official from Expo; involves deployment secrets, app store creds, update channels - warrants inspection for least-privilege and org compliance even from trusted maintainer.

## Install Prerequisites

Install: `npx skills add expo/skills --skill expo-dev-client --skill expo-deployment --skill expo-cicd-workflows --skill upgrading-expo -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[expo/skills](https://github.com/expo/skills) (official Expo team)

## Comparable Alternatives

General mobile deployment or EAS CLI wrapper skills; store submission skills.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
