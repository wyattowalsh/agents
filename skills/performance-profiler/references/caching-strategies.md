# Caching Strategies

Decision tree for cache design: eviction policy, write policy, invalidation.

## Contents

1. [Decision Tree](#decision-tree)
2. [Eviction Policies](#eviction-policies)
3. [Write Policies](#write-policies)
4. [Invalidation Strategies](#invalidation-strategies)
5. [Capacity Planning](#capacity-planning)
6. [Anti-Patterns](#cache-anti-patterns)

---

## Decision Tree

```
Is data read-heavy (>80% reads)?
  YES -> Is working set stable?
    YES -> LFU (frequency-based eviction)
    NO  -> LRU (recency-based eviction)
  NO  -> Is consistency critical?
    YES -> Write-through + TTL
    NO  -> Write-back + TTL

Is data time-sensitive?
  YES -> TTL mandatory. Set TTL = max acceptable staleness.
  NO  -> Eviction-only (LRU/LFU without TTL)

Is cache shared across instances?
  YES -> Distributed cache (Redis/Memcached) + invalidation protocol
  NO  -> In-process cache (dict/LRU decorator)
```

## Eviction Policies

| Policy | Best For | Trade-off |
|--------|----------|-----------|
| **LRU** (Least Recently Used) | General purpose, unknown access patterns | Bad for scan workloads (one-time reads evict useful entries) |
| **LFU** (Least Frequently Used) | Stable hot sets, CDN, static assets | Slow to adapt to changing access patterns |
| **TTL** (Time-To-Live) | Time-sensitive data, sessions, tokens | Requires tuning; too short = cache thrashing, too long = stale data |
| **FIFO** (First In First Out) | Simple caches, streaming data | Ignores access patterns entirely |
| **Random** | Uniform access, when simplicity matters | Unpredictable behavior under skewed access |
| **LRU-K** | Database buffer pools | Higher metadata overhead |
| **ARC** (Adaptive Replacement) | Self-tuning, mixed workloads | Patent concerns (IBM), complex implementation |

## Write Policies

| Policy | Consistency | Latency | Failure Mode |
|--------|-------------|---------|-------------|
| **Write-through** | Strong | Higher write latency (cache + store) | Safe — data always in backing store |
| **Write-back** | Eventual | Lower write latency (cache only) | Data loss on cache failure |
| **Write-around** | Eventual | Cache miss on next read | Cold cache after writes |
| **Write-behind** | Eventual | Lowest latency (async flush) | Data loss window = flush interval |

## Invalidation Strategies

| Strategy | When to Use | Complexity |
|----------|-------------|-----------|
| **TTL expiry** | Default choice. Set TTL = max staleness tolerance | Low |
| **Event-driven** | On write/update, publish invalidation event | Medium |
| **Version-based** | Include version in cache key; new version = new key | Low |
| **Tag-based** | Group related entries; invalidate by tag | Medium |
| **Purge on deploy** | Static assets, configuration | Low |
| **Cache-aside + stampede protection** | High-traffic keys with expensive recomputation | High |

**Stampede protection patterns:**
- Lock-based: acquire lock before recomputation, others wait
- Probabilistic early expiry: refresh before TTL with jitter
- Stale-while-revalidate: serve stale, recompute in background

## Capacity Planning

```
Required capacity = working_set_size * (1 + overhead_factor)
  overhead_factor = 0.2 for hash maps, 0.5 for ordered structures

Hit rate target: 95%+ for most applications
  Measure: hits / (hits + misses) over time window

Memory per entry = key_size + value_size + metadata (48-64 bytes)
  Total memory = entries * memory_per_entry

Eviction rate = (requests/sec * miss_rate) / cache_size
  High eviction rate = cache too small or wrong eviction policy
```

## Cache Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Cache everything | Memory bloat, low hit rate | Cache only hot-path data with measured benefit |
| No TTL on mutable data | Stale data served indefinitely | Always set TTL on mutable data |
| Cache stampede | Thundering herd on expiry | Use locking, jitter, or stale-while-revalidate |
| Inconsistent invalidation | Some paths update cache, others don't | Centralize cache invalidation logic |
| Cache as primary store | Data loss on eviction | Cache is derived — always have a source of truth |
| Unbounded cache | OOM risk | Set max size with eviction policy |
| Caching errors | Error responses served repeatedly | Never cache error responses (or use very short TTL) |
