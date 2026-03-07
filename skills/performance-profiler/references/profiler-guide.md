# Profiler Output Interpretation Guide

How to read and interpret common profiler outputs.

## Contents

1. [cProfile / pstats](#cprofile--pstats)
2. [py-spy](#py-spy)
3. [Linux perf](#linux-perf)
4. [Flame Graphs](#flame-graphs)
5. [Interpretation Checklist](#interpretation-checklist)

---

## cProfile / pstats

**Column meanings:**

| Column | Meaning |
|--------|---------|
| `ncalls` | Number of calls. Format `x/y` means x total, y primitive (non-recursive) |
| `tottime` | Total time spent in this function alone (excludes subfunctions) |
| `percall` (1st) | `tottime / ncalls` |
| `cumtime` | Cumulative time including subfunctions |
| `percall` (2nd) | `cumtime / primitive_calls` |
| `filename:lineno(function)` | Source location |

**Reading strategy:**

1. Sort by `cumtime` for top-down view (which call trees are expensive)
2. Sort by `tottime` for bottom-up view (which functions consume CPU)
3. High `ncalls` + low `percall` = overhead candidate (reduce call count)
4. Low `ncalls` + high `percall` = optimization candidate (speed up function)
5. `cumtime >> tottime` = time is in subfunctions, not this function

**Red flags:**

- `ncalls` in thousands for what should be a single-call operation
- `cumtime` close to total program time = this is the critical path
- `tottime / cumtime` ratio near 1.0 = this function is the bottleneck, not its children

## py-spy

**Output format:** Percentage of samples where function was on stack.

- **Top of flame graph:** Functions where CPU is actually executing
- **Bottom of flame graph:** Call chain that led there
- **Wide bars:** More time spent (higher percentage of samples)
- **Narrow bars:** Less time spent

**Key insight:** py-spy samples the call stack at intervals. A function showing 30% means it was on the stack in 30% of samples — it may be executing or waiting for a child function.

## Linux perf

**Output columns:**

| Column | Meaning |
|--------|---------|
| `Overhead` | Percentage of total samples |
| `Command` | Process name |
| `Shared Object` | Library/binary containing the function |
| `Symbol` | Function name (may be mangled) |

**Key distinction:** perf samples hardware counters (CPU cycles, cache misses, branch mispredictions). Use `perf stat` for aggregate counters, `perf record` + `perf report` for per-function breakdown.

## Flame Graphs

**Reading flame graphs:**

1. X-axis = stack frame population (NOT time). Wider = more samples.
2. Y-axis = stack depth. Bottom = entry point, top = leaf function.
3. Alphabetical ordering within each level (NOT chronological).
4. Look for "plateaus" — wide flat sections indicate hotspots.
5. Narrow "towers" = deep call stacks with little time.

**Interactive features:**
- Click to zoom into a subtree
- Search to highlight matching frames
- Compare two flame graphs for regression analysis

## Interpretation Checklist

For any profiler output, answer these questions:

1. **What percentage of time is in user code vs framework/library code?**
   - High framework time = likely misconfiguration, not algorithm issue
2. **What are the top 3 functions by cumulative time?**
   - These define the critical path
3. **Are there functions with unexpectedly high call counts?**
   - May indicate N+1, retry loops, or redundant computation
4. **Is the program CPU-bound or I/O-bound?**
   - CPU-bound: tottime is high, optimize algorithms
   - I/O-bound: cumtime >> tottime (waiting for I/O), optimize I/O patterns
5. **Are there allocation-heavy functions?**
   - Look for `__init__`, `copy`, `deepcopy`, list/dict construction
6. **Is garbage collection visible in the profile?**
   - GC time > 5% of total = memory pressure issue
