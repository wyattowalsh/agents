# Design

## Evidence and scope gate

Every inherited finding is re-run against the live tree and classified as
`open`, `already-fixed`, `duplicate`, `invalid`, or `out-of-scope`. Only `open`
findings receive implementation nodes. Focused test success does not close a
runtime-contract finding when the test double accepts a call the real dependency
rejects.

## Source URL health

Construct one `httpx.Client` with TLS verification enabled,
`trust_env=False`, and redirects disabled. Requests never pass unsupported
client-construction options. Validate and canonicalize the logical URL, resolve
all A/AAAA answers, reject every non-global address, pin each connection to an
approved address while retaining logical Host/SNI identity, and re-run the full
policy after every redirect.

The caller-provided timeout is tracked as one monotonic best-effort budget across
resolution, connect attempts, method fallback, and redirects. Every phase and
new attempt receives only the remaining budget, and no new attempt starts after
expiry. Python's synchronous system resolver cannot be preempted portably, so a
single blocked `getaddrinfo` call can exceed the wall-clock budget; the public
contract documents that limitation instead of claiming a hard total deadline.
The fallback GET is streamed, range-limited, and closed without consuming an
unbounded body. A resolver subprocess boundary is deliberately omitted because
the supported API remains synchronous and no deterministic resolver-hang
requirement justifies that added process lifecycle.

The wheel contains a collision-resistant `mcp_source_url_health` package with
the server and SSRF policy modules, retains the repository FastMCP root entry
convention through a thin wrapper, has no workspace-only runtime dependency,
and is covered by the root lint/type configuration.

## Skill archives

Collection uses no-follow `lstat` semantics and rejects symlinks, POSIX hard
links, Windows junction/reparse points, special files, traversal, absolute
paths, duplicate normalized names, case-fold collisions, control characters,
NTFS alternate-data-stream separators, and Windows device or trailing-dot/space
aliases. Limits for file count, depth, individual bytes, and total bytes are
constants derived from the current corpus inventory with documented headroom
and hard ceilings. Manifest string fields are bounded, and the generated
manifest bytes count toward the total archive ceiling.

All source and vendored members are staged first. `manifest.json` is computed
from that exact final member set with POSIX paths, then the archive is written in
deterministic member order and metadata; valid `SOURCE_DATE_EPOCH` makes both
the manifest timestamp and ZIP byte-reproducible. Publication uses a temporary
sibling, file fsync, atomic replacement, and parent-directory fsync. Portable
packages exclude `AGENTS.md` and machine/cache/build artifacts.

Toolkit reconciliation validates every requested selector and all destinations
before writing anything, rejects link/reparse targets, stages atomic sibling
replacements, revalidates each destination snapshot immediately before replace,
and fsyncs destination directories. Concurrently changed or newly created
destinations fail closed without overwriting user work. Existing toolkit directories
must match the exact supported module allowlist; partial or unknown module
selectors fail closed. Packaging automatically vendors all seven supported
toolkit modules rather than treating any existing toolkit directory as proof of
completeness.

## Eval ownership

`evals/evals.json` remains the Nerdbot canonical manifest. It explicitly lists
the per-case projection filenames it owns. The collector counts canonical cases
once and skips only those declared, validated projections; unrelated legacy JSON
files and skills without this metadata keep their current behavior. Validation
requires exact one-to-one filename/ID, skill, prompt/query, input-file, and
expected-behavior/assertion parity and the exact supported projection field set.
It rejects malformed/non-object JSON plus missing, extra, duplicated, or
behavior-drifted projections; inventory never suppresses a projection unless
that same closed-world contract passes.

## Nerdbot audit consistency

The JSONL operation journal is canonical. IDs use a deterministic intent prefix
and unique suffix. Every persisted operation starts with `prepared` and ends
with exactly one immutable-payload `committed`, `failed`, or `review-needed`
transition; `planned` exists only in memory. A project-scoped cross-platform OS
lock covers the entire prepare, workflow mutation, terminal transition, and
activity-projection batch without nested lock acquisition.

The shared strict parser rejects invalid IDs/enums/timezones/paths/scalars,
terminal-first records, duplicate prepare or terminal rows, payload mutation,
and transitions after terminal state. Persisted scalars also reject Unicode
line and paragraph separators, and marker extraction recognizes only ASCII
newline-delimited standalone records. Only committed operations project, using
an exact standalone HTML marker so marker-like prose cannot forge completion or
suppress projection repair. Replay exposes canonical `operation_state`
separately from its derived `status`.

Crash-injection tests cover every ingest mutation boundary, committed-before-
projection repair, and an enrich boundary. Abrupt `BaseException` interruption
leaves a resumable prepared intent; ordinary mutation exceptions record failed
and a later retry reconciles byte-identical/append-only residue under a new
suffix. No hash chain or implicit legacy `applied` fallback is added. A fully
durable commit and marker followed by a lost client response remains outside
automatic semantic deduplication because the CLI has no caller idempotency token;
the underlying data and append rows remain reconciled.

## Versioning and generation

The skill metadata version is monotonic from committed `1.0.0`; this feature and
security release becomes `1.1.0`. The Python runtime keeps its separate stream
and becomes `0.2.0` if its public operation/eval behavior changes. Canonical
toolkit source is updated first, eligible bundled copies are synchronized by the
repo tool, and generated docs/catalog surfaces run only after zero active source
writers.
