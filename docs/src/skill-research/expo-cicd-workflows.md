---
skill: expo-cicd-workflows
source_type: curated-external
researched_at: '2026-06-16T08:35:57Z'
research_tier: standard
mean_confidence: 0.76
---

## Purpose

Helps understand and author EAS workflow YAML for Expo projects. Guidance for CI/CD, build pipelines, deployment automation using Expo Application Services (EAS). Use when .eas/workflows/ or EAS build topics arise.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Expo org; covers CI config surface which can affect credentials/secrets and billing; inspect recommended for org policy fit despite official source. No direct code exec in skill itself.

## Install Prerequisites

Install: `npx skills add expo/skills --skill building-native-ui --skill expo-dev-client --skill expo-deployment --skill expo-cicd-workflows --skill upgrading-expo -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[expo/skills](https://github.com/expo/skills) (official Expo team)

## Comparable Alternatives

General GitHub Actions or EAS-free CI skills; deployment focused skills for other platforms.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
