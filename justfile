set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list := true

# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #

# Just: https://just.systems (minimum 1.52.0 — default-list, [arg long])
# npx: Skills CLI (https://github.com/vercel-labs/add-skill)
# uv: Python toolchain (https://docs.astral.sh/uv/)

npx := require("npx")
uv := require("uv")

# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #

repo := "github:wyattowalsh/agents"

# ---------------------------------------------------------------------------- #
#                                   DEFAULT                                    #
# ---------------------------------------------------------------------------- #

[default]
[doc("List available recipes (safe fallback when default-list unavailable)")]
default:
    @just --list

# ---------------------------------------------------------------------------- #
#                              SKILLS INSTALLATION                             #
# ---------------------------------------------------------------------------- #

[group("install")]
[doc("Install all skills to all agents (global)")]
install:
    npx -y skills add {{ repo }} --skill '*' --agent '*' -g -y

[group("install")]
[doc("Install all skills to one agent")]
[arg("agent", long, help="Harness id (e.g. claude-code, cursor)")]
install-agent agent:
    npx -y skills add {{ repo }} --skill '*' -a {{ agent }} -g -y

[group("install")]
[doc("Install specific skill(s) to all agents")]
[arg("skill", long, help="Skill name or glob")]
install-skill skill:
    npx -y skills add {{ repo }} --skill {{ skill }} --agent '*' -g -y

[group("install")]
[doc("Install all skills to Claude (Code + Desktop)")]
install-claude:
    npx -y skills add {{ repo }} --skill '*' -a claude-code -g -y

[group("install")]
[doc("Install all skills to Cursor")]
install-cursor:
    npx -y skills add {{ repo }} --skill '*' -a cursor -g -y

[group("install")]
[doc("Install all skills to GitHub Copilot")]
install-copilot:
    npx -y skills add {{ repo }} --skill '*' -a github-copilot -g -y

[group("install")]
[doc("Install all skills to Gemini CLI")]
install-gemini:
    npx -y skills add {{ repo }} --skill '*' -a gemini-cli -g -y

[group("install")]
[doc("Install all skills to Codex")]
install-codex:
    npx -y skills add {{ repo }} --skill '*' -a codex -g -y

[group("install")]
[doc("Install all skills to OpenCode")]
install-opencode:
    npx -y skills add {{ repo }} --skill '*' -a opencode -g -y

[group("install")]
[doc("Install all skills to Crush")]
install-crush:
    npx -y skills add {{ repo }} --skill '*' -a crush -g -y

[group("install")]
[doc("Install all skills to Antigravity")]
install-antigravity:
    npx -y skills add {{ repo }} --skill '*' -a antigravity -g -y

[group("install")]
[doc("List available skills without installing")]
list:
    npx -y skills add {{ repo }} --list

[group("install")]
[doc("Refresh installed skills from their recorded sources")]
update:
    npx -y skills update

# ---------------------------------------------------------------------------- #
#                                     SYNC                                     #
# ---------------------------------------------------------------------------- #

[group("sync")]
[doc("Regenerate .opencode/agents from agents/ + config/opencode-agents.json")]
sync-opencode:
    uv run python scripts/sync_agent_stack.py --apply --targets repo --platforms opencode

[group("sync")]
[doc("Recompute apm.lock.yaml local_deployed_file_hashes from on-disk files")]
refresh-apm-lock:
    uv run wagents apm refresh-lock

[group("sync")]
[doc("OpenCode agent contract tests + platform sync check")]
verify-opencode:
    uv run pytest tests/test_sync_agent_stack.py tests/test_validate_repo.py tests/test_harness_plan_fixtures.py tests/test_apm_materialize.py -q -k "doctor_opencode or refresh_lock or opencode_managed or check_opencode_managed or render_opencode_agents_use or opencode_sync_repo or opencode_agents_on_disk or opencode_agents_config or opencode_agent_overlay" --tb=line
    uv run python scripts/sync_agent_stack.py --check --targets repo --platforms opencode
    uv run wagents apm doctor

# ---------------------------------------------------------------------------- #
#                                    CHECKS                                    #
# ---------------------------------------------------------------------------- #

[group("checks")]
[doc("Validate all skills and agents")]
validate:
    uv run wagents validate

[group("checks")]
[doc("Run test suite")]
test:
    uv run pytest

[group("checks")]
[doc("Lint Python code")]
lint:
    uv run ruff check

[group("checks")]
[doc("Check Python formatting")]
format:
    uv run ruff format --check

[group("checks")]
[doc("Type-check Python code")]
typecheck:
    uv run ty check

[group("checks")]
[doc("Lint, format-check, and type-check Python code")]
check-python: lint format typecheck

[group("checks")]
[doc("Lint GitHub Actions workflows (actionlint + analyzer)")]
ci-check:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v actionlint >/dev/null || {
        echo "actionlint not found (brew install actionlint)"
        exit 1
    }
    actionlint .github/workflows/*.yml
    for wf in .github/workflows/*.yml; do
        uv run python skills/devops-engineer/scripts/workflow-analyzer.py "$wf" | \
            uv run python -c 'import json,sys; d=json.load(sys.stdin); s=d["summary"]; \
            assert s["critical_issues"]==0 and s["warnings"]==0, d; \
            print("workflow-analyzer OK:", d["file"])'
    done

[group("checks")]
[doc("Verify agent stack sync projections are fresh")]
sync-check:
    uv run python scripts/check_agent_stack.py

[group("checks")]
[doc("Audit all skill quality scores")]
audit:
    uv run python skills/skill-creator/scripts/audit.py --all --format table

[group("checks")]
[doc("Package all skills (dry-run)")]
package:
    uv run wagents package --all --dry-run

[group("checks")]
[doc("Run portable skill CI checks")]
skill-portability-check:
    SKILL_PORTABLE_CI=1 uv run pytest tests/test_skill_portability.py tests/test_skill_bundled_toolkit.py tests/test_skills_no_wagents.py tests/test_skills_p7_operator_paths.py tests/test_namer_catalog_parity.py tests/test_composed_catalog_script_parity.py tests/test_package.py -q --tb=line

[group("checks")]
[doc("Verify bundled asset_toolkit SSOT")]
skill-toolkit-sync-check:
    uv run python scripts/sync_skill_portability.py --check

[group("checks")]
[doc("Fast inner-loop check: validate + lint + key pytest subset")]
verify-fast:
    uv run wagents validate
    uv run ruff check
    uv run pytest tests/test_skills_catalog_schemas.py tests/test_catalog_index_parity.py tests/test_skill_index.py tests/test_authoring_sync.py -q --tb=line

[group("checks")]
[doc("Docs-focused check: generate + lint + build")]
verify-docs:
    uv run wagents docs generate --no-installed --check
    uv run wagents catalog index --check
    uv run wagents docs lint

[group("checks")]
[doc("Full pre-PR check: verify-fast + verify-docs + ci-check")]
verify-all: verify-fast verify-docs ci-check
    uv run wagents openspec validate

# ---------------------------------------------------------------------------- #
#                                   OPENSPEC                                   #
# ---------------------------------------------------------------------------- #

[group("openspec")]
[doc("Diagnose OpenSpec tooling and project state")]
openspec-doctor:
    uv run wagents openspec doctor

[group("openspec")]
[doc("Validate OpenSpec specs and changes")]
openspec-validate:
    uv run wagents openspec validate

[group("openspec")]
[doc("Print OpenSpec update command for downstream tool artifacts")]
openspec-update:
    uv run wagents openspec update

# ---------------------------------------------------------------------------- #
#                                     DOCS                                     #
# ---------------------------------------------------------------------------- #

[group("docs")]
[doc("Regenerate README.md")]
readme:
    uv run wagents readme

# ---------------------------------------------------------------------------- #
#                                    MCPHUB                                    #
# ---------------------------------------------------------------------------- #

[group("mcphub")]
[doc("Start local MCPHub control plane with npx")]
mcphub-up:
    scripts/mcphub/up.sh

[group("mcphub")]
[doc("Stop local MCPHub control plane")]
mcphub-down:
    scripts/mcphub/down.sh

[group("mcphub")]
[doc("Tail local MCPHub logs")]
mcphub-logs:
    scripts/mcphub/logs.sh

[group("mcphub")]
[doc("Check local MCPHub prerequisites and health")]
mcphub-doctor:
    scripts/mcphub/doctor.sh

[group("mcphub")]
[doc("Generate mcp/mcphub/mcp_settings.json from config/mcp-registry.json")]
mcphub-generate:
    uv run python scripts/generate_mcphub_settings.py

[group("mcphub")]
[doc("Fail when tracked MCPHub settings are stale vs registry")]
mcphub-generate-check:
    uv run python scripts/generate_mcphub_settings.py --check

[group("mcphub")]
[doc("Validate tracked MCPHub settings")]
mcphub-validate:
    scripts/mcphub/validate-settings.sh

[group("mcphub")]
[doc("Export MCPHub OpenAPI spec")]
mcphub-openapi:
    scripts/mcphub/export-openapi.sh

[group("mcphub")]
[doc("Run MCPHub health and tools/list smoke test")]
mcphub-smoke:
    scripts/mcphub/smoke.sh

[group("mcphub")]
[doc("Install local LaunchAgent template")]
mcphub-install-launch-agent:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p "$HOME/Library/LaunchAgents"
    cp config/launchd/com.wyattowalsh.mcphub.plist "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist" >/dev/null 2>&1 || true
    launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
    launchctl kickstart -k "gui/$(id -u)/com.wyattowalsh.mcphub"

[group("mcphub")]
[doc("Uninstall local LaunchAgent")]
mcphub-uninstall-launch-agent:
    #!/usr/bin/env bash
    set -euo pipefail
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist" || true
    rm -f "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"

# ---------------------------------------------------------------------------- #
#                                      APM                                     #
# ---------------------------------------------------------------------------- #

[group("apm")]
[doc("Materialize via apm (installs to apm_modules/ and harness dirs)")]
apm-materialize:
    -apm install --frozen || -apm install

[group("apm")]
[doc("Install bundle via apm (primary path)")]
apm-install:
    -apm install wyattowalsh/agents

[group("apm")]
[doc("Compile context with apm")]
apm-compile:
    -apm compile

[group("apm")]
[doc("Run apm audit in CI mode (no-drift for local tolerance)")]
apm-audit:
    -apm audit --ci --no-drift

[group("apm")]
[doc("Diagnose apm CLI presence and version")]
apm-doctor:
    @command -v apm >/dev/null && apm --version || echo "apm CLI not found (pip install apm-cli)"
