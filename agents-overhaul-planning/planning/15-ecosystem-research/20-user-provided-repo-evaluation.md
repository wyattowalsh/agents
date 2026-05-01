# User-Provided Repository Evaluation Ledger

Generated: `2026-05-01T10:44:04.042207+00:00`

## Purpose

This ledger turns the complete user-provided external repository universe into actionable ingredients for the `wyattowalsh/agents` planning corpus. It separates discovery from promotion.

- Discovery may use GitHub pages, awesome lists, MCP indexes, and community repos.
- Promotion into `skills/`, `mcp/`, `wagents/`, or harness-specific adapters requires license review, source verification, security review, conformance fixtures, and OpenSpec traceability.
- Agent Skills remain the default promotion path. MCP is reserved for live external state, browser/runtime interaction, authenticated SaaS, current web/search/docs data, database/cloud state, or telemetry streams.

## Decision Labels

| Label | Meaning |
|---|---|
| `adopt-candidates` | Strong candidate to become a first-class skill/tool after audit. |
| `adapt` | Extract architecture, CLI, UX, registry, eval, or docs patterns. |
| `wrap` | Keep upstream behavior but expose through a skill wrapper or guarded MCP profile. |
| `fork` | Only after legal/security review and clear maintenance plan. |
| `reference-only` | Use as design/UX/research input, not runtime dependency. |
| `quarantine` | Security-sensitive; never install by default. |
| `intake-required` | Must be inspected by an external-repo intake subagent before classification changes. |

## Evaluation Matrix

| id | repo | domain | initial_action | skills_first_fit | mcp_fit | primary_integration_surface | security_posture | recommended_next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXT-001 | JuliusBrussee/caveman | token-economy skill/plugin | adapt | high | low | skills/ | review-required | extract installer/profile matrix, terseness skill pattern, benchmark/eval/hook ideas |
| EXT-002 | DeusData/codebase-memory-mcp | codebase memory MCP | wrap | medium | medium | mcp/ | review-required | compare with graphify/code-review-graph; keep MCP only if persistent live query server beats skill-generated graph |
| EXT-003 | tirth8205/code-review-graph | code-review knowledge graph | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | reference code graph review patterns and fixtures |
| EXT-004 | es617/claude-replay | session replay exporter | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | session replay artifacts for run graph/observability lane |
| EXT-005 | Th0rgal/open-ralph-wiggum | ralph loop orchestrator | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | extract loop/status/prompt-file patterns; avoid opaque automation by default |
| EXT-006 | samber/cc-skills-golang | language skill pack | adapt | high | low | skills/ | review-required | skill quality benchmark for Go; use as external skill candidate |
| EXT-007 | rivet-dev/sandbox-agent | sandbox runtime/control API | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | sandbox orchestration pattern for CI/evals; security review required |
| EXT-008 | Prat011/awesome-llm-skills | awesome skill list | reference-only | high | low | skills/ | intake-review | discovery input for registry intake |
| EXT-009 | jhlee0409/claude-code-history-viewer | Claude history desktop viewer | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | session browser UX ingredients |
| EXT-010 | remorses/kimaki | OpenCode Discord UI | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | remote team chat UI patterns; avoid direct integration until auth reviewed |
| EXT-011 | Soju06/codex-lb | Codex/ChatGPT account LB dashboard | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | OpenAI-compatible proxy/dashboard patterns; high auth risk |
| EXT-012 | kbwo/ccmanager | multi-agent session manager | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | session/worktree profile management patterns |
| EXT-013 | Ataraxy-Labs/opensessions | tmux agent session sidebar | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | local HTTP API + session status panel pattern |
| EXT-014 | fynnfluegge/agtx | blackboard/task coordination | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | blackboard from idea to merge; integrate with task graph UX |
| EXT-015 | rynfar/meridian | Claude Max bridge/proxy | reference-only | low | low | wagents/ + planning/ + docs/ | quarantine-required | auth bridge pattern; avoid credential sharing integration |
| EXT-016 | xintaofei/codeg | agent session aggregator | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | session aggregation desktop/server patterns |
| EXT-017 | griffinmartin/opencode-claude-auth | OpenCode Claude auth plugin | reference-only | low | low | wagents/ + planning/ + docs/ | quarantine-required | credential re-use pattern; high security risk |
| EXT-018 | NeoLabHQ/context-engineering-kit | context engineering skills | adopt-candidates | high | low | skills/ | review-required | evaluate skills for context quality and skill registry |
| EXT-019 | rohitg00/skillkit | portable skill installer/translator | adapt | high | low | skills/ | review-required | compare with npx skills + wagents; extract translation patterns |
| EXT-020 | first-fluke/oh-my-agent | portable .agents harness | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | harness projection patterns |
| EXT-021 | 777genius/claude_agent_teams_ui | multi-agent kanban/control plane | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | team UI, task logs, review workflow, context monitoring |
| EXT-022 | agent-sh/agentsys | agent package system | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | plugins/agents/skills cataloging patterns |
| EXT-023 | happier-dev/happier | encrypted multi-agent client | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | privacy model and UX patterns |
| EXT-024 | guanyang/antigravity-skills | Antigravity skill pack | adapt | high | low | skills/ | review-required | Antigravity support tier candidate |
| EXT-025 | kdcokenny/ocx | OpenCode extension manager | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | OpenCode isolated profile manager |
| EXT-026 | joelhooks/swarm-tools | OpenCode swarm coordination | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | issue tracking / learning capabilities |
| EXT-027 | hosenur/portal | OpenCode web UI | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | mobile-first UI and isolated workspace patterns |
| EXT-028 | proxysoul/soulforge | graph-powered code intelligence | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | compare code graph memory strategies |
| EXT-029 | Human-Agent-Society/CORAL | multi-agent self-evolution research infra | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | orchestration/eval pattern, not direct production |
| EXT-030 | Weizhena/Deep-Research-skills | deep research skill | adapt | high | low | skills/ | review-required | external skill candidate; compare to repo research skill |
| EXT-031 | peters/horizon | terminal board/canvas | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | TUI/dashboard canvas pattern |
| EXT-032 | muxy-app/muxy | terminal runtime | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | terminal UX reference |
| EXT-033 | 0xranx/OpenContext | personal context store | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | context store and desktop GUI patterns |
| EXT-034 | f/agentlytics | agent analytics dashboard | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | metrics dashboard + usage analytics |
| EXT-035 | kdcokenny/opencode-worktree | OpenCode worktree manager | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | worktree profile patterns |
| EXT-036 | cortexkit/opencode-magic-context | OpenCode context optimizer | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | context compression/selection patterns |
| EXT-037 | borski/travel-hacking-toolkit | domain skill/toolkit | reference-only | high | low | skills/ | intake-review | domain-specific skill packaging example |
| EXT-038 | neiii/bridle | unknown/agent adjacent | intake-required | low | low | wagents/ + planning/ + docs/ | intake-review | verify repo; do not integrate until reviewed |
| EXT-039 | instavm/open-skills | open skills registry | adapt | high | low | skills/ | review-required | skill registry discovery source |
| EXT-040 | shekohex/opencode-pty | OpenCode PTY integration | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | PTY/session driver pattern |
| EXT-041 | Microck/opencode-studio | OpenCode studio UI | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | OpenCode UI/control surface pattern |
| EXT-042 | swarmclawai/swarmvault | swarm memory/vault | intake-required | low | low | wagents/ + planning/ + docs/ | intake-review | memory/security evaluation |
| EXT-043 | zenobi-us/opencode-skillful | OpenCode skill integration | adapt | high | low | skills/ | review-required | OpenCode skills support reference |
| EXT-044 | zaxbysauce/opencode-swarm | OpenCode swarm | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | swarm task orchestration |
| EXT-045 | eqtylab/cupcake | provenance/verifiable AI artifacts | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | provenance/signing lane |
| EXT-046 | opgginc/opencode-bar | OpenCode status bar | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | status bar UX |
| EXT-047 | vivy-company/aizen | agent tool/UX | intake-required | low | low | wagents/ + planning/ + docs/ | intake-review | verify license/security/domain |
| EXT-048 | vbgate/opencode-mystatus | OpenCode status plugin | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | session/status UX |
| EXT-049 | AkaraChen/aghub | agent hub/catalog | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | catalog discovery UX |
| EXT-050 | code-yeongyu/oh-my-openagent | agent profile bundle | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | profile/bundle conventions |
| EXT-051 | Yeachan-Heo/oh-my-claudecode | Claude Code bundle | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | Claude skill/profile conventions |
| EXT-052 | kepano/obsidian-skills | Obsidian skill pack | adapt | high | low | skills/ | review-required | personal knowledge skill candidate |
| EXT-053 | iOfficeAI/AionUi | agent UI/control plane | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | UI patterns, verify license/security |
| EXT-054 | manaflow-ai/cmux | multi-agent tmux/control | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | session multiplexer pattern |
| EXT-055 | mksglu/context-mode | context reduction/runtime | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | context-aware execution and SQLite continuity |
| EXT-056 | humanlayer/humanlayer | human-in-the-loop approval | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | approval/human escalation pattern |
| EXT-057 | anomalyco/opentui | terminal UI framework | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | TUI framework for wagents dashboard |
| EXT-058 | tiann/hapi | agent/api platform | intake-required | low | low | wagents/ + planning/ + docs/ | intake-review | verify |
| EXT-059 | alvinunreal/oh-my-opencode-slim | OpenCode slim bundle | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | OpenCode profile conventions |
| EXT-060 | openchamber/openchamber | open agent chamber | intake-required | low | low | wagents/ + planning/ + docs/ | intake-review | verify |
| EXT-061 | gotalab/cc-sdd | spec-driven dev for Claude Code | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | OpenSpec/spec workflow patterns |
| EXT-062 | michaelshimeles/ralphy | ralph loop | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | compare with open-ralph |
| EXT-063 | RunMaestro/Maestro | agent orchestration/control | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | orchestration patterns, verify |
| EXT-064 | mikeyobrien/ralph-orchestrator | ralph orchestrator | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | status loop pattern |
| EXT-065 | ZSeven-W/openpencil | design/writing assistant | intake-required | low | low | wagents/ + planning/ + docs/ | intake-review | verify |
| EXT-066 | junhoyeo/tokscale | token scaling/telemetry | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | token/cost telemetry pattern |
| EXT-067 | RAIT-09/obsidian-agent-client | Obsidian agent client | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | Obsidian integration pattern |
| EXT-068 | safishamsi/graphify | knowledge graph skill | adopt-candidates | high | low | skills/ | review-required | high-priority graph/context skill; uv tool install; multi-harness hooks |
| EXT-069 | VoltAgent/awesome-agent-skills | awesome skill list | reference-only | high | low | skills/ | intake-review | high-volume skill discovery source |
| EXT-070 | nexu-io/open-design | local-first design skill suite | adapt | high | low | skills/ | review-required | design systems, sandboxed preview, CLI auto-detection, artifact UX |
| EXT-071 | Orchestra-Research/AI-Research-SKILLs | research skill suite | adapt | high | low | skills/ | review-required | research/engineering skill pack candidates |
| EXT-072 | refly-ai/refly | skill builder/platform | adapt | high | low | skills/ | review-required | skill builder UX and workflow packaging |
| EXT-073 | google/skills | official Google skill pack | adopt-candidates | high | low | skills/ | review-required | official skill candidates for Google technologies |
| EXT-074 | antfu/skills | curated personal skill pack | reference-only | high | low | skills/ | intake-review | quality inspiration from expert-maintained skills |
| EXT-075 | antvis/mcp-server-chart | chart MCP+skills | wrap | high | medium | skills/ | review-required | chart generation; prefer skill CLI if static, MCP if live rendering/server needed |
| EXT-076 | tech-leads-club/agent-skills | validated skill registry | adapt | high | low | skills/ | review-required | secure registry and validation model |
| EXT-077 | iOfficeAI/OfficeCLI | office document CLI | adopt-candidates | high | low | skills/ | review-required | strong CLI-first skill wrapper for Word/Excel/PPTX |
| EXT-078 | microsoft/skills | official Microsoft skills/MCP/agents | adopt-candidates | high | medium | skills/ | review-required | official SDK/product grounding skills |
| EXT-079 | jeremylongshore/claude-code-plugins-plus-skills | large Claude marketplace | reference-only | low | low | wagents/ + planning/ + docs/ | intake-review | marketplace/catalog UX and intake scale |
| EXT-080 | supabase/agent-skills | official Supabase skills | adopt-candidates | high | low | skills/ | review-required | official skill pack; npx skills install; references model |
| EXT-081 | bergside/design-md-chrome | design extraction browser extension | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | DESIGN.md generation, browser extension intake |
| EXT-082 | himself65/finance-skills | finance skill pack | reference-only | high | low | skills/ | intake-review | domain skill packaging; high-risk finance caveats |
| EXT-083 | cloudflare/skills | official Cloudflare skills | adopt-candidates | high | low | skills/ | review-required | official Cloudflare skill pack |
| EXT-084 | SnailSploit/Claude-Red | offensive security skills | quarantine | high | low | skills/ | quarantine-required | red-team only; must not install by default |
| EXT-085 | OpenCoworkAI/open-cowork | desktop app/control plane | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | one-click install, sandbox isolation, skill/MCP UX |
| EXT-086 | conorluddy/ios-simulator-skill | iOS simulator skill | adapt | high | low | skills/ | review-required | domain skill with xcodebuild wrapper |
| EXT-087 | imxv/Pretty-mermaid-skills | Mermaid rendering skill | adopt-candidates | high | low | skills/ | review-required | docs/diagram output skill; CLI/SVG/ASCII |
| EXT-088 | agentscope-ai/OpenJudge | evaluation framework | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | eval/reward/benchmark lane |
| EXT-089 | skillmatic-ai/awesome-agent-skills | awesome skill list | reference-only | high | low | skills/ | intake-review | skill discovery source |
| EXT-090 | enulus/OpenPackage | universal package manager | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | package manager/organizer model |
| EXT-091 | millionco/react-doctor | React diagnostic tool | adapt | medium | low | wagents/ + planning/ + docs/ | review-required | frontend skill/tool candidate |
| EXT-092 | uditgoenka/autoresearch | autoresearch skill | adapt | high | low | skills/ | review-required | research iteration workflow candidate |
| EXT-093 | meodai/skill.color-expert | color design skill | adopt-candidates | high | low | skills/ | review-required | design/color skill candidate |


## High-Leverage Integration Themes

1. **Knowledge-graph/context layer**: `graphify`, `codebase-memory-mcp`, `code-review-graph`, `soulforge`, `OpenContext`, and `context-mode` point to a repo-native context graph lane. Prefer a skill-generated graph plus optional live MCP query server.
2. **Session replay/observability**: `claude-replay`, `codeg`, `agentlytics`, `claude-code-history-viewer`, `opensessions`, and `tokscale` point to session history, replay, token/cost telemetry, and run graph visualization.
3. **Multi-agent control planes**: `claude_agent_teams_ui`, `agtx`, `ccmanager`, `cmux`, `open-cowork`, `happier`, and related UIs point to dashboard/kanban/control-plane directions for `wagents`.
4. **Skill registries and packages**: `google/skills`, `microsoft/skills`, `cloudflare/skills`, `supabase/agent-skills`, `tech-leads-club/agent-skills`, `awesome-agent-skills`, `awesome-llm-skills`, `open-skills`, and `OpenPackage` provide registry, validation, marketplace, and curation patterns.
5. **OpenCode ecosystem**: `ocx`, `opencode-worktree`, `opencode-pty`, `opencode-studio`, `opencode-skillful`, `opencode-swarm`, `opencode-bar`, and `opencode-mystatus` justify a dedicated OpenCode adapter lane.
6. **Design/UI skills**: `open-design`, `design-md-chrome`, `Pretty-mermaid-skills`, `skill.color-expert`, and `mcp-server-chart` should feed docs, visualization, design, and diagram-generation skills.
7. **Security-sensitive lanes**: auth/proxy/offensive projects (`codex-lb`, `meridian`, `opencode-claude-auth`, `Claude-Red`) must remain reference-only/quarantined until explicit threat modeling and policy approval.

## Required Promotion Checklist

Every repo promoted beyond reference-only must produce: pinned revision, license compatibility finding, maintainer/activity assessment, supply-chain finding, CLI/MCP conformance fixture, security review, rollback plan, OpenSpec task mapping, and docs/AI-instruction sync plan.
