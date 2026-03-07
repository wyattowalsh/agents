# Memory Leak Patterns

Common memory leak patterns by language with detection heuristics.

## Contents

1. [Python](#python)
2. [JavaScript / TypeScript](#javascript--typescript)
3. [Go](#go)
4. [Java / JVM](#java--jvm)
5. [Cross-Language Patterns](#cross-language-patterns)

---

## Python

| Pattern | Detection Heuristic | Example |
|---------|-------------------|---------|
| **Circular references with __del__** | Class with `__del__` referencing objects that reference it back | Objects in reference cycles with custom finalizers |
| **Global / module-level accumulation** | Module-level list/dict with `.append()` but no cleanup | `_cache = []` at module level, appended in function |
| **Closure-captured large objects** | Inner function referencing outer scope variables | Lambda or nested function capturing DataFrame/large dict |
| **Forgotten threading.Timer** | `Timer` created but not cancelled on shutdown | `Timer(interval, func).start()` without cleanup |
| **Unclosed resources** | File/DB connection opened without context manager | `open()` without `with`, cursor without `close()` |
| **Lru_cache unbounded** | `@lru_cache` without maxsize on methods | `@lru_cache(maxsize=None)` with growing key space |
| **Signal handler accumulation** | `signal.signal()` called repeatedly | Signal handler registration in loop |
| **C extension leaks** | ctypes/cffi without proper cleanup | `ctypes.create_string_buffer()` without deallocation |

## JavaScript / TypeScript

| Pattern | Detection Heuristic | Example |
|---------|-------------------|---------|
| **Event listener accumulation** | `addEventListener` without matching `removeEventListener` | Event registration in component mount without cleanup |
| **SetInterval without clear** | `setInterval()` without matching `clearInterval()` | Timer set in constructor, never cleared |
| **Detached DOM nodes** | Reference to DOM node after removal | Variable holds element reference after `removeChild()` |
| **Closure scope retention** | Closure capturing variables larger than needed | Callback referencing entire scope when only one var needed |
| **Map/Set as cache without eviction** | `new Map()` with `.set()` but no `.delete()` | Growing Map used as cache without size limit |
| **Promise accumulation** | Promises created but never awaited or caught | `fetch()` calls without await in loop |
| **Observable subscription leak** | `.subscribe()` without `.unsubscribe()` | RxJS subscription in Angular component without teardown |
| **WeakRef misuse** | Using Map where WeakMap is appropriate | Caching objects by reference using strong Map |

## Go

| Pattern | Detection Heuristic | Example |
|---------|-------------------|---------|
| **Goroutine leak** | Goroutine blocked on channel with no sender/receiver | `go func()` reading from channel that is never closed |
| **Slice header retention** | Sub-slice prevents GC of underlying array | `large[5:10]` keeps entire backing array alive |
| **Time.After in loop** | `time.After()` creates new timer each iteration | `select { case <-time.After(d):` in for loop |
| **Finalizer reference cycle** | `runtime.SetFinalizer` on objects in a cycle | Finalizer prevents garbage collection of cycle |
| **Sync.Pool misuse** | Pool items growing unbounded or holding references | Pool storing items that reference large external state |
| **Context leak** | `context.WithCancel()` without calling cancel | Context created but cancel function never called |
| **HTTP body not closed** | `http.Get()` without `resp.Body.Close()` | Response body left open, connection not recycled |

## Java / JVM

| Pattern | Detection Heuristic | Example |
|---------|-------------------|---------|
| **Static collection growth** | `static List/Map` with add but no remove | `static final Map<K,V> cache = new HashMap<>()` |
| **Inner class reference** | Non-static inner class holding outer reference | Anonymous inner class preventing outer GC |
| **ThreadLocal accumulation** | ThreadLocal not removed in thread pools | `threadLocal.set(value)` without `remove()` in finally |
| **Classloader leak** | Redeployed webapp with static references | Static field referencing class from old classloader |
| **Stream not closed** | `Files.lines()` or JDBC ResultSet not closed | Stream opened without try-with-resources |
| **Listener registration** | Observer pattern without deregistration | `addPropertyChangeListener()` without matching remove |
| **StringBuilder reuse** | StringBuilder grown large, kept, reused | `sb.setLength(0)` preserves allocated capacity |

## Cross-Language Patterns

| Pattern | Languages | Key Indicator |
|---------|-----------|--------------|
| **Unbounded cache** | All | Cache/map with add, no eviction, no TTL |
| **Resource handle leak** | All | Open/acquire without close/release in finally |
| **Event listener accumulation** | JS, Java, C# | Register without deregister |
| **Goroutine/thread leak** | Go, Java, Python | Spawned workers never terminated |
| **Circular references** | Python, JS (older engines) | Mutual references between objects with custom cleanup |
| **Global state accumulation** | All | Module/static variables that grow over application lifetime |
