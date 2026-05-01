# Skills CLI Lifecycle

## Objective

Define the preferred skill management flow around `npx skills` unless a better official path is available for a harness.

## Commands to model

- install skill.
- update skill.
- remove skill.
- list installed skills.
- validate skill.
- inspect skill metadata.
- pin skill source/ref.
- export lockfile.
- audit external skill.

## Planned `wagents` wrappers

```bash
wagents skill search <query>
wagents skill add <source> --pin <ref> --agent <agent>
wagents skill validate <path-or-id>
wagents skill audit <id>
wagents skill sync --preview
wagents skill sync --apply
wagents skill rollback <transaction-id>
```

## Safety requirements

- Preview external source and license before install.
- Persist exact source/ref/checksum in lockfile.
- Refuse to run unknown scripts unless policy allows.
- Support telemetry opt-out passthrough where underlying CLI supports it.
