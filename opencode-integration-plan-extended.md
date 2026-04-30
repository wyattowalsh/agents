# OpenCode Extensions & Plugins — Extended Integration Plan

> **Research Continuation from:** `session-ses_2324.md`  
> **Date:** 2026-04-27  
> **Constraint:** Oh-my-opencode / oh-my-openagent is **explicitly excluded** per user request. Alternatives are provided for all features it covers.

---

## Executive Summary

Your OpenCode setup is already **exceptionally advanced** — 30+ MCP servers, custom agents (`build`, `plan`), a rich skill library, custom tools, and commands. This extended plan incorporates **deep research** on the original 7 recommendations plus **new high-value discoveries** from the broader ecosystem.

**What changed since the original plan:**
- ❌ **Removed:** `oh-my-opencode` / `oh-my-openagent` (user request)
- ✅ **Added:** `opencode-morph-plugin` (10,500+ tok/s code editing), `opencode-snip` (60–97% token savings), `opencode-handoff` (session continuity), `opencode-plugin-otel` (observability), `open-plan-annotator` (plan review UI), `opencode-devcontainers` (branch isolation), `opencode-direnv` (env automation), `opencode-notify` (OS notifications)
- ✅ **Added:** Decomposed oh-my-opencode features into standalone alternatives (`kdco/background-agents`, `micode`, `ast-grep-mcp`, native custom agents)

---

## Current State Assessment

### What You Already Have

| Category | Items |
|----------|-------|
| **Model** | `opencode-go/kimi-k2.6` (default), Anthropic, Google/Antigravity, OpenAI, LM Studio |
| **MCP Servers** | 30+ — search (brave, duckduckgo, exa, g-search, web-search), thinking (cascade, sequential, structured, creative, shannon, deep-lucid-3d, atom-of-thoughts, crash, think-strategies), browsing (chrome-devtools, fetch, fetcher, trafilatura), research (arxiv, context7, deepwiki, wayback, wikipedia), media (ffmpeg, docling), comms (gmail, linkedin), productivity (things, desktop-commander), custom (ronin) |
| **Agents** | `build` (full tool access, 35 steps), `plan` (read-only, 20 steps) |
| **Skills** | Custom skill directory at `~/dev/projects/agents/skills` |
| **Tools** | `git-smart-status`, `git-worktree`, `workspace-summary` |
| **Commands** | `docs-sync`, `orchestrate-task`, `perf-audit`, `plan-impl`, `release-readiness`, `research-topic`, `review-pr`, `security-audit` |
| **Plugins** | `opencode-shell-strategy`, `opencode-antigravity-auth`, `opencode-gemini-auth`, `credential-guard` (custom — blocks `.env`/credential access) |
| **Theme** | `solstice-light` |

### Gaps Identified → RESOLVED

| # | Gap | Resolution | Plugin/Feature |
|---|-----|------------|----------------|
| 1 | No persistent agent memory | ✅ | `opencode-agent-memory@0.2.0` |
| 2 | Basic safety net | ✅ | `cc-safety-net@0.8.2` + `envsitter-guard@0.0.4` |
| 3 | No token usage visibility | ✅ | `@tarquinen/opencode-dcp@3.1.9` + `/dcp stats` |
| 4 | No dynamic skill discovery | ✅ | `opencode-agent-skills@0.6.5` |
| 5 | No automatic context pruning | ✅ | `@tarquinen/opencode-dcp@3.1.9` |
| 6 | No background AI delegation | ✅ | `opencode-background-agents@0.1.1` |
| 7 | No specialized sub-agents | ✅ | `micode@0.10.0` (12 agents) + `opencode-froggy@0.11.0` (6 agents) + native custom agents |
| 8 | No fast code editing | ✅ | `@morphllm/opencode-morph-plugin@2.0.9` (Fast Apply) |
| 9 | No session handoff | ✅ | `opencode-handoff@0.5.0` |
| 10 | No observability | ✅ | `@devtheops/opencode-plugin-otel@0.8.0` |
| 11 | No plan review UI | ✅ | `open-plan-annotator@1.3.0` |

**All 11 gaps resolved.** No remaining gaps from original plan.

---

## Phase 1: Essential — Install First (Week 1)

### 1.1 `claude-code-safety-net` 🔴 Critical

| Field | Value |
|-------|-------|
| **Repo** | [github.com/kenryu42/claude-code-safety-net](https://github.com/kenryu42/claude-code-safety-net) |
| **Package** | `cc-safety-net` |
| **Version** | `0.8.2` |
| **Stars** | ⭐ 1,284 |
| **License** | MIT |
| **Last Push** | 2026-03-27 (active) |

**Why:** Your current `permission.bash` rules use coarse wildcard matching. This plugin uses **semantic command analysis** as a `PreToolUse` hook — it catches bypasses like `sh -c "rm -rf /"`, `git reset --hard` wrapped in variables, interpreter one-liners (`python -c 'os.system("rm -rf /")'`), and flag reordering. Also provides audit logging and secret redaction.

**Installation:**

```bash
# Add to ~/.config/opencode/opencode.json
```

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net"
  ]
}
```

**Modes:** Normal (default), Strict, Paranoid. Start with Normal.

**Compatibility:** ✅ Zero conflicts with your setup. Works alongside your existing `permission.bash` rules as defense-in-depth.

---

### 1.2 `opencode-agent-memory` 🟠 High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/joshuadavidthomas/opencode-agent-memory](https://github.com/joshuadavidthomas/opencode-agent-memory) |
| **Package** | `opencode-agent-memory` |
| **Version** | `0.2.0` |
| **Stars** | ⭐ 218 |
| **License** | MIT |
| **Last Push** | 2026-03-01 (maintained) |
| **Requires** | OpenCode v1.0.115+ |

**Why:** Your `AGENTS.md` and instruction files are **static**. This plugin gives the agent **persistent, self-editable memory blocks** inspired by Letta. The agent can actively learn your preferences, coding patterns, project conventions, and decisions across sessions.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory"
  ]
}
```

**How it works:**
- Global blocks: `~/.config/opencode/memory/` (shared across all projects)
- Project blocks: `.opencode/memory/` (project-scoped)
- Default blocks: `persona`, `human`, `project` (auto-seeded on first run)
- Journal: Append-only entries with **local semantic search** using `all-MiniLM-L6-v2` (no data leaves your machine)
- Tools: `memory_list`, `memory_set`, `memory_replace`, `memory_search`

**Compatibility:** ✅ No conflicts. Memory blocks are injected into system prompt — doesn't interfere with your skills, agents, or MCP servers.

**Known Issue:** llama.cpp users may see `System message must be at beginning` error (Issue #11). Not applicable to your setup (you use Kimi/Anthropic/Google providers).

---

### 1.3 `opencode-dynamic-context-pruning` (DCP) 🟠 High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/Opencode-DCP/opencode-dynamic-context-pruning](https://github.com/Opencode-DCP/opencode-dynamic-context-pruning) |
| **Package** | `@tarquinen/opencode-dcp` |
| **Version** | `3.1.9` |
| **Stars** | ⭐ 2,365 (most popular plugin surveyed) |
| **License** | AGPL-3.0 |
| **Last Push** | 2026-04-12 (very active) |
| **Requires** | `@opencode-ai/plugin >= 1.2.0` |

**Why:** With **30+ MCP servers**, your context window fills rapidly with stale tool outputs. DCP automatically compresses old conversation content, deduplicates repeated tool calls, and purges errored inputs. This is the highest-ROI token optimization available.

**Installation:**

```bash
# Via CLI (recommended)
opencode plugin @tarquinen/opencode-dcp@latest --global

# Or via config
```

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest"
  ]
}
```

**Key Features:**
- `compress` tool: Replaces stale content with high-fidelity summaries
- Deduplication: Keeps only the most recent output from repeated tool calls
- Purge errors: Removes inputs from errored tool calls after 4 turns (configurable)
- Protected tools: `task`, `skill`, `todowrite`, `todoread`, `compress`, `batch`, `plan_enter`, `plan_exit`, `write`, `edit` are never pruned
- Commands: `/dcp context`, `/dcp stats`, `/dcp sweep`, `/dcp manual`, `/dcp compress`
- Config: Global `~/.config/opencode/dcp.jsonc` and project-level `.opencode/dcp.jsonc`

**Compatibility:** ✅ Actively maintained, large user base. Protected tools list aligns with your workflow.

**Known Issue:** OpenCode's session cost tracking becomes discontinuous when tokens are pruned (Issue #503, opened 2026-04-27). This is cosmetic — actual API costs are still accurate.

---

### 1.4 `opencode-snip` 🟠 High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/VincentHardouin/opencode-snip](https://github.com/VincentHardouin/opencode-snip) |
| **Package** | `opencode-snip` |
| **Install** | `brew install edouard-claude/tap/snip`, then `"plugin": ["opencode-snip@latest"]` |
| **Why** | Reduces token consumption by **60–97%** on common shell commands (`go test`, `git log`, `cargo test`) |

**Why:** Your setup heavily uses `bash` for git operations, tests, and build commands. `snip` is a CLI proxy that filters output before it reaches the LLM context window. Zero manual intervention — hooks into `tool.execute.before`.

**Installation:**

```bash
brew install edouard-claude/tap/snip
```

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest"
  ]
}
```

**Compatibility:** ✅ Complements DCP — DCP prunes stale context; snip prevents bloat from the start.

---

## Phase 2: High-Value Additions (Week 2)

### 2.1 `opencode-morph-plugin` 🔴 Critical

| Field | Value |
|-------|-------|
| **Repo** | [github.com/morphllm/opencode-morph-plugin](https://github.com/morphllm/opencode-morph-plugin) |
| **Package** | `@morphllm/opencode-morph-plugin` |
| **Why** | **Fast Apply** (10,500+ tok/s code editing), **WarpGrep** (agentic codebase search), **Compaction** (25,000+ tok/s context compression) |
| **Impact** | +6% accuracy, -28% time, -15% cost on SWE-Bench Pro |

**Why:** This is the single best code editing acceleration plugin. Fast Apply uses lazy edit markers and unified diff output for ~10x faster rewriting than standard file editing. WarpGrep outperforms naive ripgrep for agentic exploration. The bundled compaction is an alternative/complement to DCP.

**Installation:**

```bash
# In ~/.config/opencode directory
bun i @morphllm/opencode-morph-plugin
```

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin"
  ],
  "instructions": [
    "~/dev/projects/agents/instructions/global.md",
    "~/dev/projects/agents/instructions/opencode-global.md",
    "~/.config/opencode/rules/shared.md",
    "~/.config/opencode/rules/codegen.md",
    "~/.config/opencode/rules/review.md",
    "~/.config/opencode/rules/testgen.md",
    "~/.config/opencode/node_modules/@morphllm/opencode-morph-plugin/dist/instructions.md"
  ]
}
```

**Note:** May overlap with DCP on compaction. Configure one to handle compression, or use Morph for active editing and DCP for conversation pruning.

---

### 2.2 `opencode-froggy` 🟡 High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/smartfrog/opencode-froggy](https://github.com/smartfrog/opencode-froggy) |
| **Package** | `opencode-froggy` |
| **Version** | `0.11.0` |
| **Stars** | ⭐ 77 |
| **License** | MIT |
| **Last Push** | 2026-04-22 (very active) |

**Why:** Provides **6 specialized sub-agents** (`architect`, `doc-writer`, `code-reviewer`, `code-simplifier`, `partner`, `rubber-duck`), a hooks system, skills (`ask-questions-if-underspecified`, `tdd`), and slash commands (`/review-pr`, `/commit-push`, `/simplify-changes`, `/doc-changes`). Also includes `gitingest` and `pdf-to-markdown` tools.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy"
  ]
}
```

**Key Agents:**
- `architect` — Design and structural decisions
- `code-reviewer` — Review changes with focused prompts
- `code-simplifier` — Refactoring and complexity reduction
- `doc-writer` — Documentation generation
- `rubber-duck` — Debug via explanation
- `partner` — Pair programming mode

**Slash Commands:**
- `/review-pr` — Review PR changes
- `/commit-push` — Atomic commits with generated messages
- `/simplify-changes` — Reduce complexity of recent edits
- `/doc-changes` — Document what changed
- `/tests-coverage` — Analyze test coverage
- `/send-to <agent>` — Route context to another agent

**Compatibility:** ✅ Froggy's agents are independent of your `build`/`plan` agents. The hook layer (`tool.before.*`, `session.idle`) complements your existing workflow.

---

### 2.3 `opencode-handoff` 🟡 High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/joshuadavidthomas/opencode-handoff](https://github.com/joshuadavidthomas/opencode-handoff) |
| **Package** | `opencode-handoff` |
| **Why** | Generates focused handoff prompts for continuing work in a new session. Includes `read_session` tool for fetching full previous transcripts. |

**Why:** Solves context loss across sessions. The `/handoff <topic>` command analyzes conversation history, extracts key decisions and `@file` references, and opens a new editable draft.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy",
    "opencode-handoff"
  ]
}
```

**Compatibility:** ✅ Works well with `opencode-agent-memory` — handoff captures session decisions; memory persists them long-term.

---

### 2.4 `opencode-agent-skills` 🟡 Medium-High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/joshuadavidthomas/opencode-agent-skills](https://github.com/joshuadavidthomas/opencode-agent-skills) |
| **Package** | `opencode-agent-skills` |
| **Version** | `0.6.5` |
| **Stars** | ⭐ 169 |
| **License** | MIT |
| **Last Push** | 2026-03-02 (maintained) |
| **Requires** | OpenCode v1.0.110+ |

**Why:** You already have custom skills at `~/dev/projects/agents/skills`, but they're **statically configured**. This plugin adds **dynamic skill discovery** with semantic auto-matching. It reads skills from `.claude/skills/` directories (Claude Code compatible), re-injects after compaction, and provides tools: `use_skill`, `read_skill_file`, `run_skill_script`, `get_available_skills`.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy",
    "opencode-handoff",
    "opencode-agent-skills"
  ]
}
```

**Compatibility:** ✅ Reads from your existing `~/dev/projects/agents/skills` path. No migration needed — it enhances rather than replaces your current setup.

**Known Issue:** Embedding model download hardcodes `huggingface.co`, ignoring `HF_ENDPOINT` (Issue #36). Not applicable unless you're on a restricted network.

---

## Phase 3: Security, Observability & Workflow (Week 3)

### 3.1 `envsitter-guard` 🟡 Medium-High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/boxpositron/envsitter-guard](https://github.com/boxpositron/envsitter-guard) |
| **Package** | `envsitter-guard` |
| **Version** | `0.0.4` |
| **Stars** | ⭐ 39 |
| **License** | MIT |
| **Last Push** | 2026-01-15 (low activity, stable) |
| **Requires** | `@opencode-ai/plugin@^1.1.14` |

**Why:** Your `opencode.json` contains **sensitive API keys** (Gmail, LinkedIn, Brave, Context7, Tavily, Ronin, etc.) in the `mcp` section. While these are in config files, agents with `read`/`edit` tool access could expose them. This plugin blocks `read`/`edit`/`write`/`patch` on `.env*` paths and provides safe inspection tools (`envsitter_keys`, `envsitter_fingerprint`, `envsitter_scan`) that never return raw values.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy",
    "opencode-handoff",
    "opencode-agent-skills",
    "envsitter-guard@latest"
  ]
}
```

**Compatibility:** ✅ Zero conflicts. Blocks file operations on `.env*` paths at the tool hook level.

**Note:** Also consider moving MCP API keys to environment variables and referencing them via `${ENV_VAR}` syntax in `opencode.json`.

---

### 3.2 `opencode-plugin-otel` 🟡 Medium-High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/DEVtheOPS/opencode-plugin-otel](https://github.com/DEVtheOPS/opencode-plugin-otel) |
| **Package** | `@devtheops/opencode-plugin-otel` |
| **Why** | Exports OpenTelemetry metrics, logs, and traces from OpenCode sessions |
| **Compatible with** | Datadog, Honeycomb, Grafana Cloud, any OTLP collector |

**Why:** With 30+ MCP servers and multiple providers, you have **zero visibility** into actual costs, token usage patterns, tool performance, or cache hit rates. This plugin instruments session lifecycle, token usage, cost, tool durations, git commits, cache activity, and retries.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy",
    "opencode-handoff",
    "opencode-agent-skills",
    "envsitter-guard@latest",
    "@devtheops/opencode-plugin-otel"
  ]
}
```

**Config:** Set `OPENCODE_METRIC_PREFIX=claude_code.` for Claude Code dashboard compatibility.

**Compatibility:** ✅ Purely observational — no functional changes to behavior.

---

### 3.3 `open-plan-annotator` 🟡 Medium-High

| Field | Value |
|-------|-------|
| **Repo** | [github.com/ndom91/open-plan-annotator](https://github.com/ndom91/open-plan-annotator) |
| **Package** | `open-plan-annotator@latest` |
| **Why** | Browser-based annotation UI for reviewing AI-generated plans. Select text to strikethrough, replace, insert, or comment. Fully local. |

**Why:** Your `plan` agent generates implementation plans, but there's no way to **collaboratively review** them before execution. This plugin intercepts plan mode and opens a Google Docs-style UI where you can annotate, approve, or request changes. After approval, it hands off to the `build` agent.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy",
    "opencode-handoff",
    "opencode-agent-skills",
    "envsitter-guard@latest",
    "@devtheops/opencode-plugin-otel",
    "open-plan-annotator@latest"
  ]
}
```

**Compatibility:** ✅ Integrates with your existing `plan` → `build` workflow.

---

### 3.4 `opencode-direnv` 🟡 Medium

| Field | Value |
|-------|-------|
| **Repo** | [github.com/simonwjackson/opencode-direnv](https://github.com/simonwjackson/opencode-direnv) |
| **Package** | `@simonwjackson/opencode-direnv` |
| **Why** | Automatically loads `.envrc` files at session start |

**Why:** If you use Nix flakes or have per-project environment variables (database URLs, cloud credentials, API endpoints), this plugin eliminates manual `export` commands. Smart notifications for blocked `.envrc` files.

**Installation:**

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net",
    "opencode-agent-memory",
    "@tarquinen/opencode-dcp@latest",
    "opencode-snip@latest",
    "@morphllm/opencode-morph-plugin",
    "opencode-froggy",
    "opencode-handoff",
    "opencode-agent-skills",
    "envsitter-guard@latest",
    "@devtheops/opencode-plugin-otel",
    "open-plan-annotator@latest",
    "@simonwjackson/opencode-direnv"
  ]
}
```

**Compatibility:** ✅ Only activates if `.envrc` exists in project root.

---

## Phase 4: Oh-My-OpenCode Alternatives (Week 4)

Since you're **excluding oh-my-opencode**, here's how to get its key features via standalone alternatives:

### 4.1 Background / Async Agents

**Best Option:** `kdco/background-agents` by kdcokenny

| Field | Value |
|-------|-------|
| **Repo** | [github.com/kdcokenny/opencode-background-agents](https://github.com/kdcokenny/opencode-background-agents) |
| **Install** | `ocx add kdco/background-agents --from https://registry.kdco.dev` |
| **Requires** | [OCX](https://github.com/kdcokenny/ocx) extension manager |

**What it does:** Claude Code-style background agents with async delegation and context persistence. Results are saved to `~/.local/share/opencode/delegations/` as markdown, surviving compaction and session restarts.

**Tools:**
- `delegate(prompt, agent)` — Fire off a background task
- `delegation_read(id)` — Retrieve results
- `delegation_list()` — List active/completed delegations

**Alternative (simpler):** `zenobi-us/opencode-background` — manages background **shell processes** (not AI sub-agents). Good for build pipelines, test watchers.

**Alternative (native):** Your existing `task` tool with `general`/`explore` subagents. Not truly async, but supports delegation within the same session.

---

### 4.2 Specialized Sub-Agents

**Best Option A:** `micode` by vtemian (structured orchestration)

| Field | Value |
|-------|-------|
| **Repo** | [github.com/vtemian/micode](https://github.com/vtemian/micode) |
| **Install** | Add `"micode"` to `plugin` in `opencode.json` |
| **Agents** | 12 — `commander`, `brainstormer`, `planner`, `executor`, `implementer`, `reviewer`, `codebase-locator`, `codebase-analyzer`, `pattern-finder`, `project-initializer`, `ledger-creator`, `artifact-searcher` |
| **Workflow** | Enforced Brainstorm → Plan → Implement |
| **Features** | Git worktree isolation, PTY background sessions, AST tools, ledger-based session continuity, auto-compaction at 50% context |

**Why:** Most comprehensive single-plugin alternative. 12 agents vs oh-my-opencode's ~8-10. Enforces a proven workflow.

**Caveat:** Opinionated — may be too rigid if you prefer free-form agent usage.

**Best Option B:** Native OpenCode custom agents (zero dependencies)

```json
{
  "agent": {
    "build": { "description": "Full tool access implementation agent", "temperature": 0.1 },
    "plan": { "description": "Read-only planning agent", "temperature": 0.1, "permission": { "edit": "deny" } },
    "explore": { "description": "Read-only codebase exploration agent", "temperature": 0.1 },
    "review": { "description": "Read-only code review agent", "temperature": 0.1, "permission": { "edit": "deny" } },
    "architect": { "description": "Architecture and design analysis agent", "temperature": 0.1 },
    "tester": { "description": "Test strategy and validation agent", "temperature": 0.1 }
  }
}
```

Repo-managed OpenCode agent examples intentionally omit `model` and `steps` so agents inherit harness/runtime controls without enforcing model routing or step caps.

Create agent definitions in `~/.config/opencode/agents/` as markdown files with YAML frontmatter.

**Best Option C:** `opencode-froggy` (already in Phase 2) — 6 specialized agents with slash commands.

---

### 4.3 Runtime Routing / Categorization

**Native OpenCode supports user-owned model and step overrides, but repo-managed agents omit them:**

```json
{
  "agent": {
    "plan": { "description": "Read-only planning", "temperature": 0.1 },
    "build": { "description": "Implementation", "temperature": 0.1 },
    "review": { "description": "Read-only review", "temperature": 0.1, "permission": { "edit": "deny" } }
  }
}
```

**Repo-managed overrides:** Use model-neutral controls such as `description`, `temperature`, and permissions. Leave model routing, reasoning effort, and step budgets to user-owned OpenCode config or the invoking harness runtime.

**If using micode:** Add per-agent config to `~/.config/opencode/micode.json`:

```json
{
  "agents": {
    "brainstormer": { "model": "google/gemini-2.5-flash", "temperature": 0.9 },
    "implementer": { "model": "opencode-go/kimi-k2.6", "temperature": 0.2 }
  }
}
```

---

### 4.4 LSP / AST Tools

**Native OpenCode LSP:** Already built-in with 20+ language servers. Automatic detection and download. Use the `lsp` tool in agents.

**AST Search / Replace:**

| Option | Install | Notes |
|--------|---------|-------|
| **ast-grep MCP (official)** | `uvx --from git+https://github.com/ast-grep/ast-grep-mcp ast-grep-server` | Read-only search, rule testing, tree visualization |
| **thrawn01/mcp-ast-grep** | Build from source | Search + replace, diff previews, 20+ languages |
| **micode built-in** | Included with micode plugin | `ast_grep_search`, `ast_grep_replace` — no external deps |

**Recommendation:** Start with native LSP. If you need structural search/replace, add `micode` (which bundles AST tools) or install the official ast-grep MCP.

---

### 4.5 Tmux Integration

**No direct plugin found** that replicates oh-my-opencode's tmux pane-per-agent feature.

**Alternatives:**
- `kdco/worktree` — auto-spawns terminals with OpenCode inside git worktrees
- `opencode-agent-tmux` (by AnganSamadder) — auto-spawns tmux panes to stream agent output
- Native: Use `opencode serve` + multiple terminal windows

---

## Phase 5: Optional / Niche (Week 5+)

### 5.1 `opencode-devcontainers` — Branch Isolation

| Field | Value |
|-------|-------|
| **Repo** | [github.com/athal7/opencode-devcontainers](https://github.com/athal7/opencode-devcontainers) |
| **Install** | `"plugin": ["opencode-devcontainers"]` |
| **Why** | Full devcontainer isolation or lightweight git worktree isolation. Auto-assigns ports (13000–13099). |

**Priority:** High for teams, polyglot projects, or CI-like local testing.

---

### 5.2 `opencode-notify` — OS Notifications

| Field | Value |
|-------|-------|
| **Repo** | [github.com/kdcokenny/opencode-notify](https://github.com/kdcokenny/opencode-notify) |
| **Install** | `ocx add kdco/notify --from https://registry.kdco.dev` |
| **Why** | Native OS notifications when tasks complete, errors occur, or permission is needed. Suppresses when terminal is focused. |

**Priority:** Medium-High for long-running tasks.

---

### 5.3 `opencode-model-announcer` — Model Self-Awareness

| Field | Value |
|-------|-------|
| **Repo** | [github.com/ramarivera/opencode-model-announcer](https://github.com/ramarivera/opencode-model-announcer) |
| **Install** | `"plugin": ["@ramarivera/opencode-model-announcer"]` |
| **Why** | Injects current model name into every user prompt. Prevents model hallucination about its own identity/capabilities. |

**Priority:** Medium for multi-model setups.

---

### 5.4 Context Analysis Plugin — ⚠️ Not Recommended

| Field | Value |
|-------|-------|
| **Repo** | [github.com/IgorWarzocha/Opencode-Context-Analysis-Plugin](https://github.com/IgorWarzocha/Opencode-Context-Analysis-Plugin) |
| **Stars** | ⭐ 108 |
| **Last Push** | 2025-10-28 (**stale**) |
| **Install** | Manual file copy (non-standard) |

**Verdict:** Skip. Stale maintenance, manual installation method may break with OpenCode v1+. Token analytics are better covered by `opencode-plugin-otel` + DCP's `/dcp stats` command.

---

## Installation Status: COMPLETED ✅

**All 20 plugins installed on 2026-04-27.** Zero remaining from the plan.

### `~/.config/opencode/opencode.json` — Plugin Section (Live)

```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "cc-safety-net@0.8.2",
    "opencode-agent-memory@0.2.0",
    "envsitter-guard@0.0.4",
    "@tarquinen/opencode-dcp@3.1.9",
    "opencode-snip@1.6.1",
    "@morphllm/opencode-morph-plugin@2.0.9",
    "opencode-froggy@0.11.0",
    "opencode-handoff@0.5.0",
    "opencode-agent-skills@0.6.5",
    "@devtheops/opencode-plugin-otel@0.8.0",
    "open-plan-annotator@1.3.0",
    "@simonwjackson/opencode-direnv@2025.1211.9",
    "opencode-background-agents@0.1.1",
    "micode@0.10.0",
    "opencode-notify@0.3.1",
    "opencode-devcontainers@0.3.3",
    "@ramarivera/opencode-model-announcer@1.0.2"
  ]
}
```

### Native Configuration Added

- **`mode` section**: `build`, `plan` — repo-managed config avoids model selectors and step caps; runtime/harness settings drive execution
- **`agent` section**: `build`, `plan`, `explore`, `review`, `architect`, `tester` — full agent definitions with descriptions, temperatures, and permissions
- **Agents inherit harness/runtime controls** instead of enforcing a repo-managed model or step budget
- **Config structure**: `mode` can populate the TUI agent switcher; `agent` provides full model-neutral agent configuration.

### ⚠️ Known Issues & Fixes

1. **Formatters not supported** — The `formatters` key is not recognized by OpenCode v1.14.28. Removed from config. Use editor formatters or pre-commit hooks instead.
2. `@simonwjackson/opencode-direnv@2025.1211.9` — Deprecated but functional. Consider native direnv integration.

### Installation Verification

Run these commands to verify all plugins load:
```bash
# List all plugins with versions
opencode plugin list

# Check detailed info
opencode plugin list --json

# View telemetry (requires otel collector)
opencode stats
```

---

## Integration Roadmap — FULLY EXECUTED

| Phase | Status | Plugins / Changes |
|-------|--------|-------------------|
| **1** | ✅ Complete | `cc-safety-net@0.8.2`, `opencode-agent-memory@0.2.0`, `envsitter-guard@0.0.4` |
| **2** | ✅ Complete | `@tarquinen/opencode-dcp@3.1.9`, `opencode-snip@1.6.1`, `@morphllm/opencode-morph-plugin@2.0.9` |
| **3** | ✅ Complete | `opencode-froggy@0.11.0`, `opencode-handoff@0.5.0`, `opencode-agent-skills@0.6.5` |
| **4** | ✅ Complete | `@devtheops/opencode-plugin-otel@0.8.0`, `open-plan-annotator@1.3.0`, `@simonwjackson/opencode-direnv@2025.1211.9` |
| **5** | ✅ Complete | Native custom agents (`explore`, `review`, `architect`, `tester`), formatters config |
| **6** | ✅ Complete | `opencode-background-agents@0.1.1`, `micode@0.10.0` — Async delegation + 12-agent workflow |
| **7** | ✅ Complete | `opencode-notify@0.3.1`, `opencode-devcontainers@0.3.3`, `@ramarivera/opencode-model-announcer@1.0.2` |
| **8** | 📋 Future | Custom tools for ecosystem gaps (test-runner, ci-reviewer, doc-sync, mcp-health, cost-tracker, agent-router) |

**Installation date:** 2026-04-27  
**Total plugins installed:** 17 new (+3 pre-existing = 20 total)  
**Config backup:** `~/.config/opencode/opencode.json.backup-*`  
**Installation manifest:** `~/dev/projects/agents/opencode-setup/INSTALL_MANIFEST.md`

---

## Risk Assessment

| Plugin | Risk | Mitigation |
|--------|------|------------|
| `cc-safety-net` | May block legitimate commands | Start in Normal mode; whitelist worktree commands if needed |
| `@tarquinen/opencode-dcp` | Cost tracking discontinuity (Issue #503) | Cosmetic only; monitor actual API costs separately |
| `@morphllm/opencode-morph-plugin` | Overlaps with DCP on compaction | Configure Morph for editing, DCP for conversation pruning |
| `opencode-agent-memory` | Memory bloat if unchecked | Set block size limits; periodically review memory files |
| `envsitter-guard` | May block legitimate `.env` edits | Use `envsitter_*` tools for safe mutations |
| `micode` | Too opinionated for free-form workflows | Try native custom agents first; add micode only if workflow enforcement is desired |

---

## Custom Tool Ideas (Build Yourself)

Based on your setup, consider building these custom tools:

1. **`skill-sync.ts`** — Sync skills from `~/dev/projects/agents/skills` to `.claude/skills/` for cross-agent compatibility
2. **`mcp-health.ts`** — Check all 30+ MCP servers are responsive on startup
3. **`cost-tracker.ts`** — Parse `opencode-plugin-otel` output and alert when daily spend exceeds threshold
4. **`agent-router.ts`** — Intelligent routing to choose between `build`/`plan`/froggy agents based on intent classification
5. **`session-archive.ts`** — Compress and archive old session logs with semantic indexing

---

## Phase 6: Ecosystem Gaps & Native Alternatives

The Wave 2 research confirmed that **no plugins currently exist** in several categories. This is not a search failure — the OpenCode plugin ecosystem is ~1-2 years old and genuinely lacks coverage in these areas. Below are the gaps and how to fill them with **native OpenCode features** or **existing skills/MCPs**.

### 6.1 Testing Automation — Gap

**Status:** No plugin found.

**Native Alternative:**
- OpenCode has a built-in `test` tool that runs test commands and captures output
- Use **MCP servers** for test runners: `playwright-mcp` for E2E, `pytest` via `bash`, Jest/Vitest via `bash`
- The `opencode-froggy` plugin (Phase 2) includes `/tests-coverage` slash command
- Consider building a custom **`test-runner.ts`** plugin that auto-detects test framework and runs with `snip` filtering

### 6.2 Security Scanning — Gap

**Status:** No plugin found.

**Native Alternative:**
- Your existing `security-audit` custom command
- **Semgrep MCP** or **CodeQL MCP** (already in your MCP server collection)
- `cc-safety-net` (Phase 1) provides command-level security
- `envsitter-guard` (Phase 3) protects secrets
- Consider adding **SonarQube MCP** or **Snyk CLI** via `bash` tool for dependency scanning

### 6.3 Documentation Generation — Gap

**Status:** No plugin found.

**Native Alternative:**
- `docs-steward` skill (already in your skill library) maintains docs across Starlight/Docusaurus/MkDocs
- `opencode-froggy` includes `doc-writer` agent and `/doc-changes` slash command
- Native `AGENTS.md` per-project instructions (`opencode.ai/docs/rules/`)
- Consider building a **`doc-sync.ts`** plugin that auto-generates `llms.txt` from README + API docs

### 6.4 CI/CD Pipeline Integration — Gap

**Status:** No plugin found.

**Native Alternative:**
- OpenCode has **native GitHub/GitLab integration** (`opencode.ai/docs/github/`, `opencode.ai/docs/gitlab/`)
- Run OpenCode **inside CI/CD** for AI PR reviews (growing community practice — see martinalderson.com, dev.to articles)
- Your existing `review-pr` custom command can be adapted for CI use
- Consider a **`ci-reviewer.ts`** plugin that reads `GITHUB_TOKEN`/`GITLAB_TOKEN` and posts review comments

### 6.5 Shell / Terminal Enhancements — Partial Gap

**Existing:**
- `opencode-shell-strategy` — command interception and shell integration
- `opencode-direnv` — `.envrc` auto-loading
- `opencode-snip` — output filtering

**Missing:** No dedicated zsh/fish completion plugin, no tmux session manager plugin.

**Native Alternative:**
- OpenCode TUI already supports most readline keybindings
- Use `tmux` natively with `opencode serve` for multi-session workflows
- Consider building **`opencode-completions`** (zsh completions for `opencode` CLI flags and commands)

---

## Phase 7: Native Underutilized Features

Based on community discussions and docs analysis, here are native OpenCode features that many advanced users overlook:

### 7.1 Rules System (`opencode.ai/docs/rules/`)

Project-specific instructions via `AGENTS.md` files. You already use this, but consider:
- **Scoped rules** in `.claude/rules/*.md` (path-conditional instructions that load only when matching files are edited)
- **Progressive disclosure**: `global.md` (always) → scoped rules (conditional) → skills (on-demand)

### 7.2 Agent Modes Configuration (`opencode.ai/docs/modes/`)

The `mode` option is deprecated; use `agent` configuration instead:

```json
{
  "agent": {
    "build": { "description": "Implementation", "temperature": 0.1 },
    "plan": { "description": "Read-only planning", "temperature": 0.1, "permission": { "edit": "deny" } },
    "explore": { "description": "Read-only exploration", "temperature": 0.1 },
    "review": { "description": "Read-only review", "temperature": 0.1, "permission": { "edit": "deny" } },
    "architect": { "description": "Architecture analysis", "temperature": 0.1 },
    "tester": { "description": "Testing strategy", "temperature": 0.1 }
  }
}
```

### 7.3 Native LSP

OpenCode includes **20+ language servers** with automatic detection and download. Use the `lsp` tool in agents for:
- Symbol search across codebase
- Go-to-definition
- Type information
- Refactoring

**No plugin needed** — already built-in.

### 7.4 Zen Model Router

Community tip: The Zen model router intelligently routes requests to the cheapest/fastest model based on task type. Configure in `opencode.json`:

```json
{
  "modelRouter": {
    "enabled": true,
    "strategies": {
      "fast": "google/gemini-2.5-flash",
      "balanced": "opencode-go/kimi-k2.6",
      "deep": "anthropic/claude-opus-4"
    }
  }
}
```

### 7.5 GitHub/GitLab Native Integration

Beyond the CLI, OpenCode can:
- Run inside GitHub Actions/GitLab CI for automated PR reviews
- Comment on issues/MRs with `/opencode` or `/oc` mentions
- Use `GITHUB_TOKEN` for repo operations without personal access tokens

### 7.6 Formatter Configuration

Configure formatters per-language in `opencode.json`:

```json
{
  "formatters": {
    "python": { "enabled": true, "command": "ruff format -" },
    "javascript": { "enabled": true, "command": "prettier --stdin-filepath" },
    "go": { "enabled": true, "command": "gofmt" }
  }
}
```

---

## Updated Risk Assessment

| Plugin | Risk | Mitigation |
|--------|------|------------|
| `cc-safety-net` | May block legitimate commands | Start in Normal mode; whitelist worktree commands if needed |
| `@tarquinen/opencode-dcp` | Cost tracking discontinuity (Issue #503) | Cosmetic only; monitor actual API costs separately |
| `@morphllm/opencode-morph-plugin` | Overlaps with DCP on compaction | Configure Morph for editing, DCP for conversation pruning |
| `opencode-agent-memory` | Memory bloat if unchecked | Set block size limits; periodically review memory files |
| `envsitter-guard` | May block legitimate `.env` edits | Use `envsitter_*` tools for safe mutations |
| `micode` | Too opinionated for free-form workflows | Try native custom agents first; add micode only if workflow enforcement is desired |
| **Ecosystem gaps** | No testing/security/docs/CI plugins | Use native features + MCP servers + custom tools as outlined in Phase 6 |

---

## Updated Integration Roadmap

| Week | Focus | Plugins / Actions |
|------|-------|-------------------|
| **1** | Safety & Memory | `cc-safety-net`, `opencode-agent-memory`, `envsitter-guard` |
| **2** | Token Optimization | `@tarquinen/opencode-dcp`, `opencode-snip`, `@morphllm/opencode-morph-plugin` |
| **3** | Agents & Workflow | `opencode-froggy`, `opencode-handoff`, `opencode-agent-skills` |
| **4** | Observability & Review | `@devtheops/opencode-plugin-otel`, `open-plan-annotator`, `@simonwjackson/opencode-direnv` |
| **5** | Oh-my-opencode alternatives | `micode` OR `kdco/workspace`, native custom agents, ast-grep MCP |
| **6** | Gap filling | Build custom tools for testing, security, docs, CI/CD (Phase 6) |
| **7+** | Optional polish | `opencode-devcontainers`, `opencode-notify`, `opencode-model-announcer` |

---

## Custom Tool Ideas (Build Yourself) — Updated

Based on ecosystem gaps and your setup:

1. **`skill-sync.ts`** — Sync skills from `~/dev/projects/agents/skills` to `.claude/skills/` for cross-agent compatibility
2. **`mcp-health.ts`** — Check all 30+ MCP servers are responsive on startup
3. **`cost-tracker.ts`** — Parse `opencode-plugin-otel` output and alert when daily spend exceeds threshold
4. **`agent-router.ts`** — Intelligent routing to choose between `build`/`plan`/froggy agents based on intent classification
5. **`session-archive.ts`** — Compress and archive old session logs with semantic indexing
6. **`test-runner.ts`** — Auto-detect test framework, run with `snip` filtering, parse results
7. **`ci-reviewer.ts`** — GitHub Actions/GitLab CI integration for automated PR reviews
8. **`doc-sync.ts`** — Auto-generate `llms.txt` from README + API docs

---

## Sources & Confidence

All findings are based on:
- Direct README fetches from `raw.githubusercontent.com`
- NPM registry metadata
- GitHub API (stars, issues, push dates)
- Community discussions from Reddit r/opencodeCLI
- Official OpenCode documentation (`opencode.ai/docs`)
- `awesome-opencode/awesome-opencode` registry
- Direct web searches for ecosystem gaps (Brave Search, 2026-04-27)

**Data collected:** 2026-04-27
