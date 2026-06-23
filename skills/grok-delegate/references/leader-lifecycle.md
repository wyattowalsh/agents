# Leader pool lifecycle

Use when the graph has many nodes against one repo cwd and cold-start latency matters.

## Start

```bash
grok agent leader --no-exit-on-disconnect --no-auto-update
```

## Client attachment

Per `grok agent --help`, clients use `--leader` to connect to the shared leader instead of spawning a new agent backend.

Custom socket:

```bash
grok agent leader --leader-socket ~/.grok/leader-myrepo.sock --no-exit-on-disconnect --no-auto-update
```

## Health

```bash
grok leader list
grok leader info
```

## Stop

```bash
grok leader kill
```

## When not to use

- Single-shot `-p` nodes with long gaps between waves
- Nodes targeting different `cwd` values (separate leaders per cwd if needed)