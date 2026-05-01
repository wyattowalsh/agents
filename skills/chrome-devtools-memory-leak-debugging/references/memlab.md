# Using Memlab

[Memlab](https://facebook.github.io/memlab/) analyzes heap snapshots and reports retainer traces.

## Rule

Never read raw `.heapsnapshot` files directly. Use tools that summarize them.

## Three-Snapshot Workflow

1. Baseline: before the suspected action.
2. Target: after repeating the suspected action.
3. Final: after reverting the action.

```bash
npx memlab find-leaks --baseline <baseline.heapsnapshot> --target <target.heapsnapshot> --final <final.heapsnapshot>
```

Analyze a single snapshot only when a leak workflow is unavailable:

```bash
npx memlab analyze snapshot --snapshot <snapshot.heapsnapshot>
```

Report only bounded summaries and retainer traces relevant to the suspected leak.
