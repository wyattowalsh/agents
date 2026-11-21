# Organization Strategies

Start from a bounded proposal. Preserve ownership/dependency units and leave
unmatched files in place. Future files do not inherit approval from a previous
successful preview.

## Contents

1. Rule safety
2. Supported literal proposals
3. Projects, sidecars, and collisions
4. Bounded watch observations
5. Future automation gates

## Rule Safety

`organize sim` is not an unconditional safety boundary. organize 3.4.0 permits a
shell action with `run_in_simulation: true`; custom Python or template logic can
also be executable. Never feed arbitrary imported YAML directly into sim or run.

The bundled validator accepts a deliberately small proposal language:

- One explicitly named scope root per rule.
- A literal extension-list filter.
- One move/copy **proposal** with a destination inside that root.
- Only `{name}` and `{extension}` placeholders; no expressions or format access.

It rejects shell, Python, custom or deletion actions, custom filters, extra
settings, expression/escaped-brace templates, traversal, extra locations, and
symlink destination directories. It does not launch organize, simulate an
arbitrary program, or confer permission to execute the resulting proposals.

```bash
python scripts/storage-audit.py validate-rules rules.yml --root "$HOME/Downloads"
```

JSON requires no extra parser dependency. YAML uses declared PyYAML `safe_load`,
then the same closed allowlist. Passing YAML syntax validation alone is not
passing the rule safety boundary.

## Supported Literal Proposals

Replace `/Users/example/Downloads` with the exact selected root:

```yaml
rules:
  - name: Images for review
    locations:
      - /Users/example/Downloads
    filters:
      - extension: [jpg, jpeg, png, webp]
    actions:
      - move: Images/{name}.{extension}
  - name: Documents for review
    locations:
      - /Users/example/Downloads
    filters:
      - extension: [pdf, txt, docx]
    actions:
      - move: Documents/{name}.{extension}
```

The validator emits normalized rules with `execution_allowed: false`. Resolve
rules against the bounded metadata inventory, preserve dependency exclusions,
construct exact mappings, and check destinations before proposing an executor
plan. Date buckets require an explicit mapping derived from known metadata;
arbitrary `{created.year}` expressions are outside this restricted language.

Broad category suggestions are useful for an inbox: images, video, audio,
documents, spreadsheets, and archives. They are not a reason to reorganize
code, DAW projects, libraries, model stores, or app-owned folders by extension.

## Projects, Sidecars, and Collisions

Treat a directory as a project/dependency unit when metadata markers include
`.git`, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, or
`CMakeLists.txt`. Preserve Photos/Music libraries, Logic/DAW packages, sample
libraries, VM bundles, and associated sidecars. A `.env` marker signals
sensitive context; do not inspect its contents to classify it.

Check existing destinations and duplicate mappings, including case and Unicode
collisions. No overwrite is allowed. If suffixes are needed, show their exact
final names in the reviewed plan. Do not choose a new suffix after approval or
silently pull new files into an old count-based preview.

## Bounded Watch Observations

The implemented watch mode is a finite foreground metadata observer:

```bash
python scripts/storage-audit.py watch "$HOME/Downloads" \
  --database "$HOME/.files-buddy/runs/inbox-watch/inventory.sqlite" \
  --cycles 3 --interval 2
```

It records changed-entry counts and identifies eligible files with unchanged
object/version metadata in at least two consecutive snapshots, then exits. It does
not launch a daemon, run organizing rules, move files, install `watchexec` or
`pueue`, or persist standing mutation approval. Budgets, cloud/hidden policy,
non-following paths, dependency exclusions, and partial coverage are identical
to the normal scanner. Each pass revalidates file metadata. Settled candidates are review proposals,
not executable plans. If exported rows are capped, settlement coverage is
explicitly partial and unseen files are never called settled. A file that
appears stable in two observations still needs fresh preconditions before any
later approved operation.

## Future Automation Gates

An autonomous watcher is a separate capability. Before enabling it, require an
explicit standing policy with exact roots, allowed rule/version digest, file/
byte budgets, expiry, revocation, settled-file criteria, collision handling,
stop/resume behavior, and common-executor ownership of each mutation. A prior
simulation cannot authorize arbitrary future paths or modified rules. Keep it
proposal-only until those controls and native acceptance evidence exist.

The source-reviewed hazard is documented in [organize v3.4.0 shell action](https://github.com/tfeldmann/organize/blob/v3.4.0/organize/actions/shell.py).
