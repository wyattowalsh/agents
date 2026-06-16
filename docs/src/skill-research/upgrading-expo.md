---
skill: upgrading-expo
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.75
---

## Purpose

Guidance for upgrading Expo SDKs, handling breaking changes, migration of config/plugins, and maintaining compatibility across Expo versions and related native deps.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Expo; upgrade paths touch dependency graphs, native code, and can introduce instability - inspect for project-specific risk tolerance.

## Install Prerequisites

Install: `npx skills add expo/skills --skill building-native-ui --skill expo-dev-client --skill expo-deployment --skill expo-cicd-workflows --skill upgrading-expo -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[expo/skills](https://github.com/expo/skills) (official Expo team)

## Comparable Alternatives

General dependency upgrade or React Native upgrade skills; migration guide skills for other frameworks.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
