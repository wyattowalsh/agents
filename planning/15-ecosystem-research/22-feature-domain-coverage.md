# External Feature And Domain Coverage

## Purpose

This research note ensures the external repository universe is covered as a set of feature/domain requirements for the agents platform overhaul. It does not promote, install, vendor, or trust any external repository by default.

Coverage rule: every repository becomes one of these outputs.

- **Integrate as skill/tool** when the upstream artifact is already a skill, CLI-backed tool, or official vendor skill pack and passes license, provenance, security, fixture, and OpenSpec gates.
- **Wrap** when the upstream value depends on live external state or a long-running server and the MCP/live-system model is justified by a smoke fixture.
- **Borrow logic as clean-room requirements** when the repo is useful as a product, UX, orchestration, or architecture reference but should not become a dependency.
- **Quarantine** when the repo touches credentials, account sharing, auth bridges, proxies, offensive security, or opaque automation.

## Research Triage

Complexity score: 9/10, Exhaustive.

- Scope breadth: 2. The set spans skills, MCP, harness plugins, UI/control planes, telemetry, context graphs, sandboxing, security, design, evaluation, and domain tools.
- Source difficulty: 2. Many repos are community projects with unknown license, maintenance, executable surface, or source-list behavior.
- Temporal sensitivity: 2. OpenCode, Claude Code, skills registries, and official vendor skills are moving quickly.
- Verification complexity: 2. Promotion requires independent license/security/provenance verification, not only README claims.
- Synthesis demand: 1. The near-term output is a coverage map and dispatch backlog; later lanes perform repo-level verification.

Current run mode: degraded planning mode. This document is ledger-backed and source-aware, but it is not a completed source audit. Confidence remains capped at 0.6 for repo-specific claims until each repo is inspected at a pinned revision.

## Domain Taxonomy

| Domain | Coverage Goal | Primary Output | Candidate Repos |
|---|---|---|---|
| Skill packs and registries | Expand skill catalog safely without registry drift or duplicate installs. | Skill registry intake queue, external skill audit tasks, fixture requirements. | `samber/cc-skills-golang`, `Prat011/awesome-llm-skills`, `NeoLabHQ/context-engineering-kit`, `guanyang/antigravity-skills`, `Weizhena/Deep-Research-skills`, `instavm/open-skills`, `kepano/obsidian-skills`, `Orchestra-Research/AI-Research-SKILLs`, `google/skills`, `antfu/skills`, `tech-leads-club/agent-skills`, `microsoft/skills`, `supabase/agent-skills`, `himself65/finance-skills`, `cloudflare/skills`, `conorluddy/ios-simulator-skill`, `imxv/Pretty-mermaid-skills`, `skillmatic-ai/awesome-agent-skills`, `uditgoenka/autoresearch`, `meodai/skill.color-expert` |
| Skill lifecycle and portability | Improve skill install, translation, validation, packaging, and support tiers. | `wagents` skill lifecycle requirements and registry schemas. | `JuliusBrussee/caveman`, `rohitg00/skillkit`, `first-fluke/oh-my-agent`, `agent-sh/agentsys`, `zenobi-us/opencode-skillful`, `refly-ai/refly`, `enulus/OpenPackage` |
| MCP and live-system tools | Keep MCP only for live state, server-side rendering, authenticated APIs, or persistent query services. | MCP audit queue and smoke-fixture requirements. | `DeusData/codebase-memory-mcp`, `antvis/mcp-server-chart`, plus any future verified live-state candidates |
| Knowledge graph and context memory | Build repo-native context graph, code-review graph, memory, and retrieval lanes. | Skill-generated graph first; optional MCP only if persistent live query server is justified. | `tirth8205/code-review-graph`, `proxysoul/soulforge`, `0xranx/OpenContext`, `mksglu/context-mode`, `swarmclawai/swarmvault`, `RAIT-09/obsidian-agent-client` |
| Session replay and telemetry | Add session history, replay, token/cost, analytics, and run graph requirements. | Session telemetry OpenSpec tasks and `wagents` observability backlog. | `es617/claude-replay`, `jhlee0409/claude-code-history-viewer`, `xintaofei/codeg`, `f/agentlytics`, `junhoyeo/tokscale` |
| Multi-agent orchestration | Cover blackboards, swarms, task boards, approvals, human escalation, and autonomous loops. | Orchestration and UI/control-plane requirements with safety gates. | `Th0rgal/open-ralph-wiggum`, `kbwo/ccmanager`, `fynnfluegge/agtx`, `777genius/claude_agent_teams_ui`, `joelhooks/swarm-tools`, `Human-Agent-Society/CORAL`, `zaxbysauce/opencode-swarm`, `humanlayer/humanlayer`, `openchamber/openchamber`, `michaelshimeles/ralphy`, `RunMaestro/Maestro`, `mikeyobrien/ralph-orchestrator`, `OpenCoworkAI/open-cowork` |
| Harness adapters and profile managers | Cover Claude Code, OpenCode, Codex/OpenAI, Cursor, Antigravity, and profile/bundle projection patterns. | Harness-specific child changes and adapter manifests. | `first-fluke/oh-my-agent`, `guanyang/antigravity-skills`, `kdcokenny/ocx`, `kdcokenny/opencode-worktree`, `zenobi-us/opencode-skillful`, `code-yeongyu/oh-my-openagent`, `Yeachan-Heo/oh-my-claudecode`, `alvinunreal/oh-my-opencode-slim`, `jeremylongshore/claude-code-plugins-plus-skills` |
| OpenCode UI and plugins | Cover OpenCode session UX, status bars, PTY, worktrees, studio/control surfaces, context plugins, and swarms. | OpenCode/Gemini harness lane plus UI/CLI backlog. | `remorses/kimaki`, `kdcokenny/ocx`, `hosenur/portal`, `kdcokenny/opencode-worktree`, `cortexkit/opencode-magic-context`, `shekohex/opencode-pty`, `Microck/opencode-studio`, `zenobi-us/opencode-skillful`, `zaxbysauce/opencode-swarm`, `opgginc/opencode-bar`, `vbgate/opencode-mystatus`, `manaflow-ai/cmux`, `alvinunreal/oh-my-opencode-slim` |
| UI/control planes and dashboards | Cover local/desktop/web/mobile UIs for teams, sessions, catalogs, analytics, dashboards, and one-click workflows. | UX/CLI and multi-agent UI pattern tasks. | `jhlee0409/claude-code-history-viewer`, `remorses/kimaki`, `ccmanager`, `opensessions`, `hosenur/portal`, `peters/horizon`, `muxy-app/muxy`, `f/agentlytics`, `Microck/opencode-studio`, `AionUi`, `cmux`, `opentui`, `OpenCoworkAI/open-cowork`, `openchamber/openchamber`, `openpencil` |
| Sandboxing and execution safety | Cover safe code execution, isolated workspaces, PTY/runtime boundaries, and CI/eval sandboxes. | Config safety, CI/evals, and quarantine requirements. | `rivet-dev/sandbox-agent`, `shekohex/opencode-pty`, `OpenCoworkAI/open-cowork`, `enulus/OpenPackage` |
| Security, credentials, proxying, and offensive use | Quarantine or reference-only. Never install or bridge credentials by default. | Security quarantine lane, threat model prompts, deny-by-default policy. | `Soju06/codex-lb`, `rynfar/meridian`, `griffinmartin/opencode-claude-auth`, `SnailSploit/Claude-Red`, plus any repo found to store/share credentials |
| Provenance, trust, and evaluation | Cover verifiable artifacts, eval harnesses, source locks, reward/judge systems, and registry trust. | Registry core, CI/evals/observability, release/archive tasks. | `eqtylab/cupcake`, `agentscope-ai/OpenJudge`, `tech-leads-club/agent-skills`, `google/skills`, `microsoft/skills`, `cloudflare/skills`, `supabase/agent-skills` |
| Design, diagrams, artifacts, and frontend diagnostics | Cover design systems, color, diagrams, charting, browser extraction, office/docs, and React diagnostics. | Design/document skills, docs generation, artifact/preview CLI requirements. | `nexu-io/open-design`, `antvis/mcp-server-chart`, `iOfficeAI/OfficeCLI`, `bergside/design-md-chrome`, `imxv/Pretty-mermaid-skills`, `millionco/react-doctor`, `meodai/skill.color-expert` |
| Domain-specific skills | Cover vertical skill packaging patterns while preserving legal, safety, and advice disclaimers. | Domain-skill intake queue with warnings and fixture contracts. | `borski/travel-hacking-toolkit`, `kepano/obsidian-skills`, `himself65/finance-skills`, `conorluddy/ios-simulator-skill` |

## Integration Principles

1. Prefer repo-native skills for deterministic, portable workflows.
2. Promote official vendor skill packs only after source-list, license, executable-surface, and fixture review.
3. Use MCP only when a capability needs live external state, a server process, current browser/runtime state, authenticated SaaS, telemetry streams, or persistent query service semantics.
4. Treat UI/control-plane repos as product and architecture references first; build repo-native `wagents` surfaces instead of importing opaque apps.
5. Treat auth/proxy/offensive repos as quarantine references until `agents-c15-security-quarantine` produces explicit policy and threat-model approval.
6. Borrow logic as clean-room requirements, not copied implementation, unless a later lane records license compatibility and pinned provenance.
7. Every promoted skill/tool must define conformance fixtures, rollback, docs/instruction sync, and OpenSpec traceability.

## Required Feature Coverage

| Feature Area | Must Be Covered By Platform | Required Lane |
|---|---|---|
| Skill discovery and source-list audit | Registry sources, source-list output, dedupe, support tiers, install command generation. | `agents-c13-skill-registry-intake` |
| Skill quality benchmark | Frontmatter, descriptions, scripts, hooks, fixture tests, docs shape, portability. | `agents-c02-skills-lifecycle` |
| Official vendor skill intake | Google, Microsoft, Supabase, Cloudflare skills as high-priority but still gated. | `agents-c13-skill-registry-intake` |
| Language/domain packs | Go, Obsidian, finance, iOS simulator, research, design, mermaid, color, office, React diagnostics. | `agents-c02-skills-lifecycle`, `agents-c13-skill-registry-intake` |
| Codebase graph/context memory | Graph build, query, code review graph, memory freshness, local cache policy. | `agents-c11-knowledge-graph-context` |
| Session replay/history | Replay export, transcript redaction, run graph, searchable sessions, history viewer patterns. | `agents-c12-session-telemetry` |
| Token/cost analytics | Token scale, cost summaries, context usage trends, quota/status surfaces. | `agents-c12-session-telemetry`, `agents-c07-ci-evals-observability` |
| Multi-agent coordination | Blackboard, task graph, swarm, team UI, approval gates, human escalation. | `agents-c14-multiagent-ui-patterns`, `agents-c05-ux-cli` |
| OpenCode extensions | Worktree, PTY, status bar, studio, skills integration, context optimizer, swarms. | `agents-c04-opencode-gemini-harness` |
| Harness profile bundles | Claude, Codex/OpenAI, Copilot, Cursor, Gemini, Antigravity, OpenCode, experimental harnesses. | `agents-c04-*` lanes |
| Safe sandboxing | Isolated workspace/run model, PTY boundary, ephemeral execution, eval sandbox policy. | `agents-c06-config-safety`, `agents-c07-ci-evals-observability` |
| MCP conformance | Secrets model, transport model, sandbox model, smoke fixture, live-state justification. | `agents-c03-mcp-audit` |
| UI/control plane | Dashboard, task board, session browser, status panels, mobile-first view, terminal UI references. | `agents-c05-ux-cli`, `agents-c14-multiagent-ui-patterns` |
| Artifact/design generation | DESIGN.md extraction, chart/diagram rendering, color expertise, docs previews, office docs. | `agents-c02-skills-lifecycle`, `agents-c08-docs-instructions` |
| Provenance and release trust | Signed/provenance metadata, source locks, release archive, rollback. | `agents-c01-registry-core`, `agents-c09-release-archive` |
| Evaluations and judges | Eval framework, judge/reward workflows, skill conformance evals, regression gates. | `agents-c07-ci-evals-observability` |
| Quarantine | Auth bridges, proxies, credential-sharing, offensive tooling, high-risk finance/security warnings. | `agents-c15-security-quarantine` |

## Confidence Landscape

| Claim | Confidence | Basis | Gap |
|---|---:|---|---|
| Agent Skills should remain the default integration path. | 0.6 | Repo policy and attached ledger agree. | Needs per-repo source inspection before promotion. |
| MCP should be reserved for live-state/server-backed capabilities. | 0.6 | Repo AGENTS policy and attached ledger agree. | Needs MCP smoke fixture design. |
| The current repo set spans at least 13 feature domains. | 0.6 | Ledger domains and user-provided URL set. | Needs pinned repo metadata and README inspection. |
| Auth/proxy/offensive repos require quarantine. | 0.6 | Repo policy and ledger security posture. | Needs explicit threat model per candidate. |
| Official vendor skill packs are high-priority candidates. | 0.6 | Ledger labels and source-owner authority. | Needs source-list, license, executable-surface, and fixture audit. |

## Open Questions For Child Lanes

1. Which official vendor skill packs should be inspected first once non-Markdown work is allowed: Google, Microsoft, Supabase, or Cloudflare?
2. Should `antvis/mcp-server-chart` be treated as a static skill wrapper, a live MCP server, or both behind separate support tiers?
3. Should UI/control-plane work target a terminal-first `wagents` dashboard first or a browser-based dashboard first?
4. Should session replay store only local redacted summaries by default, or preserve full transcripts behind explicit opt-in?
5. Which quarantine repos should become threat-model exemplars versus being excluded from the active backlog?
