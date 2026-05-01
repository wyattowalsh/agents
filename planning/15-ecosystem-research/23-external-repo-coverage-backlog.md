# External Repo Coverage Backlog

## Boundary

This backlog covers the user-provided external repo set as feature/domain input. It is intentionally not an install list.

Required before promotion beyond research input:

- Pinned commit or release.
- License compatibility finding.
- Maintainer and activity finding.
- Dependency, installer, hook, and executable-surface finding.
- Secrets, network, filesystem, telemetry, and credential-behavior finding.
- Skill/MCP/plugin fit decision.
- Conformance fixture and rollback plan.
- OpenSpec change/task mapping.

## Per-Repo Coverage Queue

| id | repo | coverage lane | default outcome | integration strategy |
|---|---|---|---|---|
| EXT-001 | `JuliusBrussee/caveman` | skill lifecycle, token economy | adapt | Borrow installer/profile matrix, terseness patterns, benchmark hooks. |
| EXT-002 | `DeusData/codebase-memory-mcp` | MCP, context memory | wrap candidate | Compare persistent server value against skill-generated graph; require MCP smoke fixture. |
| EXT-003 | `tirth8205/code-review-graph` | code graph, review graph | adapt | Borrow graph schema and review fixture ideas into `agents-c11`. |
| EXT-004 | `es617/claude-replay` | session replay | adapt | Borrow replay/export artifact requirements into `agents-c12`. |
| EXT-005 | `Th0rgal/open-ralph-wiggum` | orchestration loop | reference-only | Borrow loop/status prompt-file concepts; do not import opaque automation. |
| EXT-006 | `samber/cc-skills-golang` | Go skill pack | adapt candidate | Audit as skill quality benchmark and possible external skill candidate. |
| EXT-007 | `rivet-dev/sandbox-agent` | sandbox runtime | adapt | Borrow sandbox orchestration and security model; no runtime dependency by default. |
| EXT-008 | `Prat011/awesome-llm-skills` | skill discovery | reference-only | Use as discovery source only after dedupe and source verification. |
| EXT-009 | `jhlee0409/claude-code-history-viewer` | session UI | adapt | Borrow history browser UX; keep local transcript redaction requirements. |
| EXT-010 | `remorses/kimaki` | OpenCode remote UI | reference-only | Borrow remote team chat UX only after auth/network risk review. |
| EXT-011 | `Soju06/codex-lb` | OpenAI proxy/dashboard | quarantine-reference | Treat as auth/proxy risk; no install or credential bridge. |
| EXT-012 | `kbwo/ccmanager` | session manager | adapt | Borrow multi-agent session/worktree profile management patterns. |
| EXT-013 | `Ataraxy-Labs/opensessions` | tmux session sidebar | adapt | Borrow local API and session status panel concepts. |
| EXT-014 | `fynnfluegge/agtx` | blackboard coordination | adapt | Borrow blackboard/task coordination model for task graph UX. |
| EXT-015 | `rynfar/meridian` | Claude auth bridge/proxy | quarantine-reference | Quarantine credential-sharing/proxy concepts. |
| EXT-016 | `xintaofei/codeg` | session aggregation | adapt | Borrow desktop/server session aggregation patterns. |
| EXT-017 | `griffinmartin/opencode-claude-auth` | OpenCode auth bridge | quarantine-reference | Keep as local-user-owned plugin reference only; no repo default behavior. |
| EXT-018 | `NeoLabHQ/context-engineering-kit` | context engineering skills | adopt candidate | Audit skill set for context quality, overlap, and fixtures. |
| EXT-019 | `rohitg00/skillkit` | skill installer/translator | adapt | Compare with `npx skills` and `wagents`; borrow translation patterns. |
| EXT-020 | `first-fluke/oh-my-agent` | portable harness bundle | adapt | Borrow projection/profile conventions for multi-harness adapters. |
| EXT-021 | `777genius/claude_agent_teams_ui` | multi-agent kanban UI | adapt | Borrow team UI, task logs, review workflow, context monitoring. |
| EXT-022 | `agent-sh/agentsys` | agent package system | adapt | Borrow plugins/agents/skills catalog model. |
| EXT-023 | `happier-dev/happier` | encrypted multi-agent client | reference-only | Borrow privacy model and UX; defer runtime integration. |
| EXT-024 | `guanyang/antigravity-skills` | Antigravity skill pack | adapt candidate | Audit for Antigravity support-tier input. |
| EXT-025 | `kdcokenny/ocx` | OpenCode extension manager | adapt | Borrow isolated profile and extension manager patterns. |
| EXT-026 | `joelhooks/swarm-tools` | OpenCode swarm coordination | adapt | Borrow issue tracking and learning-capability workflow concepts. |
| EXT-027 | `hosenur/portal` | OpenCode web UI | adapt | Borrow mobile-first UI and isolated workspace patterns. |
| EXT-028 | `proxysoul/soulforge` | graph-powered code intelligence | adapt | Compare graph memory strategy with other graph/context repos. |
| EXT-029 | `Human-Agent-Society/CORAL` | self-evolving multi-agent research | reference-only | Borrow eval/orchestration research patterns; avoid production dependency. |
| EXT-030 | `Weizhena/Deep-Research-skills` | research skill suite | adapt candidate | Compare to repo `research` skill and extract missing workflows. |
| EXT-031 | `peters/horizon` | terminal board/canvas | reference-only | Borrow TUI/dashboard canvas patterns. |
| EXT-032 | `muxy-app/muxy` | terminal runtime | reference-only | Borrow terminal UX patterns if license and maintenance allow. |
| EXT-033 | `0xranx/OpenContext` | personal context store | adapt | Borrow context store and desktop GUI patterns. |
| EXT-034 | `f/agentlytics` | agent analytics dashboard | adapt | Borrow metrics dashboard, usage analytics, and observability dimensions. |
| EXT-035 | `kdcokenny/opencode-worktree` | OpenCode worktree manager | adapt | Borrow worktree/profile manager patterns. |
| EXT-036 | `cortexkit/opencode-magic-context` | OpenCode context optimizer | adapt | Borrow context selection/compression patterns. |
| EXT-037 | `borski/travel-hacking-toolkit` | travel domain toolkit | reference-only | Borrow domain-specific skill packaging pattern; no advice trust by default. |
| EXT-038 | `neiii/bridle` | unverified agent-adjacent | intake-required | Verify domain, license, and executable surface before classification. |
| EXT-039 | `instavm/open-skills` | open skill registry | adapt | Use as skill registry discovery source after source-list verification. |
| EXT-040 | `shekohex/opencode-pty` | OpenCode PTY integration | adapt | Borrow PTY/session driver boundary patterns. |
| EXT-041 | `Microck/opencode-studio` | OpenCode studio UI | adapt | Borrow studio/control-surface patterns. |
| EXT-042 | `swarmclawai/swarmvault` | swarm memory/vault | intake-required | Verify memory/security posture before use. |
| EXT-043 | `zenobi-us/opencode-skillful` | OpenCode skills integration | adapt | Borrow OpenCode skill support and adapter behavior. |
| EXT-044 | `zaxbysauce/opencode-swarm` | OpenCode swarm | adapt | Borrow swarm task orchestration patterns. |
| EXT-045 | `eqtylab/cupcake` | provenance/verifiable AI artifacts | adapt | Borrow provenance/signing concepts for registry/release lanes. |
| EXT-046 | `opgginc/opencode-bar` | OpenCode status bar | adapt | Borrow status bar UX requirements. |
| EXT-047 | `vivy-company/aizen` | unverified agent tool/UX | intake-required | Verify domain, license, security, and overlap. |
| EXT-048 | `vbgate/opencode-mystatus` | OpenCode status plugin | adapt | Borrow session/status UX requirements. |
| EXT-049 | `AkaraChen/aghub` | agent hub/catalog | adapt | Borrow catalog discovery UX and registry concepts. |
| EXT-050 | `code-yeongyu/oh-my-openagent` | agent profile bundle | adapt | Borrow profile/bundle conventions. |
| EXT-051 | `Yeachan-Heo/oh-my-claudecode` | Claude Code bundle | adapt | Borrow Claude skill/profile conventions. |
| EXT-052 | `kepano/obsidian-skills` | Obsidian skill pack | adapt candidate | Audit personal knowledge skill candidates and overlap with repo Obsidian skills. |
| EXT-053 | `iOfficeAI/AionUi` | agent UI/control plane | adapt | Borrow UI patterns after license/security verification. |
| EXT-054 | `manaflow-ai/cmux` | multi-agent tmux/control | adapt | Borrow multiplexer and session-control patterns. |
| EXT-055 | `mksglu/context-mode` | context reduction/runtime | adapt | Borrow context-aware execution and continuity storage concepts. |
| EXT-056 | `humanlayer/humanlayer` | human-in-the-loop approval | adapt | Borrow approval/escalation model into governance tasks. |
| EXT-057 | `anomalyco/opentui` | terminal UI framework | adapt | Borrow TUI framework ideas for `wagents` dashboard. |
| EXT-058 | `tiann/hapi` | unverified agent/API platform | intake-required | Verify scope and risk before classifying. |
| EXT-059 | `alvinunreal/oh-my-opencode-slim` | OpenCode slim bundle | adapt | Borrow OpenCode profile conventions. |
| EXT-060 | `openchamber/openchamber` | open agent chamber | intake-required | Verify scope, license, and security posture. |
| EXT-061 | `gotalab/cc-sdd` | spec-driven Claude Code workflow | adapt | Borrow spec-driven development patterns compatible with OpenSpec. |
| EXT-062 | `michaelshimeles/ralphy` | ralph loop | reference-only | Compare status loop pattern with other Ralph repos. |
| EXT-063 | `RunMaestro/Maestro` | agent orchestration/control | adapt | Borrow orchestration/control patterns after verification. |
| EXT-064 | `mikeyobrien/ralph-orchestrator` | ralph orchestrator | reference-only | Borrow status loop pattern only; no opaque automation. |
| EXT-065 | `ZSeven-W/openpencil` | design/writing assistant | intake-required | Verify product scope and executable surface. |
| EXT-066 | `junhoyeo/tokscale` | token scaling/telemetry | adapt | Borrow token/cost telemetry requirements. |
| EXT-067 | `RAIT-09/obsidian-agent-client` | Obsidian agent client | adapt | Borrow Obsidian integration/client model after security review. |
| EXT-068 | `safishamsi/graphify` | knowledge graph skill | adopt candidate | High-priority graph/context skill candidate; verify source and fixtures. |
| EXT-069 | `VoltAgent/awesome-agent-skills` | skill discovery | reference-only | Use as discovery source only after dedupe and source verification. |
| EXT-070 | `nexu-io/open-design` | local-first design skills | adapt candidate | Borrow design systems, sandbox preview, CLI detection, artifact UX. |
| EXT-071 | `Orchestra-Research/AI-Research-SKILLs` | research/engineering skill pack | adapt candidate | Audit research and engineering skill candidates. |
| EXT-072 | `refly-ai/refly` | skill builder/platform | adapt | Borrow skill builder UX and workflow packaging. |
| EXT-073 | `google/skills` | official Google skills | adopt candidate | High-priority official skill audit; no install until source-list and fixture review. |
| EXT-074 | `antfu/skills` | curated skill pack | reference-only | Use as quality inspiration and dedupe input. |
| EXT-075 | `antvis/mcp-server-chart` | charts/visualization | wrap candidate | Prefer static skill wrapper unless live MCP rendering is justified. |
| EXT-076 | `tech-leads-club/agent-skills` | validated skill registry | adapt | Borrow secure registry and validation model. |
| EXT-077 | `iOfficeAI/OfficeCLI` | office document CLI | adopt candidate | Strong CLI-first wrapper candidate for Word/Excel/PPTX tasks. |
| EXT-078 | `microsoft/skills` | official Microsoft skills/MCP/agents | adopt candidate | High-priority official audit; split skills vs MCP vs agents. |
| EXT-079 | `jeremylongshore/claude-code-plugins-plus-skills` | Claude marketplace/catalog | reference-only | Borrow marketplace/catalog UX and intake-scale patterns. |
| EXT-080 | `supabase/agent-skills` | official Supabase skills | adopt candidate | High-priority official skill audit and reference-model comparison. |
| EXT-081 | `bergside/design-md-chrome` | design extraction extension | adapt | Borrow DESIGN.md generation and browser-extension intake requirements. |
| EXT-082 | `himself65/finance-skills` | finance skill pack | reference-only | Borrow packaging patterns; require finance-risk disclaimers before use. |
| EXT-083 | `cloudflare/skills` | official Cloudflare skills | adopt candidate | High-priority official skill audit and overlap check with current Cloudflare skills. |
| EXT-084 | `SnailSploit/Claude-Red` | offensive security skills | quarantine | Red-team-only; never install by default. |
| EXT-085 | `OpenCoworkAI/open-cowork` | desktop/control plane | adapt | Borrow one-click install, sandbox isolation, and skill/MCP UX. |
| EXT-086 | `conorluddy/ios-simulator-skill` | iOS simulator skill | adapt candidate | Audit xcodebuild wrapper, simulator safety, fixtures. |
| EXT-087 | `imxv/Pretty-mermaid-skills` | Mermaid rendering skill | adopt candidate | Audit docs/diagram output skill with SVG/ASCII fixtures. |
| EXT-088 | `agentscope-ai/OpenJudge` | evaluation framework | adapt | Borrow eval/reward/benchmark model. |
| EXT-089 | `skillmatic-ai/awesome-agent-skills` | skill discovery | reference-only | Use as discovery source after dedupe and source verification. |
| EXT-090 | `enulus/OpenPackage` | universal package manager | adapt | Borrow package manager/organizer model. |
| EXT-091 | `millionco/react-doctor` | React diagnostic tool | adapt | Borrow frontend diagnostics skill/tool requirements. |
| EXT-092 | `uditgoenka/autoresearch` | autoresearch skill | adapt candidate | Compare research iteration workflow with repo `research` skill. |
| EXT-093 | `meodai/skill.color-expert` | color design skill | adopt candidate | Audit color/design skill and fixture expectations. |

## Priority Waves

### Wave A: Official And High-Trust Skill Sources

Targets: `google/skills`, `microsoft/skills`, `supabase/agent-skills`, `cloudflare/skills`, `tech-leads-club/agent-skills`.

Output: source-list evidence, license/provenance matrix, duplicate coverage report, fixture plan, and install command candidates with no execution.

### Wave B: Repo-Native Capability Gaps

Targets: graph/context, session replay, telemetry, OpenCode adapters, skill lifecycle, design/artifact generation.

Output: clean-room feature requirements and local implementation specs.

### Wave C: UI And Control Plane Borrowing

Targets: team dashboards, OpenCode UIs, tmux/session UIs, status bars, terminal UI frameworks.

Output: UX patterns, data contracts, and prototype requirements without importing upstream apps.

### Wave D: Quarantine And Threat Modeling

Targets: auth bridges, proxy/account-sharing, offensive security, any repo with credential or remote execution behavior.

Output: security quarantine records, denied-by-default policy, and threat-model exemplars.
