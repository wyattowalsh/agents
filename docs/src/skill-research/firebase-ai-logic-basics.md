---
skill: firebase-ai-logic-basics
source_type: curated-external
researched_at: '2026-06-16T08:36:15Z'
research_tier: standard
mean_confidence: 0.78
---

## Purpose

Official Firebase skill for integrating Firebase AI Logic (Gemini API) into web (and mobile) apps. Covers setup, multimodal inference (text, images, audio, video, PDFs), structured output/JSON, security (App Check), client-side only without backend, hybrid on-device where available (Gemini Nano).

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; official Google/Firebase org (github.com/firebase/agent-skills); high provenance; AI/LLM integration touches model keys, usage quotas, data handling - inspect for billing/security posture and App Check enforcement even from trusted source.

## Install Prerequisites

Install: `npx skills add firebase/agent-skills --skill firebase-ai-logic-basics --skill firebase-app-hosting-basics --skill firebase-auth-basics -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`; status=inspect-then-install; selector=named; policy=Inspect source, hooks, scripts, credentials, and dedupe before install.

## Upstream Maintainer

[firebase/agent-skills](https://github.com/firebase/agent-skills) (official Firebase/Google)

## Comparable Alternatives

Other Gemini/Vertex or LLM client integration skills; general Firebase basics skills; langchain or direct SDK skills for AI.

> Evidence synthesized from public web sources (GitHub repos, official docs, skill registries); confidence reflects source reputation and public signals only. Not an endorsement.
