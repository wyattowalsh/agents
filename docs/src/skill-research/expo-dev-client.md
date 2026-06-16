---
skill: expo-dev-client
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Guidance around Expo Dev Client for custom development builds, native module integration, and debugging flows distinct from Expo Go. Complements other Expo UI and deployment skills.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Expo source; dev client involves native builds and potential custom native code - higher surface for review before install in shared envs.

## Install Prerequisites

Install: `npx skills add expo/skills --skill building-native-ui --skill expo-dev-client --skill expo-deployment --skill expo-cicd-workflows --skill upgrading-expo -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[expo/skills](https://github.com/expo/skills) (official Expo team)

## Comparable Alternatives

React Native dev client or custom build skills; general native module integration guidance.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
