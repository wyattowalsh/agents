# Install Guidance

## When To Surface Install Commands

Surface install commands only when one of these is true:

1. the user explicitly asks how to install `harness-master`
2. the dry-run review concludes that missing skill installation is the actual root cause
3. the user asks for global rollout across one or more harnesses

Do **not** surface install commands for native config problems such as:

- stale `CLAUDE.md` or `AGENTS.md`
- broken `opencode.json`
- MCP config drift in native harness files

## Canonical Surfaced Form

Use this order exactly when you show the command:

```bash
npx skills add <source> --skill harness-master -y -g --agent claude-code --agent codex --agent crush --agent cursor --agent opencode
```

This is the complete Skills CLI target set. Grok uses the dedicated wagents
sync and mirror route because Skills CLI has no native Grok adapter.

## Per-Harness Commands

```bash
npx skills add <source> --skill harness-master -y -g --agent claude-code
npx skills add <source> --skill harness-master -y -g --agent codex
npx skills add <source> --skill harness-master -y -g --agent crush
npx skills add <source> --skill harness-master -y -g --agent cursor
npx skills add <source> --skill harness-master -y -g --agent opencode
```

Cursor Agent CLI (`cursor-cli`) consumes the same Skills CLI projection as the editor. Keep `--agent cursor` (`-a cursor`). Do not recommend `-a cursor-cli`.

No Skills CLI install command is available for these config-only or UI-managed harnesses:

- `claude-desktop`
- `chatgpt`
- `perplexity-desktop`
- `cherry-studio`

For this repository's published collection, the likely source is:

```bash
npx skills add wyattowalsh/agents --skill harness-master -y -g --agent claude-code --agent codex --agent crush --agent cursor --agent opencode
```

If the skill is not being installed from that source, replace `<source>` with the actual published source.

Build install commands without executing them:

```bash
python skills/harness-master/scripts/install_skills.py harness-master --dry-run -a <agent>
```

## Project-Local Install Guidance

Do not suggest project-local install by default.

If the user explicitly asks for project-local installation, mention:

```bash
python skills/harness-master/scripts/install_skills.py harness-master --local --execute -y
```

Do not invent an `npx skills add --local` form.

## Approval Gate For Install Steps

If installation is part of an approved remediation batch, it may be executed during `Apply Approved`.

If installation was not reviewed in the dry-run report, do not run it during apply.
