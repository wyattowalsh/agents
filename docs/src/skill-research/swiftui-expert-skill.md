---
skill: swiftui-expert-skill
source_type: curated-external
researched_at: '2026-06-16T08:40:14Z'
research_tier: standard
mean_confidence: 0.78
---

## Purpose

SwiftUI Expert Skill: expert best-practices guidance for AI coding tools in Agent Skills format. Covers state management (property wrappers, @Observable, data flow), view composition/extraction/identity, performance (hot paths, lazy, granularity), lists & ForEach (stable id, Table, filtering), navigation/sheets (NavigationStack/SplitView, Inspector, enum sheets), Swift Charts (marks/axes/selection/styling/a11y/Chart3D), animations (implicit/explicit, transitions, keyframes, @Animatable), macOS (scenes, multi-window, Table, styling, AppKit interop), iOS 26+ Liquid Glass effects + fallbacks, accessibility (VoiceOver, Dynamic Type, traits), image optimization (AsyncImage, downsampling, cache), latest APIs migration (iOS 15+), previews, focus/scroll/text/layout patterns, localization. Includes unique executable Python xctrace-based Instruments trace recorder/analyzer (time profiler, hangs, hitches, SwiftUI updates/causes) for diagnosing perf issues with structured JSON+md output. Non-opinionated, correctness/performance focus. 16.6k weekly installs, 3k stars. MIT. Complements author's Swift Concurrency skill.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Install: npx skills add ... --skill swiftui-expert-skill; Claude Code plugin (marketplace + install, or .claude/settings.json for teams); Cursor plugin; Codex via agents/openai.yaml or copy; pi pkg mgr; manual symlink. Skill + 20+ references/ load on-demand.

## Trust And Risks

Curated install-now-after-trust-gate / curated-trust-gated. MIT. High adoption (16.6k weekly). Authors AvdLee (Antoine van der Lee, SwiftLee) + Omar Elsayed. 261 commits, frequent releases (4.0.0). Strong structure with SKILL.md + references/ + executable tools for traces. Maintenance workflow for API freshness (requires Sosumi MCP). Complements avdlee/swift-concurrency-agent-skill per config. Risks: domain-specific UI guidance; review generated SwiftUI for target iOS/macOS versions; trace tools require Xcode/xctrace and device/sim access; high visibility reduces unknown risk but always audit before broad adoption. npx provenance verified.

## Install Prerequisites


[38;5;250m███████╗██╗  ██╗██╗██╗     ██╗     ███████╗[0m
[38;5;248m██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝[0m
[38;5;245m███████╗█████╔╝ ██║██║     ██║     ███████╗[0m
[38;5;243m╚════██║██╔═██╗ ██║██║     ██║     ╚════██║[0m
[38;5;240m███████║██║  ██╗██║███████╗███████╗███████║[0m
[38;5;238m╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝[0m

┌   skills 
│
│  Tip: use the --yes (-y) and --global (-g) flags to install without prompts.
[?25l│
◇  Source: https://github.com/avdlee/swiftui-agent-skill.git
[?25h[?25l│
◒  Cloning repository[999D[J◐  Cloning repository[999D[J◓  Cloning repository[999D[J◑  Cloning repository[999D[J◒  Cloning repository[999D[J◐  Cloning repository[999D[J◓  Cloning repository[999D[J◑  Cloning repository[999D[J◒  Cloning repository.[999D[J◐  Cloning repository.[999D[J◓  Cloning repository.[999D[J◑  Cloning repository.[999D[J◒  Cloning repository.[999D[J◇  Repository cloned
[?25h[?25l│
[999D[J◇  Found 2 skills
[?25h│
●  Selected 1 skill: swiftui-expert-skill
│
■  Invalid agents: grok
│
●  Valid agents: aider-desk, amp, antigravity, antigravity-cli, astrbot, autohand-code, augment, bob, claude-code, openclaw, cline, codearts-agent, codebuddy, codemaker, codestudio, codex, command-code, continue, cortex, crush, cursor, deepagents, devin, dexto, droid, firebender, forgecode, gemini-cli, github-copilot, goose, hermes-agent, inference-sh, jazz, junie, iflow-cli, kilo, kimi-code-cli, kiro-cli, kode, lingma, loaf, mcpjam, mistral-vibe, moxby, mux, opencode, openhands, ona, pi, qoder, qoder-cn, qwen-code, replit, reasonix, rovodev, roo, tabnine-cli, terramind, tinycloud, trae, trae-cn, warp, windsurf, zed, zencoder, zenflow, neovate, pochi, promptscript, adal, universal

status=install-now-after-trust-gate; selector=source-spec/named. Plugin or manual options per README. Verification: agent should reference SKILL.md workflows/checklists and load references on demand. Node for some packaging; Xcode for trace tooling.

## Upstream Maintainer

AvdLee / Antoine van der Lee + Omar Elsayed (github.com/AvdLee/SwiftUI-Agent-Skill; avanderlee.com, swiftdifferently.com). MIT. 3k stars. Companion skills from author: Swift Concurrency, Core Data, Swift Testing. Inspired by Dimillian/Skills and jordibruin Swift Charts Examples. Includes AGENTS.md, CONTRIBUTING, release automation. Active sponsorship.

## Comparable Alternatives

Author's swift-concurrency (same maintainer); other SwiftUI or iOS UI skills (e.g. from Dimillian or antfu web-design); official Apple SwiftUI / Human Interface Guidelines docs + sample code; Instruments + SwiftUI inspector without agent skill layer; general mobile UI or design system skills.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
