# Design

## Lifecycle Packet

Meaningful skill creation and improvement work produces a compact lifecycle
packet before implementation:

| Field | Meaning |
| --- | --- |
| `source_evidence` | Existing workflows, docs, user examples, logs, or exemplar skills used as evidence |
| `trigger_surface` | Positive triggers, near-miss negatives, and explicit scope boundaries |
| `eval_plan` | Static eval cases and optional behavioral eval categories |
| `security_posture` | Tools, scripts, hooks, network, credentials, writes, installs, and approval gates |
| `runtime_matrix` | Portable core, portable-but-variable behavior, and runtime-specific fallbacks |
| `baseline` | `without_skill` for new skills or `old_skill` for improvements |

The packet is a planning and review contract, not a generated registry format.
It can be represented in a plan, report, or benchmark artifact.

## Security Governance

Skill-creator treats skills as executable supply-chain assets. Security review
covers `SKILL.md`, frontmatter, scripts, hooks, templates, references, body
substitutions, dependencies, generated examples, remote sources, and packaged
artifacts. A blocking finding prevents release or endorsement until fixed or
explicitly accepted by the maintainer.

## Behavioral Proof

Static validation remains mandatory. Behavioral measurement is explicit and
opt-in:

- New skills compare `with_skill` against `without_skill`.
- Existing-skill improvements compare `new_skill` against `old_skill`.
- Description optimization uses should-trigger and should-not-trigger queries
  plus held-out near misses.
- Run artifacts live outside committed `skills/` source unless a sanitized
  report is intentionally referenced.

## Parallel Orchestration

Parallelism is limited by verified independence. Every worker lane declares
owned paths/resources, dependencies, locks, artifacts, validation commands,
handoff criteria, and judge criteria. Same-file edits, generated surfaces,
OpenSpec, hooks, validators, and public workflow changes serialize behind a
lead or judge lane.

## Compatibility

Skill-creator documentation distinguishes:

- portable core fields and bundled skill files,
- portable-but-variable behavior such as scripts, hooks, body substitutions,
  and tool allowlists,
- runtime-specific fields, install paths, and plugin projections.

Portable packages must degrade clearly when a target runtime lacks a variable
feature.

Executable hook commands are treated as runtime-specific unless they resolve
inside the packaged skill folder. Repo-managed hooks belong in projection
config such as `config/hook-registry.json` and generated harness settings.
Package and audit portability checks flag frontmatter command strings that rely
on repo-root `skills/<name>/...` paths, `{repo_root}`, `${workspaceFolder}`, or
machine-local absolute paths.
