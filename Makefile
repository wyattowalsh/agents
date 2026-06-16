# Skills installation and development commands
REPO := github:wyattowalsh/agents

## Installation ---------------------------------------------------------------

install:                  ## Install all skills to all agents (global)
	npx -y skills add $(REPO) --skill '*' --agent '*' -g -y

install-agent:            ## Install all skills to one agent: make install-agent AGENT=claude-code
ifndef AGENT
	$(error AGENT is required: make install-agent AGENT=claude-code)
endif
	npx -y skills add $(REPO) --skill '*' -a $(AGENT) -g -y

install-skill:            ## Install specific skill(s) to all agents: make install-skill SKILL=honest-review
ifndef SKILL
	$(error SKILL is required: make install-skill SKILL=honest-review)
endif
	npx -y skills add $(REPO) --skill $(SKILL) --agent '*' -g -y

install-claude:           ## Install all skills to Claude (Code + Desktop)
	npx -y skills add $(REPO) --skill '*' -a claude-code -g -y

install-cursor:           ## Install all skills to Cursor
	npx -y skills add $(REPO) --skill '*' -a cursor -g -y

install-copilot:          ## Install all skills to GitHub Copilot
	npx -y skills add $(REPO) --skill '*' -a github-copilot -g -y

install-gemini:           ## Install all skills to Gemini CLI
	npx -y skills add $(REPO) --skill '*' -a gemini-cli -g -y

install-codex:            ## Install all skills to Codex
	npx -y skills add $(REPO) --skill '*' -a codex -g -y

install-opencode:         ## Install all skills to OpenCode
	npx -y skills add $(REPO) --skill '*' -a opencode -g -y

install-crush:            ## Install all skills to Crush
	npx -y skills add $(REPO) --skill '*' -a crush -g -y

install-antigravity:      ## Install all skills to Antigravity
	npx -y skills add $(REPO) --skill '*' -a antigravity -g -y

list:                     ## List available skills without installing
	npx -y skills add $(REPO) --list

update:                   ## Refresh installed skills from their recorded sources
	npx -y skills update

## Development ----------------------------------------------------------------

validate:                 ## Validate all skills and agents
	uv run wagents validate

test:                     ## Run test suite
	uv run pytest

lint:                     ## Lint Python code
	uv run ruff check wagents/ tests/ scripts/validate/ skills/skill-creator/scripts/

typecheck:                ## Type-check Python code
	uv run ty check

audit:                    ## Audit all skill quality scores
	uv run python skills/skill-creator/scripts/audit.py --all --format table

package:                  ## Package all skills (dry-run)
	uv run wagents package --all --dry-run

openspec-doctor:          ## Diagnose OpenSpec tooling and project state
	uv run wagents openspec doctor

openspec-validate:        ## Validate OpenSpec specs and changes
	uv run wagents openspec validate

openspec-update:          ## Print OpenSpec update command for downstream tool artifacts
	uv run wagents openspec update

readme:                   ## Regenerate README.md
	uv run wagents readme

mcphub-up:                ## Start local MCPHub control plane with npx
	scripts/mcphub/up.sh

mcphub-down:              ## Stop local MCPHub control plane
	scripts/mcphub/down.sh

mcphub-logs:              ## Tail local MCPHub logs
	scripts/mcphub/logs.sh

mcphub-doctor:            ## Check local MCPHub prerequisites and health
	scripts/mcphub/doctor.sh

mcphub-validate:          ## Validate tracked MCPHub settings
	scripts/mcphub/validate-settings.sh

mcphub-openapi:           ## Export MCPHub OpenAPI spec
	scripts/mcphub/export-openapi.sh

mcphub-smoke:             ## Run MCPHub health and tools/list smoke test
	scripts/mcphub/smoke.sh

mcphub-install-launch-agent: ## Install local LaunchAgent template
	mkdir -p "$$HOME/Library/LaunchAgents"
	cp config/launchd/com.wyattowalsh.mcphub.plist "$$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
	-launchctl bootout "gui/$$(id -u)" "$$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist" >/dev/null 2>&1
	launchctl bootstrap "gui/$$(id -u)" "$$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
	launchctl kickstart -k "gui/$$(id -u)/com.wyattowalsh.mcphub"

mcphub-uninstall-launch-agent: ## Uninstall local LaunchAgent
	-launchctl bootout "gui/$$(id -u)" "$$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
	rm -f "$$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"

help:                     ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: install install-agent install-skill list update help \
        install-claude install-cursor install-copilot install-gemini \
        install-codex install-opencode install-crush install-antigravity \
        validate test lint typecheck audit package openspec-doctor \
        openspec-validate openspec-update readme \
        mcphub-up mcphub-down mcphub-logs mcphub-doctor mcphub-validate \
        mcphub-openapi mcphub-smoke mcphub-install-launch-agent \
        mcphub-uninstall-launch-agent
