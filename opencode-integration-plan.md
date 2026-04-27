# OpenCode Extensions & Plugins Integration Plan

## Executive Summary

Your OpenCode setup is already **exceptionally advanced** — you have 30+ MCP servers, custom agents, skills, tools, and commands. This plan identifies the **highest-value plugins and integrations** to add capabilities you're currently missing: async background agents, persistent memory, semantic safety nets, token analytics, and more.

---

## Current State Assessment

### What You Already Have (Impressive)
- **Providers**: Anthropic, Google/Antigravity, OpenAI, LM Studio (local)
- **MCP Servers**: 30+ including search (brave, duckduckgo, exa, g-search, web-search), thinking tools (cascade, sequential, structured, creative, shannon, deep-lucid-3d, atom-of-thoughts, crash, think-strategies), browsing (chrome-devtools, fetch, fetcher, trafilatura), research (arxiv, context7, deepwiki, wayback, wikipedia), media (ffmpeg, docling), communications (gmail, linkedin), productivity (things, desktop-commander), and custom (ronin)
- **Agents**: `build` (full tool access, 35 steps) and `plan` (read-only, 20 steps)
- **Skills**: Custom skill directory at `~/dev/projects/agents/skills`
- **Tools**: `git-smart-status`, `git-worktree`, `workspace-summary`
- **Commands**: `docs-sync`, `orchestrate-task`, `perf-audit`, `plan-impl`, `release-readiness`, `research-topic`, `review-pr`, `security-audit`
- **Plugins**: `opencode-shell-strategy`, `opencode-antigravity-auth`, `opencode-gemini-auth`
- **Theme**: `solstice-light`

### Gaps Identified
1. **No async background delegation** — Research tasks block your main session
2. **No persistent agent memory** — Context lost across sessions/compaction
3. **No token usage visibility** — Can't optimize context consumption
4. **Basic safety net** — Bash permissions are coarse; no semantic command analysis
5. **No dynamic skill discovery** — Skills are statically configured
6. **No .env leak protection** — Sensitive files could be exposed
7. **No specialized sub-agents** — Only `build` and `plan`; missing reviewer, architect, etc.
8. **No IDE extension** — Working purely in TUI; no VS Code/JetBrains integration

---

## Phase 1: High-Impact Plugins (Install First)

### 1.1 Oh My OpenAgent (formerly Oh My OpenCode)
**Priority**: 🔴 Critical
**Repository**: `code-yeongyu/oh-my-openagent` (npm: `oh-my-opencode`)
**What it does**: The most comprehensive OpenCode plugin — batteries-included agent harness with async subagents, 52 lifecycle hooks, 26 built-in tools, LSP/AST integration, curated MCPs, and Claude Code compatibility layer.

**Key Features**:
- **Background/Async Agents**: Run parallel workers for research, exploration, and prep work
- **Specialized Sub-Agents**: Explorer, Oracle, Librarian, Designer, Frontend Engineer, etc.
- **Category-Based Model Routing**: Use cheap models for exploration, expensive ones for implementation
- **IntentGate Classifier**: Automatically routes tasks to appropriate agents
- **Hashline Edit Tool**: Fast code editing with LINE#ID markers
- **3-Tier MCP System**: Built-in + `.mcp.json` + skill-embedded MCPs
- **Tmux Integration**: Live visibility into background agents

**Installation**:
```bash
# Add to opencode.json plugins array
# Or install via npm in OpenCode config directory
cd ~/.config/opencode
npm install oh-my-opencode
```

**Configuration**: Create `~/.config/opencode/oh-my-opencode.json`:
```jsonc
{
  "agents": {
    "explorer": {
      "model": "gemini-2.5-flash",
      "description": "Cheap parallel codebase exploration"
    },
    "oracle": {
      "model": "claude-opus-4",
      "description": "Deep architectural reasoning"
    }
  },
  "mcp": {
    "enabled": true,
    "curated": ["web-search", "github-search", "docs-context"]
  }
}
```

**Why you need it**: Your setup already has the infrastructure (MCPs, skills, agents). Oh My OpenAgent orchestrates them intelligently with background delegation and model routing, saving tokens and time.

---

### 1.2 Background Agents
**Priority**: 🔴 Critical (if not using Oh My OpenAgent)
**Repository**: `kdcokenny/opencode-background-agents`
**Alternative to**: Oh My OpenAgent's background feature (use this if OMO is too heavy)

**What it does**: Claude Code-style background agents with async delegation and context persistence. Results survive compaction.

**Tools Added**:
| Tool | Purpose |
|------|---------|
| `delegate(prompt, agent)` | Launch a background task |
| `delegation_read(id)` | Retrieve a specific result |
| `delegation_list()` | List all delegations |

**Installation**:
```bash
# Using OCX (recommended)
ocx add kdco/background-agents --from https://registry.kdco.dev

# Or manual
git clone https://github.com/kdcokenny/opencode-background-agents ~/.config/opencode/plugin/background-agents
```

**Why you need it**: Your `research-topic` command runs inline. With background agents, you can fire off research, continue coding, and retrieve results later. Your 30+ MCP servers make background research incredibly powerful.

---

### 1.3 Agent Memory
**Priority**: 🟠 High
**Repository**: `joshuadavidthomas/opencode-agent-memory`
**npm**: `opencode-agent-memory`

**What it does**: Letta-inspired persistent, self-editable memory blocks. The agent maintains its own memory across sessions.

**Features**:
- **Persistent Memory**: Survives sessions and compaction
- **Shared Across Sessions**: Global blocks + project-specific blocks
- **Self-Editing**: Agent reads/writes its own memory with dedicated tools
- **Journal**: Append-only entries with semantic search (local embeddings)
- **System Prompt Injection**: Memory always in context

**Default Blocks**:
| Block | Scope | Purpose |
|-------|-------|---------|
| `persona` | global | How the agent should behave |
| `human` | global | Your preferences, habits, constraints |
| `project` | project | Codebase-specific knowledge |

**Tools**:
| Tool | Description |
|------|-------------|
| `memory_list` | List available memory blocks |
| `memory_set` | Create or update a memory block |
| `memory_replace` | Replace substring within a block |
| `journal_write` | Write a journal entry |
| `journal_search` | Semantic search entries |
| `journal_read` | Read entry by ID |

**Installation**:
```json
// Add to ~/.config/opencode/opencode.json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "opencode-agent-memory"
  ]
}
```

**Why you need it**: Your `AGENTS.md` files are static. Agent Memory lets the AI dynamically learn and remember your preferences, coding patterns, and project conventions across sessions.

---

### 1.4 Claude Code Safety Net
**Priority**: 🟠 High
**Repository**: `kenryu42/claude-code-safety-net`

**What it does**: Catches destructive git and filesystem commands before execution using semantic analysis, not just pattern matching.

**Why it's better than bash permissions**:
| Feature | Bash Permissions | Safety Net |
|---------|-----------------|------------|
| Parsing | Wildcard patterns | Semantic command analysis |
| Execution Order | Runs second | Runs first (PreToolUse hook) |
| Shell Wrappers | Not handled | Recursively analyzed (5 levels) |
| Interpreter One-Liners | Not handled | Detected and blocked |
| Bypass Vectors | Many (flag reordering, variables) | Semantic understanding |

**Commands Blocked**:
- `rm -rf /`, `rm -rf ~`, `rm -rf /*`
- `git reset --hard`, `git checkout -- .`
- `git push --force`, `git push -f`
- `dd if=/dev/zero of=/dev/sda`
- `mkfs.*`, `format`
- `> /dev/sda`, `:(){ :|: & };:`

**Modes**:
- **Normal**: Blocks known destructive patterns
- **Strict**: Adds `git clean`, `git stash drop`, branch deletion
- **Paranoid**: Also blocks `git merge`, `git rebase`, `git cherry-pick`

**Installation**:
```bash
# Via npm
cd ~/.config/opencode
npm install claude-code-safety-net

# Or copy to plugin directory
git clone https://github.com/kenryu42/claude-code-safety-net ~/.config/opencode/plugin/claude-code-safety-net
```

**Configuration**: Add to `~/.config/opencode/opencode.json`:
```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "opencode-agent-memory",
    "claude-code-safety-net"
  ]
}
```

**Why you need it**: You currently have coarse bash permissions (`rm -rf *` denied, `sudo *` denied). Safety Net provides semantic analysis that catches bypasses like `sh -c "rm -rf /"` or `git reset --hard` wrapped in variables.

---

### 1.5 Context Analysis Plugin
**Priority**: 🟡 Medium-High
**Repository**: `IgorWarzocha/Opencode-Context-Analysis-Plugin`

**What it does**: Visual token usage breakdown for your OpenCode sessions. See exactly where tokens go.

**Commands**:
```bash
/context              # Standard analysis
/context detailed     # More detailed breakdown
/context short        # Quick summary
/context verbose      # Everything included
/context "focus on tools"  # Custom analysis
```

**Insights**:
- Which tools cost the most tokens
- System prompt impact
- Conversation patterns
- Reasoning costs (for supported models)

**Installation**:
```bash
git clone https://github.com/IgorWarzocha/Opencode-Context-Analysis-Plugin.git
cp -r Opencode-Context-Analysis-Plugin/.opencode ~/.config/opencode/
```

**Why you need it**: With 30+ MCP servers and complex agents, you're likely burning tokens inefficiently. This shows you exactly where to optimize.

---

## Phase 2: Specialized Plugins (Add as Needed)

### 2.1 Froggy Plugin
**Priority**: 🟡 Medium
**Repository**: `smartfrog/opencode-froggy`
**npm**: `opencode-froggy`

**What it does**: Hooks system + specialized agents + skills + tools (gitingest, pdf-to-markdown, blockchain queries)

**Specialized Agents**:
| Agent | Mode | Description |
|-------|------|-------------|
| `architect` | subagent | Strategic technical advisor for architecture decisions |
| `doc-writer` | subagent | Technical documentation writer |
| `code-reviewer` | subagent | Read-only quality/security review |
| `code-simplifier` | subagent | Simplifies code while preserving behavior |
| `partner` | subagent | Strategic ideation partner |
| `rubber-duck` | subagent | Exploratory thinking partner |

**Commands**:
```bash
/commit-push              # Stage, commit, push with confirmation
/review-changes           # Review uncommitted changes
/review-pr <source> <target>  # Review PR diff
/simplify-changes         # Simplify recent changes
/doc-changes              # Update docs for new features
/tests-coverage           # Run tests with coverage
/diff-summary [branch]    # Show working tree or branch diff
```

**Skills**:
- `ask-questions-if-underspecified` — Prevents ambiguous task execution
- `tdd` — Test-driven development workflow

**Tools**:
- `gitingest` — Ingest repository structure for analysis
- `pdf-to-markdown` — Convert PDFs to markdown
- `agent-promote` — Promote subagent to primary

**Why you need it**: Your `build` agent does everything. Froggy's specialized agents let you delegate code review, documentation, and simplification to purpose-built assistants with appropriate permissions.

---

### 2.2 Agent Skills (Dynamic Loader)
**Priority**: 🟡 Medium
**Repository**: `joshuadavidthomas/opencode-agent-skills`
**npm**: `opencode-agent-skills`

**What it does**: Dynamic skills loader that discovers skills from project, user, and plugin directories.

**Discovery Locations**:
- `~/.config/opencode/skills/` (user skills)
- `./.opencode/skills/` (project skills)
- `<plugin>/skills/` (plugin-bundled skills)

**Why you need it**: You already have skills in `~/dev/projects/agents/skills`. This plugin auto-discovers them without manual path configuration and enables project-specific skills.

---

### 2.3 EnvSitter Guard
**Priority**: 🟡 Medium
**Repository**: `boxpositron/envsitter-guard`

**What it does**: Prevents agents/tools from reading or editing sensitive `.env*` files. Allows safe inspection via EnvSitter (keys + deterministic fingerprints; never values).

**Why you need it**: Your MCP servers include gmail, linkedin, and various APIs with keys in config. This prevents accidental exposure of secrets in AI context.

---

### 2.4 Dynamic Context Pruning
**Priority**: 🟢 Low-Medium
**Repository**: `Tarquinen/opencode-dynamic-context-pruning`

**What it does**: Optimizes token usage by pruning obsolete tool outputs from conversation context.

**Why you need it**: With 30+ MCP servers, old tool outputs bloat context. This auto-prunes stale results.

---

### 2.5 Model Announcer
**Priority**: 🟢 Low
**Repository**: `ramarivera/opencode-model-announcer`

**What it does**: Injects the current model name into chat context so the LLM is self-aware.

**Why you need it**: Minor UX improvement — helps the agent know its own capabilities (context window, modalities).

---

## Phase 3: IDE Extensions

### 3.1 VS Code Extension
**Priority**: 🟡 Medium
**Marketplace**: `sst-dev.opencode` (official) or `sst-dev.opencode-v2` (beta)

**Features**:
- Launch OpenCode directly from VS Code
- Send selected code to OpenCode with context
- File/path awareness
- Multiple sessions support

**Installation**: Search "OpenCode" in VS Code Extensions Marketplace

### 3.2 JetBrains Plugin (Optional)
**Priority**: 🟢 Low
**Marketplace**: `OpenCode` (plugin ID 30681)

**Features**:
- AI coding agent inside JetBrains IDEs
- Context from active file, cursor position, open tabs
- Manual code selection support

### 3.3 Zed Extension (Optional)
**Priority**: 🟢 Low
**URL**: `zed.dev/extensions/opencode`

---

## Phase 4: Custom Plugin Development

Given your advanced setup, consider building **custom plugins** for your specific workflow:

### 4.1 Project-Specific Plugin
Create `~/.config/opencode/plugin/agents-workflow.ts`:

```typescript
import { Plugin } from '@opencode-ai/plugin'

export const AgentsWorkflowPlugin: Plugin = async (ctx) => {
  return {
    // Custom tool for your agents repo
    tool: {
      skill_validate: {
        description: 'Validate a skill file against AGENTS.md conventions',
        args: {
          path: { type: 'string', description: 'Path to SKILL.md' }
        },
        async execute({ path }) {
          // Run wagents validate on specific skill
          const result = await ctx.$`uv run wagents validate --skill ${path}`.text()
          return result
        }
      },
      readme_regenerate: {
        description: 'Regenerate README.md from repo contents',
        args: {},
        async execute() {
          await ctx.$`uv run wagents readme`.text()
          return 'README regenerated'
        }
      }
    },
    // Hook to auto-run validation on skill changes
    'file.edited': async ({ path }) => {
      if (path.endsWith('SKILL.md')) {
        await ctx.$`uv run wagents validate --skill ${path}`.quiet()
      }
    }
  }
}
```

### 4.2 MCP Orchestrator Plugin
Since you have 30+ MCP servers, create a plugin that intelligently routes queries:

```typescript
export const MCPOrchestratorPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      smart_search: {
        description: 'Intelligently search using the best MCP server for the query',
        args: {
          query: { type: 'string' },
          type: { type: 'string', enum: ['web', 'academic', 'news', 'code'] }
        },
        async execute({ query, type }) {
          // Route to appropriate MCP based on query type
          const routers = {
            web: ['brave-search', 'duckduckgo-search', 'exa'],
            academic: ['arxiv', 'context7'],
            news: ['tavily', 'brave-search'],
            code: ['deepwiki', 'repomix']
          }
          // ... implementation
        }
      }
    }
  }
}
```

---

## Integration Roadmap

### Week 1: Foundation
- [ ] Install **Oh My OpenAgent** or **Background Agents**
- [ ] Install **Agent Memory**
- [ ] Install **Claude Code Safety Net**
- [ ] Test background delegation with a research task
- [ ] Configure memory blocks (persona, human, project)

### Week 2: Optimization
- [ ] Install **Context Analysis Plugin**
- [ ] Analyze token usage patterns
- [ ] Optimize MCP server calls based on findings
- [ ] Install **Froggy Plugin** for specialized agents
- [ ] Configure `architect`, `code-reviewer`, and `doc-writer` agents

### Week 3: Security & Polish
- [ ] Install **EnvSitter Guard**
- [ ] Audit existing configs for secrets exposure
- [ ] Install **Dynamic Context Pruning** (if token usage is high)
- [ ] Install VS Code extension for IDE integration
- [ ] Create custom project-specific plugin for `wagents` workflow

### Week 4: Advanced Orchestration
- [ ] Build custom MCP orchestrator plugin
- [ ] Configure Oh My OpenAgent categories for model routing
- [ ] Set up tmux integration for background agent visibility
- [ ] Document your complete setup

---

## Configuration Summary

### Final `opencode.json` plugins array:
```json
{
  "plugin": [
    "opencode-shell-strategy",
    "opencode-antigravity-auth@latest",
    "opencode-gemini-auth@latest",
    "opencode-agent-memory",
    "claude-code-safety-net",
    "opencode-froggy",
    "opencode-agent-skills",
    "envsitter-guard",
    "oh-my-opencode"
  ]
}
```

> **Note**: Only include `oh-my-opencode` OR `opencode-background-agents`, not both (OMO includes background agents).

---

## Risk Assessment

| Plugin | Risk | Mitigation |
|--------|------|------------|
| Oh My OpenAgent | High complexity, many features | Install gradually; disable unused agents |
| Agent Memory | Memory files grow unbounded | Set `limit` fields; prune old journal entries |
| Safety Net | May block legitimate commands | Use `/safety-net allow <command>` for exceptions |
| EnvSitter Guard | May break tools needing env vars | Whitelist safe variables |
| Background Agents | Results consume disk space | Clean `~/.local/share/opencode/delegations/` periodically |

---

## Expected Outcomes

After full integration:
1. **2-5x productivity gain** from background delegation and specialized agents
2. **Token usage reduced 20-40%** from context pruning and intelligent routing
3. **Zero destructive command incidents** from semantic safety analysis
4. **Persistent project knowledge** across sessions via agent memory
5. **Full IDE integration** for seamless TUI ↔ GUI workflow

---

## References

- [Awesome OpenCode](https://github.com/awesome-opencode/awesome-opencode)
- [OpenCode Plugin Docs](https://opencode.ai/docs/plugins/)
- [Plugin Development Guide](https://gist.github.com/rstacruz/946d02757525c9a0f49b25e316fbe715)
- [OpenCode Plugin Marketplace](https://opencode-plugin-market.web.app/)
- [opencode.cafe](https://www.opencode.cafe/)
