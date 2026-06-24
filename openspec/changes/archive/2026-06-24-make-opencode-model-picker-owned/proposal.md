# Proposal

## Problem

OpenCode model selection previously moved toward picker-owned state, but the
current runtime requirement is explicit build and plan defaults with a small
set of selectable high-effort provider alternatives. Leaving the picker-owned
proposal active contradicts repo and live config generation.

## Intent

Make OpenCode build and plan defaults repo-managed while keeping the TUI model
picker useful through explicit provider variants.

## Scope

- Set root `model` to `openai/gpt-5.5` and root `small_model` to
  `openai/gpt-5.4-mini`.
- Set build agent defaults to `openai/gpt-5.5` variant `high`.
- Set plan agent defaults to `openai/gpt-5.5` variant `xhigh`.
- Keep selectable variants for OpenAI, Vercel OpenAI, Vercel xAI Grok 4.3,
  OpenCode Go Kimi K2.6, and Moonshot Kimi for Coding.
- Preserve plugin-owned provider options such as `websearch_cited`.

## Out Of Scope

- Falling back from `openai/gpt-5.5`.
- Removing TUI model picker support.
