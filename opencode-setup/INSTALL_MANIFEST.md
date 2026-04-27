# OpenCode Plugin Installation Manifest
# Completed: 2026-04-27
# Backup: ~/.config/opencode/opencode.json.backup-*

## Installation Results — ALL PHASES COMPLETE

### Pre-Existing Plugins (3)
- [x] opencode-shell-strategy
- [x] opencode-antigravity-auth@latest
- [x] opencode-gemini-auth@latest

### Phase 1: Safety & Memory (3)
- [x] cc-safety-net@0.8.2 - Semantic command analysis, blocks destructive ops
- [x] opencode-agent-memory@0.2.0 - Persistent self-editable memory blocks
- [x] envsitter-guard@0.0.4 - Blocks .env* file access by agents

### Phase 2: Token Optimization (3)
- [x] @tarquinen/opencode-dcp@3.1.9 - Dynamic context pruning, deduplication
- [x] opencode-snip@1.6.1 - 60-97% token savings on shell output
- [x] @morphllm/opencode-morph-plugin@2.0.9 - Fast Apply (10,500+ tok/s), WarpGrep

### Phase 3: Agents & Workflow (3)
- [x] opencode-froggy@0.11.0 - 6 specialized agents + slash commands
- [x] opencode-handoff@0.5.0 - Session continuity with handoff prompts
- [x] opencode-agent-skills@0.6.5 - Dynamic skill discovery with semantic matching

### Phase 4: Observability & Review (3)
- [x] @devtheops/opencode-plugin-otel@0.8.0 - OpenTelemetry metrics/traces/logs
- [x] open-plan-annotator@1.3.0 - Browser-based plan review UI
- [x] @simonwjackson/opencode-direnv@2025.1211.9 - .envrc auto-loading ⚠️ deprecated

### Phase 5: Oh-My-OpenCode Alternatives (2)
- [x] opencode-background-agents@0.1.1 - Async/background delegation
- [x] micode@0.10.0 - 12 specialized agents with enforced workflow

### Phase 6: Optional Polish (2)
- [x] opencode-notify@0.3.1 - OS notifications when tasks complete
- [x] opencode-devcontainers@0.3.3 - Isolated branch workspaces via devcontainers/worktrees
- [x] @ramarivera/opencode-model-announcer@1.0.2 - Injects current model name into context

### Phase 7: Native Configuration
- [x] `mode` section: `build`, `plan` — drives TUI shift+tab agent switching
- [x] `agent` section: `build`, `plan`, `explore`, `review`, `architect`, `tester` — full agent definitions
- [x] All agents use `opencode-go/kimi-k2.6` (per OpenCode global instructions)
- [ ] ~~Formatters~~ — **Not supported by OpenCode v1.14.28** (config validation failed, removed)

## Total Plugin Count
- **20 plugins** installed (3 pre-existing + 17 new)
- All pinned to specific versions for reproducibility

## Deprecation Notices
1. `@simonwjackson/opencode-direnv@2025.1211.9` - Deprecated but functional
   - Alternative: Native direnv shell integration

## Verification Commands
```bash
# List all installed plugins
opencode plugin list

# View plugin details
opencode plugin list --json

# Check config
opencode stats
```

## Rollback
If issues occur, restore from backup:
```bash
cp ~/.config/opencode/opencode.json.backup-* ~/.config/opencode/opencode.json
```

## Configuration Locations
- Main config: `~/.config/opencode/opencode.json`
- TUI config: `~/.config/opencode/tui.json`
- Plugin data: `~/.config/opencode/node_modules/`
- Agent memory: `~/.config/opencode/memory/` (created by opencode-agent-memory)
- DCP config: `~/.config/opencode/dcp.jsonc`
- Devcontainers: `~/.config/opencode/devcontainers.json`

## Next Steps
1. Restart OpenCode TUI to verify all 20 plugins load
2. Test `/dcp stats` for context pruning
3. Test `/handoff` for session continuity
4. Run `opencode stats` for telemetry
5. Verify `opencode-agent-memory` initialized memory blocks
6. Test background agents with async delegation
