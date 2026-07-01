# Design

## Plan Critique

The first RTK plan had the right center of gravity: hook-first where possible, OpenCode plugin ownership left to RTK, and no shared `@RTK.md` include. The weak points were operational:

- It mixed "can be configured" with "currently configured." Doctor output must distinguish binary presence, command capability, and local hook state.
- It underplayed RTK init cross-effects. Current `rtk init -g --agent cursor --auto-patch` also plans Claude RTK files, so sync must stay dry-run-first.
- It treated Grok as almost Claude-compatible without proof. Grok remains a custom-follow-up lane until live hook output shape is verified.
- It proposed new global prose in several instruction files. The repo should keep always-loaded RTK prose small and platform-scoped.
- It did not account for the active research write guard blocking the approved implementation after `/research`. That hook needs a handoff path rather than a manual settings edit.

## Architecture

`config/rtk-integration.json` is the repo policy and command map. `wagents rtk` reads that file and never scrapes markdown plans.

The CLI has three operational layers:

1. Binary checks: `rtk --version`, semantic floor comparison, `rtk gain` probe.
2. Capability checks: `rtk init --help` must expose requested flags before sync recommends them.
3. Harness posture checks: `rtk init --show` and target-specific show commands are parsed into ok/warn/fail rows.

The sync command is intentionally command orchestration, not a custom hook generator. It prints or runs upstream RTK init commands for supported harnesses. Repo-owned custom Grok hooks are represented as `repo:` commands and remain dry-run-only until a follow-up implementation adds the shim.

## Ownership Rules

- RTK owns `RTK.md`, local shell hooks, and local plugin files.
- The agents repo owns policy, dry-run orchestration, validation, and public documentation.
- `opencode.json` must not include RTK as a plugin entry.
- Shared instruction files must not include `@RTK.md`.
- Generated docs may mention RTK only from generated or authored repo sources, not from local machine paths.

## Parallel Task Graph

The graph is optimized for a large subagent team. Same-file writers are serialized; read-only exploration and validation fan out.

| Node | Lane | Depends On | Writer | Deliverable |
| --- | --- | --- | --- | --- |
| R00 | research-upstream-help | none | no | Current `rtk init --help`, `--show`, release/version facts |
| R01 | research-harness-surfaces | none | no | Harness matrix from registry and docs |
| R02 | research-prior-failures | none | no | Stale `@RTK.md` and hook-blocker evidence |
| H00 | hook-diagnose | R02 | no | Identify write blocker state path and policy |
| H01 | hook-implement | H00 | yes: `hooks/wagents-hook.py` | Implementation handoff clears active research state |
| H02 | hook-tests | H01 | yes: `tests/test_wagents_hook.py` | Regression tests for activation and handoff |
| C00 | config-schema | R00,R01 | yes: `config/rtk-integration.json` | Policy and command map |
| O00 | openspec-proposal | R00,R01,R02 | yes: proposal files | Why/what/scope/risk |
| O01 | openspec-spec-delta | C00 | yes: spec delta | Downstream tooling requirements |
| O02 | task-graph | R00,R01,R02 | yes: tasks/design | Hyperfine task graph |
| W00 | cli-module | C00 | yes: `wagents/rtk.py` | Doctor, sync plan, gain wrapper functions |
| W01 | cli-registration | W00 | yes: `wagents/cli.py` | `wagents rtk` Typer app |
| W02 | self-doctor-row | W00 | yes: `wagents/self_cmd.py` | Non-fatal RTK row |
| T00 | cli-unit-tests | W00,W01 | yes: tests | RTK doctor/sync JSON tests |
| T01 | self-tests | W02 | yes: tests | `self doctor` includes RTK |
| V00 | focused-hook-validation | H02 | no | Hook tests pass |
| V01 | focused-cli-validation | T00,T01 | no | CLI tests pass |
| V02 | openspec-validation | O00,O01,O02 | no | OpenSpec validation command result |
| V03 | final-diff-review | all writers | no | Diff inspected; unrelated dirty state preserved |

## Stop Rules

- Do not run `wagents rtk sync --apply` unless the maintainer explicitly asks for live local hook installation.
- Do not edit `~/.config/opencode/plugins/rtk.ts`, `~/.claude/RTK.md`, `~/.codex/RTK.md`, or other RTK-generated local files from repo code.
- Do not add generated RTK artifacts to `skills/`, `agents/`, or `instructions/global.md`.
- Stop if `rtk init --help` drops a planned flag; update the policy config before sync can recommend it.

## Follow-Up Lanes

- Implement and live-test a Grok RTK rewrite hook only after Grok hook input/output schema is verified.
- Add optional sync integration into `scripts/sync_agent_stack.py` behind an explicit `--with-rtk` flag.
- Add docs catalog or README text only after the doctor/sync surface stabilizes.
