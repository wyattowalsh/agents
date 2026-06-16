---
skill: anthropics-skills-all
source_type: curated-external
researched_at: '2026-06-16T08:36:37Z'
research_tier: standard
mean_confidence: 0.78
---

## Purpose

Official Anthropic skills repository demonstrating the Agent Skills system for Claude. Contains example skills across creative/design, development/technical, enterprise/comms, plus production document creation/editing capabilities (docx, pdf, pptx, xlsx) and the skills spec/template. The `anthropics-skills-all` entry represents the full/wildcard source (many individual skills available). Skills are self-contained SKILL.md + resources for repeatable task performance; some open (Apache 2.0), document skills source-available as reference.

## Harness Coverage

No specific target agents listed in the avoid/global-only entry (install_command empty). In general the source supports Claude Code (via /plugin), Claude.ai (paid plans), and API. Config entry is marked global-only-or-avoid to discourage broad install.

## Trust And Risks

global-only-or-avoid / global-only-or-avoid. Massive official Anthropic repo (151k stars). Disclaimer: provided for demonstration/educational purposes only; implementations may differ from production Claude; always test thoroughly before critical use. Many skills duplicate local/system skills per config rationale for avoid classification. Case-by-case inspection required; broad wildcard install not recommended. High authority source but scope overlap and demo nature are key risks. Apache 2.0 or source-available licenses.

## Install Prerequisites

No direct curated install command for the -all wildcard in this status section (see config/external-skills.md for explicit avoid note). General install via Claude Code plugin marketplace (anthropic-agent-skills), document-skills or example-skills sub-plugins, or skills.sh. Selector would be wildcard or broad. Status explicitly global-only-or-avoid.

## Upstream Maintainer

Anthropic (github.com/anthropics/skills; anthropic.com). Official. Includes partner examples (e.g. Notion). Links to full skills docs and engineering post on Agent Skills. 151k stars, active.

## Comparable Alternatives

Local or repo-owned skills for document handling, creative tasks, or specific workflows; narrower curated skills from other sources; direct use of Claude native document features or MCP where applicable instead of broad third-party skill bundles; custom skills built from the included template/spec.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
