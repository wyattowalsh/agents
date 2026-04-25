# Python Performance Quick-Reference

Use this reference for lightweight Python optimization guidance. Route profiling
plans, regression analysis, benchmark interpretation, caching architecture, or
multi-service performance work to `performance-profiler`.

## Profiling Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `cProfile` | CPU hotspots (function-level) | `uv run python -m cProfile -s cumulative script.py` |
| `py-spy` | Sampling profiler (no code changes) | `uv run py-spy top -- python script.py` |
| `line_profiler` | Line-by-line timing | Decorate with `@profile`, run with `kernprof -lv` |
| `memory_profiler` | Line-by-line memory | Decorate with `@profile`, run with `mprof run` |
| `tracemalloc` | Memory leak detection | `tracemalloc.start()` in code, snapshot and compare |

## Optimization Patterns

### Collections and Lookups

```python
# Prefer set/dict for membership (O(1) vs O(n))
valid_ids = set(load_ids())
if item_id in valid_ids: ...

# Prefer list comprehension over append loop
results = [transform(x) for x in items if x.valid]
```

### Memory

```python
# Generator for large datasets — constant memory
def read_chunks(path, size=8192):
    with open(path, "rb") as f:
        while chunk := f.read(size):
            yield chunk

# __slots__ for high-volume instances
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x, self.y = x, y
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def expensive_lookup(key: str) -> Result:
    ...
```

### Concurrency

| Pattern | Use when |
|---------|----------|
| `asyncio` / `aiohttp` | I/O-bound: HTTP calls, DB queries, file I/O |
| `multiprocessing.Pool` | CPU-bound: number crunching, image processing |
| `concurrent.futures.ThreadPoolExecutor` | Mixed I/O with GIL-releasing C extensions |

### Database

```python
# Batch inserts — avoid per-row commits
session.add_all(objects)
session.commit()

# Use executemany for raw SQL
cursor.executemany("INSERT INTO t (a, b) VALUES (?, ?)", rows)
```

### Strings

```python
# Join instead of += in loops
result = "".join(parts)  # O(n) total
# Not: result += part    # O(n^2) total
```
