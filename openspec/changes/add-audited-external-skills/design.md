# Design

## Approach

Reuse the existing curated external skill mechanism instead of introducing a new registry. Add only audited command entries and harness coverage notes to `instructions/external-skills.md`, then let existing `wagents` inventory/docs generation read that source wherever possible.

## Audit-Gated Sources

- `ljagiello/ctf-skills` is accepted as `inspect then install` after audit because it provides useful CTF-domain skills, has an MIT license, and includes responsible-use framing, but it also contains offensive-security workflows, write-capable permissions, and a broad local tooling installer.
- `nextlevelbuilder/ui-ux-pro-max-skill` is accepted as `inspect then install` for `ui-ux-pro-max` only because the main skill has useful design intelligence and no observed hooks, while bundled `ckm:*` skills overlap existing local skills and introduce broader API/script surfaces.
- `Leonxlnx/taste-skill` is accepted as `inspect then install` for `design-taste-frontend` only. Source-list found 12 skills at audited HEAD `60c2de19766019297287bd26a260275e499789a9`; the repository has MIT licensing and strong public adoption, but the bundle overlaps existing design/image-generation workflows and includes style variants, Google Stitch rules, and output-behavior overrides that should not be curated by default.

## Harness Coverage Strategy

- First discover exact Skills CLI target IDs from current CLI help/source-list output.
- Use `harness-master` to inspect project and global harness surfaces for the requested target list.
- Prefer native `npx skills add ... -a <agent>` installs where adapters exist.
- Normalize aliases only when backed by tool output or repository conventions.
- For unsupported harnesses, record the exact command output or inspected configuration evidence and report manual follow-up paths if available.
- Do not reduce coverage to the previous six-agent target suffix unless discovery proves those are the only supported adapters.

## Discovered Harness Mapping

Current repo code exposes these Skills CLI-supported target IDs through `wagents.site_model.SUPPORTED_AGENT_IDS` and `wagents skills sync`: `antigravity`, `claude-code`, `codex`, `crush`, `cursor`, `gemini-cli`, `github-copilot`, and `opencode`.

For the requested harness set, use these install targets in the next execution pass:

- `claude-code` -> `claude-code`
- `codex` -> `codex`
- `github-copilot-web` -> `github-copilot` aggregate target, with web facet reported separately
- `github-copilot-cli` -> `github-copilot` aggregate target, with CLI facet reported separately
- `cursor` and Cursor agent/web/CLI aliases -> `cursor`, with cloud/UI blind spots reported separately
- `gemini-cli` -> `gemini-cli`
- `antigravity` -> `antigravity`
- `opencode` -> `opencode`

No distinct Skills CLI install target is available for `claude-desktop`, `chatgpt`, `perplexity-desktop`, or `cherry-studio`. These must be reported as app/config surfaces rather than direct skills install adapters. `harness-master` discovery found present local surfaces for Claude Desktop config, ChatGPT desktop MCP config, Perplexity project skills, and Cherry Studio config/import packs, but their UI/cloud behavior remains partially blind-spot scoped.

## Curated Commands

Base command for `ctf-skills` after target discovery:

```bash
npx skills add ljagiello/ctf-skills --skill ctf-ai-ml --skill ctf-crypto --skill ctf-forensics --skill ctf-malware --skill ctf-misc --skill ctf-osint --skill ctf-pwn --skill ctf-reverse --skill ctf-web --skill ctf-writeup --skill solve-challenge -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

Base command for `ui-ux-pro-max-skill` after target discovery:

```bash
npx skills add nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

Base command for `taste-skill` after target discovery:

```bash
npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

## Alternatives Rejected

- Promote external skill contents into this repo: rejected because the existing curated external source preserves provenance and avoids taking ownership of third-party code.
- Install the whole `ui-ux-pro-max-skill` bundle: rejected because the `ckm:*` skills are not part of the approved install set and have broader overlap/risk.
- Install the whole `taste-skill` bundle: rejected because only `design-taste-frontend` fills the broadest design-taste gap; the other bundle members overlap existing UI, image-generation, Stitch, or output-behavior skills.
- Skip unsupported harness reporting: rejected because the user explicitly requested broad target coverage and unsupported results need evidence.
- Skip docs generation: rejected because external skill lists and target coverage are generated public surfaces.

## Compatibility Notes

- The existing parser already supports selected skill names with colons, so excluding `ckm:*` is a policy decision rather than a parser limitation.
- Existing dirty worktree changes may cause generated docs/README diffs unrelated to this change; keep reporting precise about what this implementation actually changed.
- If Skills CLI adapter names differ from the user's requested names, preserve both the requested name and the discovered adapter name in the final report.
