# Performance Anti-Patterns

Catalog of common performance anti-patterns with detection heuristics.

## Contents

1. [Query Anti-Patterns](#query-anti-patterns)
2. [Algorithmic Anti-Patterns](#algorithmic-anti-patterns)
3. [Memory Anti-Patterns](#memory-anti-patterns)
4. [I/O Anti-Patterns](#io-anti-patterns)
5. [Concurrency Anti-Patterns](#concurrency-anti-patterns)

---

## Query Anti-Patterns

| Pattern | Description | Detection | Fix |
|---------|-------------|-----------|-----|
| **N+1 queries** | Loop issues 1 query per item after initial list query | Loop containing DB call; ORM lazy loading in iteration | Eager load / JOIN / batch query |
| **SELECT *** | Fetching all columns when only few needed | `SELECT *` or ORM without `.only()` / `.values()` | Select specific columns |
| **Missing index** | Full table scan on filtered/sorted column | `WHERE` or `ORDER BY` on unindexed column | Add index; check EXPLAIN |
| **Over-fetching** | Loading large result sets into memory | No LIMIT, unbounded queries | Paginate, stream, or limit |
| **Repeated queries** | Same query executed multiple times per request | Identical queries in logs | Cache result or restructure |

## Algorithmic Anti-Patterns

| Pattern | Description | Detection | Fix |
|---------|-------------|-----------|-----|
| **Quadratic loop** | Nested iteration over same collection | Double `for` over same list/array | Use set/dict for O(1) lookup |
| **Linear search** | `x in list` in a loop | Membership check on list/array | Convert to set |
| **Repeated sorting** | Sort called inside loop | `sorted()` or `.sort()` in loop body | Sort once outside loop |
| **String concatenation** | `str += str` in loop | `+=` on string in loop | Use `join()` or `StringIO` |
| **Redundant computation** | Same expensive result computed multiple times | Identical expression in loop or branches | Memoize or hoist out of loop |
| **Premature materialization** | `list()` on generator before lazy consumption | `list(generator)` when iterator suffices | Use generator/iterator directly |

## Memory Anti-Patterns

| Pattern | Description | Detection | Fix |
|---------|-------------|-----------|-----|
| **Unbounded collection** | List/dict grows without limit over lifetime | `.append()` in loop without cleanup | Bound with maxlen or eviction |
| **Large object copy** | Deep copy of large structures in hot path | `copy.deepcopy()` on large objects | Use immutable structures or share references |
| **Holding references** | Keeping references to large objects beyond need | Variables referencing large data after use | Set to None / use weak references |
| **Buffer bloat** | Pre-allocating oversized buffers | Large array allocation "just in case" | Size buffers to actual need |
| **Accumulator pattern** | Results accumulated in memory instead of streamed | Building full list before writing output | Stream/yield results |

## I/O Anti-Patterns

| Pattern | Description | Detection | Fix |
|---------|-------------|-----------|-----|
| **Sequential I/O** | Independent I/O operations run one after another | Multiple `await fetch()` in sequence | Use `asyncio.gather()` or concurrent futures |
| **Chatty protocol** | Many small requests instead of batch | Loop containing HTTP/RPC calls | Batch API, bulk endpoints |
| **Missing connection pool** | New connection per request | `connect()` in request handler | Use connection pool |
| **Synchronous I/O in async** | Blocking call in async context | `open()`, `requests.get()` in async function | Use async I/O libraries |
| **Unbuffered I/O** | Writing byte-by-byte instead of buffered | File write in tight loop without buffering | Buffer writes, flush periodically |
| **Missing compression** | Large payloads sent uncompressed | Large response bodies without Content-Encoding | Enable gzip/brotli |

## Concurrency Anti-Patterns

| Pattern | Description | Detection | Fix |
|---------|-------------|-----------|-----|
| **Lock contention** | Broad locks serializing parallel work | Global lock, lock around large block | Fine-grained locks, lock-free structures |
| **Thread per request** | Unbounded thread creation | `Thread()` in request handler | Thread pool with bounded size |
| **Busy wait** | Polling in tight loop | `while not ready: pass` | Use events, condition variables |
| **False sharing** | Cache line contention between threads | Adjacent fields modified by different threads | Pad structures to cache line boundaries |
| **GIL bottleneck** | CPU-bound Python with threading | `threading` for compute work | Use multiprocessing or C extension |
