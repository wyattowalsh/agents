# Runtime and Portable Package Contract

## Contents

1. Environment and entrypoints
2. Exact local plan workflow
3. Compatibility and legacy data
4. Validation and evidence

## Environment and Entrypoints

The skill is an independent Python 3.13 project. Its `pyproject.toml` and generated
`uv.lock` declare PyYAML for bundled asset/rule validation and a development group
for pytest, JSON Schema, Ruff, and ty. The core execution and inventory helpers
use the standard library. Install/sync only the environment the user has chosen;
never install optional OSS tools merely because a capability check finds them absent.

From the skill directory:

```bash
uv sync --locked
uv run python scripts/storage-audit.py --help
uv run python scripts/manifest-manager.py --help
uv run python scripts/dashboard-renderer.py --help
uv run python scripts/check.py --tests
```

| Helper | Contract |
| --- | --- |
| storage-audit | Metadata inventory, bounded duplicate review, versioned observations and safe-rule validation; no user-file mutations |
| manifest-manager | Exact local plans, contained state inspection, execution/reconciliation/reverse plans |
| dashboard-renderer | Validated reports, distinct HTML outputs, explicit refresh/import |
| check | Mandatory bundled validation/package gates; optional executable regressions |

Successful observations are not authorization. Content reads can hydrate files,
external tools may have auxiliary effects, and scanner/report/state outputs are
writes. The tool registry and each command's preview make these effects explicit.
Errors return nonzero; never judge success from a JSON field without checking the
process status. Standard argparse usage errors may print diagnostics to stderr.

## Exact Local Plan Workflow

Create a JSON array of exact absolute source/destination mappings:

```json
[
  {"type": "rename", "source": "<absolute source>", "destination": "<absolute destination>"}
]
```

The placeholders above must be replaced with paths in the explicitly selected
roots. The helper captures object evidence itself. It does not execute arbitrary
commands or accept arbitrary recorded completion rows.

```bash
uv run python scripts/manifest-manager.py plan \
  --mapping mapping.json --source-root "$source_root" \
  --destination-root "$destination_root" --intent "Reviewed local rename" --local-only
uv run python scripts/manifest-manager.py show "$manifest"
uv run python scripts/manifest-manager.py validate "$manifest"
uv run python scripts/manifest-manager.py report "$manifest"
```

Planning hashes selected local files and writes a private state document. The
local-only attestation must come from trusted context, including custom sync roots.
After displaying the exact mapping, digest, restrictions and recovery behavior,
obtain explicit consent. The trusted caller then passes the approved digest:

```bash
uv run python scripts/manifest-manager.py execute "$manifest" --approve "$approved_digest"
uv run python scripts/manifest-manager.py reconcile "$manifest"
uv run python scripts/manifest-manager.py undo "$manifest"
uv run python scripts/manifest-manager.py undo "$manifest" --approve "$approved_reverse_digest"
```

The first undo command previews; the second mutates only after separate approval.
An approved digest is a caller-supplied binding, not a cryptographic identity or
independent human-authentication system. Untrusted data must never choose it.
Public execute/undo commands refuse non-macOS mutation. Unit fixtures exercise
portable internals separately and do not expose a production bypass flag.

`--state-dir` precedes the subcommand and selects an explicit private coordination
root. A run has one canonical state document. Advisory locks on owned directory
identities also serialize overlapping target scopes across different state roots.
These locks coordinate cooperating invocations; they do not exclude unrelated
applications or make file and state writes one transaction. State location is
not permission to operate outside the approved target roots.

## Compatibility and Legacy Data

Version 2 replaces append-only-after-the-fact CRUD with exact plans and a lifecycle.
Version 1 persisted manifests remain read-only and retain their BLAKE3 semantics;
there is no automatic migration or digest relabelling. Replan current files for
new execution. A missing BLAKE3 verifier means unverified legacy evidence.

`list` and `search` return an object with `valid`, `results`, and `errors`.
Unreadable, corrupt, or unsupported regular state documents appear in `errors`
and produce a nonzero exit status while valid summaries remain available.
Symlink and nonregular discovery entries are not followed. A successful empty
result therefore does not conceal a discovered corrupt regular manifest.

The portable source intentionally has no `model` or `argument-hint` frontmatter.
The previous `sonnet` preference is removed in favor of the invoking harness's
configured model; invocation syntax is ordinary body text. This reconciles the
strict portable policy without inventing an unused global adapter registry.
Native field projection must be implemented and tested by its owning harness
before claiming native metadata preservation. The portable check enforces this
skill's source keys even if a general repository validator is more permissive.

Reported compatibility covers local package validation, not every target's
installation UI or permission model. Scripts do not bypass harness approvals.
No live skill sync, credential setup, provider configuration, or daemon is part
of installation validation.

## Validation and Evidence

`check.py` always executes its bundled skill validator, eval validator, and
packager. Missing bundled files and missing declared dependencies fail with
structured diagnostics. A repository-only structural audit is additional when
available; its absence in a portable package does not skip the bundled gates.

For maintainers in the source repository, the structural comparison command is:

```bash
uv run python skills/skill-creator/scripts/audit.py skills/files-buddy/
```

The audit recognizes portable `Input` dispatch tables and harness-neutral state
paths; a client-specific substitution token or per-harness directory is not a
prerequisite for those patterns.

Use `--tests` for executable regressions, including report truthfulness, malformed
data, scan/resume, adapters, safe rules, concurrency, interruption, stale approvals,
collisions, reverse plans, and standalone missing-reference failures. The root
repository CI invokes the portable test suite through a focused bridge test.
Natural-language evals describe model expectations; schema validation does not
mean those prompts have been run through a model.

For release evidence, distinguish Python/Linux fixtures, actual upstream CLI
invocations, native Mac metadata/provider tests, rendered browser/a11y checks,
and live model tool-call evaluations. Unsupported metadata/provider/restore
semantics stay rejected or report-only until their acceptance tests are run.

The dedicated Files Buddy CI runs the package on Python 3.13 for Linux and macOS,
and runs the rendered dashboard fixture in Chromium using the repository's
locked Playwright dependency. Browser screenshots are retained as CI artifacts.
The macOS tests exercise ordinary-file execution/reversal and refusal of ACLs
and extended attributes; they do not qualify every APFS, provider, or metadata
configuration. Native constants and ACL return handling are pinned to Apple's
[Libc ACL definitions](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/include/sys/acl.h),
[ACL entry implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/posix1e/acl_entry.c),
[ACL file implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/posix1e/acl_file.c),
and [exclusive rename definitions](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/sys/stdio.h).
