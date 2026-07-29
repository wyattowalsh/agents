set shell := ["bash", "-euo", "pipefail", "-c"]
set default-list
set minimum-version := "1.55.0"

# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #

# Just: https://just.systems (minimum 1.55.0; minimum-version, default-list, [arg long])
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

[doc("Install all skills to all agents (global)")]
[group("install")]
install:
    npx -y skills add {{ repo }} --skill '*' --agent '*' -g -y

[arg("agent", long, pattern="^[a-z0-9][a-z0-9-]*$", help="Harness id (e.g. claude-code, cursor)")]
[doc("Install all skills to one agent")]
[group("install")]
[positional-arguments]
install-agent agent:
    npx -y skills add {{ repo }} --skill '*' -a "$1" -g -y

[arg("skill", long, pattern="^[A-Za-z0-9._*/-]+$", help="Skill name or glob")]
[doc("Install specific skill(s) to all agents")]
[group("install")]
[positional-arguments]
install-skill skill:
    npx -y skills add {{ repo }} --skill "$1" --agent '*' -g -y

[doc("Install all skills to Claude (Code + Desktop)")]
[group("install")]
install-claude:
    npx -y skills add {{ repo }} --skill '*' -a claude-code -g -y

[doc("Install all skills to Cursor")]
[group("install")]
install-cursor:
    npx -y skills add {{ repo }} --skill '*' -a cursor -g -y

[doc("Install all skills to Codex")]
[group("install")]
install-codex:
    npx -y skills add {{ repo }} --skill '*' -a codex -g -y

[doc("Install all skills to OpenCode")]
[group("install")]
install-opencode:
    npx -y skills add {{ repo }} --skill '*' -a opencode -g -y

[doc("Install all skills to Crush")]
[group("install")]
install-crush:
    npx -y skills add {{ repo }} --skill '*' -a crush -g -y

[doc("List available skills without installing")]
[group("install")]
list:
    npx -y skills add {{ repo }} --list

[doc("Refresh installed skills from their recorded sources")]
[group("install")]
update:
    npx -y skills update

# ---------------------------------------------------------------------------- #
#                                     SYNC                                     #
# ---------------------------------------------------------------------------- #

[doc("Apply config/agent-delegation-policy.json task allowlists to opencode-agents.json")]
[group("sync")]
materialize-opencode-tasks:
    uv run python scripts/materialize_opencode_task_permissions.py --apply

[doc("Regenerate .opencode/agents from agents/ + config/opencode-agents.json")]
[group("sync")]
sync-opencode:
    uv run python scripts/materialize_opencode_task_permissions.py --apply
    uv run python scripts/sync_agent_stack.py --apply --targets repo --platforms opencode

[doc("Recompute apm.lock.yaml local_deployed_file_hashes from on-disk files")]
[group("sync")]
refresh-apm-lock:
    uv run wagents apm refresh-lock

[doc("OpenCode agent contract tests + platform sync check")]
[group("sync")]
verify-opencode:
    uv run pytest tests/test_sync_agent_stack.py tests/test_validate_repo.py tests/test_harness_plan_fixtures.py tests/test_apm_materialize.py -q -k "doctor_opencode or refresh_lock or opencode_managed or check_opencode_managed or render_opencode_agents_use or opencode_sync_repo or opencode_agents_on_disk or opencode_agents_config or opencode_agent_overlay" --tb=line
    uv run python scripts/sync_agent_stack.py --check --targets repo --platforms opencode
    uv run wagents apm doctor

# ---------------------------------------------------------------------------- #
#                                    CHECKS                                    #
# ---------------------------------------------------------------------------- #

[doc("Validate all skills and agents")]
[group("checks")]
validate:
    uv run wagents validate

[doc("Run test suite")]
[group("checks")]
test:
    uv run pytest

[doc("Lint Python code")]
[group("checks")]
lint:
    uv run ruff check

[doc("Check Python formatting")]
[group("checks")]
format:
    uv run ruff format --check

[doc("Type-check Python code")]
[group("checks")]
typecheck:
    uv run ty check

[doc("Lint, format-check, and type-check Python code")]
[group("checks")]
check-python: lint format typecheck

[doc("Lint GitHub Actions workflows (actionlint + analyzer)")]
[group("checks")]
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

[doc("Verify agent stack sync projections are fresh")]
[group("checks")]
sync-check:
    uv run python scripts/check_agent_stack.py

[doc("Audit all skill quality scores")]
[group("checks")]
audit:
    uv run python skills/skill-creator/scripts/audit.py --all --format table

[doc("Package all skills (dry-run)")]
[group("checks")]
package:
    uv run wagents package --all --dry-run

[doc("Run portable skill CI checks")]
[group("checks")]
skill-portability-check:
    SKILL_PORTABLE_CI=1 uv run pytest tests/test_skill_portability.py tests/test_skill_bundled_toolkit.py tests/test_skills_no_wagents.py tests/test_skills_p7_operator_paths.py tests/test_namer_catalog_parity.py tests/test_composed_catalog_script_parity.py tests/test_package.py -q --tb=line

[doc("Verify bundled asset_toolkit SSOT")]
[group("checks")]
skill-toolkit-sync-check:
    uv run python scripts/sync_skill_portability.py --check

[doc("Fast inner-loop check: validate + lint + key pytest subset")]
[group("checks")]
verify-fast:
    uv run wagents validate
    uv run ruff check
    uv run pytest tests/test_skills_catalog_schemas.py tests/test_catalog_index_parity.py tests/test_skill_index.py tests/test_authoring_sync.py -q --tb=line

[doc("Docs-focused check: generate + lint + build")]
[group("checks")]
verify-docs:
    uv run wagents docs generate --no-installed --check
    uv run wagents catalog index --check
    uv run wagents docs lint
    uv run wagents docs build

[doc("Full pre-PR check: verify-fast + verify-docs + ci-check")]
[group("checks")]
verify-all: verify-fast verify-docs ci-check
    uv run wagents openspec validate

# ---------------------------------------------------------------------------- #
#                                   OPENSPEC                                   #
# ---------------------------------------------------------------------------- #

[doc("Diagnose OpenSpec tooling and project state")]
[group("openspec")]
openspec-doctor:
    uv run wagents openspec doctor

[doc("Validate OpenSpec specs and changes")]
[group("openspec")]
openspec-validate:
    uv run wagents openspec validate

[doc("Print OpenSpec update command for downstream tool artifacts")]
[group("openspec")]
openspec-update:
    uv run wagents openspec update

# ---------------------------------------------------------------------------- #
#                                     DOCS                                     #
# ---------------------------------------------------------------------------- #

[doc("Regenerate README.md")]
[group("docs")]
readme:
    uv run wagents readme

# ---------------------------------------------------------------------------- #
#                                    MCPHUB                                    #
# ---------------------------------------------------------------------------- #

[doc("Start local MCPHub control plane with npx")]
[group("mcphub")]
mcphub-up:
    scripts/mcphub/up.sh

[doc("Stop local MCPHub control plane")]
[group("mcphub")]
mcphub-down:
    scripts/mcphub/down.sh

[doc("Tail local MCPHub logs")]
[group("mcphub")]
mcphub-logs:
    scripts/mcphub/logs.sh

[doc("Check local MCPHub prerequisites and health")]
[group("mcphub")]
mcphub-doctor:
    scripts/mcphub/doctor.sh

[doc("Generate mcp/mcphub/mcp_settings.json from config/mcp-registry.json")]
[group("mcphub")]
mcphub-generate:
    uv run python scripts/generate_mcphub_settings.py

[doc("Fail when tracked MCPHub settings are stale vs registry")]
[group("mcphub")]
mcphub-generate-check:
    uv run python scripts/generate_mcphub_settings.py --check

[doc("Validate tracked MCPHub settings")]
[group("mcphub")]
mcphub-validate:
    scripts/mcphub/validate-settings.sh

[doc("Export MCPHub OpenAPI spec")]
[group("mcphub")]
mcphub-openapi:
    scripts/mcphub/export-openapi.sh

[doc("Sync runtime settings, warm package-version-check-mcp, restart LaunchAgent")]
[group("mcphub")]
[positional-arguments]
mcphub-reconcile-runtime *FLAGS:
    scripts/mcphub/reconcile-runtime.sh "$@"

[doc("Run MCPHub health and tools/list smoke test")]
[group("mcphub")]
mcphub-smoke:
    scripts/mcphub/smoke.sh

[doc("Install local LaunchAgent template")]
[group("mcphub")]
mcphub-install-launch-agent:
    #!/usr/bin/env bash
    set -euo pipefail
    repo_root="$(pwd)"
    mkdir -p "$HOME/Library/LaunchAgents"
    sed "s|/path/to/agents|${repo_root}|g" config/launchd/com.wyattowalsh.mcphub.plist \
        > "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist" >/dev/null 2>&1 || true
    launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"
    launchctl kickstart -k "gui/$(id -u)/com.wyattowalsh.mcphub"

[doc("Uninstall local LaunchAgent")]
[group("mcphub")]
mcphub-uninstall-launch-agent:
    #!/usr/bin/env bash
    set -euo pipefail
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist" || true
    rm -f "$HOME/Library/LaunchAgents/com.wyattowalsh.mcphub.plist"

# ---------------------------------------------------------------------------- #
#                                      APM                                     #
# ---------------------------------------------------------------------------- #

[doc("Materialize via apm (installs to apm_modules/ and harness dirs)")]
[group("apm")]
apm-materialize:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v apm >/dev/null || { echo "apm CLI not found (pip install apm-cli)" >&2; exit 127; }
    apm install --frozen || apm install

[doc("Install bundle via apm (primary path)")]
[group("apm")]
apm-install:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v apm >/dev/null || { echo "apm CLI not found (pip install apm-cli)" >&2; exit 127; }
    apm install wyattowalsh/agents

[doc("Compile context with apm")]
[group("apm")]
apm-compile:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v apm >/dev/null || { echo "apm CLI not found (pip install apm-cli)" >&2; exit 127; }
    apm compile

[doc("Run apm audit in CI mode (no-drift for local tolerance)")]
[group("apm")]
apm-audit:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v apm >/dev/null || { echo "apm CLI not found (pip install apm-cli)" >&2; exit 127; }
    apm audit --ci --no-drift

[doc("Diagnose apm CLI presence and version")]
[group("apm")]
apm-doctor:
    @command -v apm >/dev/null && apm --version || echo "apm CLI not found (pip install apm-cli)"
