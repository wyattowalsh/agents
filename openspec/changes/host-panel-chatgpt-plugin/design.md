# Design

## Canonical Instruction Ownership

Keep `skills/host-panel/SKILL.md` and `references/*.md` as the single instruction source for Chat and other compatible skill-capable runtimes. The plugin is a generated projection, not a separately edited copy. Preserve the existing three formats and the exclusion of ordinary code review and simulated real human opinion.

## Preservation And Contract Changes

| Existing rule | Revised contract | Reason and retained protection |
| --- | --- | --- |
| Require a quoted topic through `/host-panel` | Accept natural-language and contextual requests; retain the documented slash form where supported | Quotes are an interface convention rather than a deliberation safeguard. Resolve an unambiguous topic from the conversation, and ask only when the intended scope is materially unresolved. No invented panel topic. |
| Every initial position is independent and precedes seeing other claims | Default to explicitly labeled single-context perspective simulation; label separate first-pass calls only when actual tools isolate them from peer outputs | Ordinary one-context generation cannot establish independence. Preserve initial positions before cross-talk as a structure, and use actual peer-blind calls when available. Separate calls do not imply statistical independence or multiple providers. |
| One global verified/thin/unverified badge | Distinguish claim-level support, evidence quality, inference, and gaps; summarize mixed coverage honestly | A verified citation cannot validate every statement in a panel. Preserve explicit source limitations and citation integrity without a misleading all-or-nothing badge. |
| Add an absent counterposition when participants converge | Test convergent claims against omitted assumptions and evidence; preserve agreement when supported | Prevent conformity without manufacturing dissent or false balance. Preserve significant minority arguments when their support warrants it. |
| Never skip final synthesis | Complete normal panels with synthesis; obey explicit pause, stop, and end instructions | User control takes precedence. Pausing preserves state without advancing; stopping does not force another panel phase or unwanted synthesis. |
| Roundtable, Oxford, and Socratic formats | Retain all three with their distinct phases and eligibility requirements | Compact output changes presentation, not the intellectual purpose of the format. A bounded challenge phase is interpreted within the selected format. |
| Research before constructing the roster | Retain research-first grounding whenever factual claims require it; state unavailable or mixed evidence | Methodological perspectives remain tied to the question and evidence. No invented credentials, citations, people, or consensus. |
| Final synthesis tracks changes and cruxes rather than voting | Retain facts, interpretations, position changes, cruxes, residual disagreements, and practical implications | Agreement and fluent rhetoric remain non-evidence. More participants or rounds do not imply greater accuracy. |

## Invocation And Execution

`@host-panel` is the intended user-facing entrypoint. Actual discovery, mention routing, reference loading, and context access must be observed in the target product; the source package alone does not establish them. The instruction contract also supports an ordinary request to host a panel when the skill is available.

Use the tools the current runtime actually exposes. The default needs no shell, external provider, backend, or extra authentication. Evidence retrieval and isolated workers are optional capabilities, reported according to what was used. Shared evidence can still create correlated blind spots even with separate workers.

Conversation state tracks the topic, format, perspectives, sources, claims, cruxes, updates, and current phase. Added evidence and changed assumptions update that record explicitly. No external storage occurs as a side effect of running the panel. Export is requested separately.

## Narrow Packaging

`config/plugins/host-panel.json` is a versionless manifest template using `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. OpenAI interface metadata stays inside `extensions.com.openai.interface`. The template declares no MCP server, apps, dependencies, or policy. `shortDescription` is at most 30 characters.

The exporter reads only:

- The versionless template.
- `skills/host-panel/SKILL.md`.
- Flat `skills/host-panel/references/*.md` files.

It emits a new ZIP with root `plugin.json` and the canonical skill paths. `--release-version` injects SemVer only into the archived manifest. Canonical Markdown bytes are preserved exactly. Sorted members, fixed timestamps, permissions, and compression settings make builds reproducible for identical source bytes and release identity in the same runtime. A source-content digest and archive digest are returned without adding bookkeeping files to the package.

The content digest describes the bytes read for that build. It is not a repository-wide atomic snapshot or a guarantee against all concurrent edits. Build the release after the canonical edits settle; per-file read checks only detect the changes they can observe.

The output must be outside the source repository and must not already exist. Reject source and output symlinks, invalid identity, missing reference directories, and local Markdown links that escape or point outside the included files. Anchor fragments are excluded from path checks; HTTP(S) and mailto links remain external. Source and interface validation happen before output creation.

## Reuse And Scope

The existing `wagents package` command packages skill ZIPs and includes a bundled validation toolkit. It does not produce this narrow plugin artifact. The documented generic `wagents plugin build` implementation is absent from the pinned checkout. A small standalone exporter avoids reviving unrelated distribution infrastructure or changing the existing package format.

Use the root project's Python, Ruff, ty, and pytest tooling. Add no dependency. Existing package tests provide conventions, but only the new exporter's meaningful behavior tests are required for its implementation. Repository-wide gates can report unrelated failures without weakening checks or repairing unrelated assets.
