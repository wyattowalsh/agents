# When not Just — scope boundaries

Use this skill only for Just / justfile task-runner work. Redirect otherwise.

## Hard redirects

| User intent | Redirect |
| --- | --- |
| Generate or review a `.sh` / bash script | `shell-scripter` |
| Shell style conventions only (no justfile) | `shell-conventions` |
| GitHub Actions / CI workflow YAML | `devops-engineer` |
| Docker Compose file authorship | Compose / container skill — not this |
| mise / asdf / toolchain version product work | mise-oriented tooling — not this |
| Make pattern rules, headers → `.o`, precise mtimes | Stay on Make (or explain Just is a poor fit) |

## Soft boundaries

- **npm scripts as the product API** — may wrap with Just, but do not force deletion of `package.json` scripts used by other tools.
- **Python CLIs already covered by `just` in-repo** — edit existing recipes via this skill; do not invent parallel Make.
- **One-off shell one-liners** — if no justfile change is needed, do not open this skill's write path.

## Negative decision tests

Refuse `/justfile` (or implicit justfile framing) when:

1. Prompt is only "write a bash script that …" with no justfile mention → `shell-scripter`
2. Prompt is "add a CI workflow to …" → `devops-engineer`
3. Prompt is "create Dockerfile/compose …" → not Just
4. Prompt is "pin Node/Python versions with mise …" → not Just
5. Prompt is "Make builds `.c` to `.o` when headers change" → not a Just migration

## Ambiguous cases

| Signal | Prefer |
| --- | --- |
| "add a check recipe" + existing justfile | **edit** (this skill) |
| "add a check script" + no justfile | ask: script vs just recipe |
| "migrate Makefile" but heavy pattern rules | migrate **task** targets only; leave builds |
| "justfile mode" via shell-scripter | Prefer this dedicated `/justfile` skill |

## Refusal shape

When refusing:

1. Name the boundary in one sentence.
2. Name the correct skill or tool.
3. Offer a Just-shaped alternative only if the user actually wants recipes.

Do not partially author a justfile for an out-of-scope request unless the user
reframes to Just task-runner work.
