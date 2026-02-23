# Skills installation and development commands
REPO := wyattowalsh/agents

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

## Development ----------------------------------------------------------------

validate:                 ## Validate all skills and agents
	uv run wagents validate

test:                     ## Run test suite
	uv run pytest

lint:                     ## Lint Python code
	uv run ruff check wagents/ skills/skill-creator/scripts/

audit:                    ## Audit all skill quality scores
	uv run python skills/skill-creator/scripts/audit.py --all --format table

package:                  ## Package all skills (dry-run)
	uv run wagents package --all --dry-run

readme:                   ## Regenerate README.md
	uv run wagents readme

help:                     ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: install install-agent install-skill list help \
        install-claude install-cursor install-copilot install-gemini \
        install-codex install-opencode install-crush install-antigravity \
        validate test lint audit package readme
