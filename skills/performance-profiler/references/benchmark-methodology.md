# Benchmark Methodology

Best practices for designing and interpreting benchmarks.

## Contents

1. [Design Principles](#design-principles)
2. [Statistical Methods](#statistical-methods)
3. [Common Pitfalls](#common-pitfalls)
4. [Environment Control](#environment-control)
5. [Reporting Standards](#reporting-standards)

---

## Design Principles

1. **Measure what matters.** Benchmark the actual operation, not setup/teardown.
2. **Use representative data.** Synthetic data masks real-world behavior.
3. **Warmup before measuring.** JIT compilation, cache warming, lazy initialization.
4. **Multiple iterations.** Single runs are noise, not signal.
5. **Control the environment.** Same machine, same load, same data.

**Benchmark structure:**

```
1. Setup (excluded from measurement)
2. Warmup (N iterations, discarded)
3. Measurement (M iterations, recorded)
4. Teardown (excluded from measurement)
5. Statistical analysis of M results
```

## Statistical Methods

| Metric | When to Use | Formula |
|--------|-------------|---------|
| **Mean** | Throughput benchmarks | sum(times) / n |
| **Median (p50)** | Latency benchmarks (robust to outliers) | middle value |
| **p95 / p99** | Tail latency (SLA-critical) | value at 95th/99th percentile |
| **Min** | Best-case performance (cache-hot, JIT-warm) | smallest value |
| **Stddev** | Measurement stability | sqrt(variance) |
| **CV (coefficient of variation)** | Comparing stability across benchmarks | stddev / mean |

**Minimum iterations:** For statistical significance, run until:
- CV < 5% (stable results) OR
- At least 30 iterations (Central Limit Theorem) OR
- p95 confidence interval width < 10% of mean

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| **No warmup** | First runs include JIT/cache cold start | Discard first N iterations |
| **Optimized away** | Compiler removes unused computation | Use result (assign, return, volatile) |
| **Microbenchmark fallacy** | Function fast in isolation, slow in context | Benchmark at integration level too |
| **Clock resolution** | Operation faster than timer resolution | Batch N operations per measurement |
| **GC pauses** | GC introduces variance | Force GC between iterations or exclude GC time |
| **Power management** | CPU throttling during benchmark | Pin CPU frequency, disable turbo boost |
| **System load** | Other processes interfere | Use dedicated machine, measure system load |
| **Caching effects** | Repeated access warms caches unrealistically | Vary input data between iterations |

## Environment Control

**Checklist before running benchmarks:**

- [ ] Close unnecessary applications
- [ ] Disable CPU frequency scaling (if possible)
- [ ] Pin process to specific CPU cores (taskset/numactl)
- [ ] Disable swap (or ensure sufficient RAM)
- [ ] Record system info: CPU model, RAM, OS version, runtime version
- [ ] Run multiple times on different occasions
- [ ] Compare against baseline (previous version, not absolute numbers)

## Reporting Standards

**Minimum reporting requirements:**

1. **What was measured:** Function/operation, input size, data characteristics
2. **Environment:** Hardware, OS, runtime version, configuration
3. **Methodology:** Iterations, warmup, statistical method
4. **Results:** Mean/median, variance, percentiles (p50/p95/p99)
5. **Baseline:** What is this compared against

**Example report format:**

```
Benchmark: sort_large_list (n=10000, random integers)
Environment: Python 3.12, M2 MacBook Pro, 16GB RAM
Warmup: 100 iterations
Measured: 1000 iterations, 5 repeats

Results (ms/call):
  Mean:   1.234
  Median: 1.198
  p95:    1.456
  p99:    1.789
  Stddev: 0.123
  CV:     9.97%

Baseline (previous version): Mean 1.567 ms/call
Improvement: 21.3%
```
