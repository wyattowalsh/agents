# Complexity Patterns

Code pattern to Big-O mapping with examples.

## Contents

1. [Constant O(1)](#constant-o1)
2. [Logarithmic O(log n)](#logarithmic-olog-n)
3. [Linear O(n)](#linear-on)
4. [Linearithmic O(n log n)](#linearithmic-on-log-n)
5. [Quadratic O(n^2)](#quadratic-on2)
6. [Cubic O(n^3)](#cubic-on3)
7. [Exponential O(2^n)](#exponential-o2n)
8. [Common Traps](#common-traps)

---

## Constant O(1)

- Hash table lookup (dict/set access)
- Array index access
- Stack push/pop
- Arithmetic operations

```python
# O(1) — dict lookup
value = cache[key]
```

## Logarithmic O(log n)

- Binary search
- Balanced BST operations
- Bisect/lower_bound
- Exponentiation by squaring

```python
# O(log n) — binary search
idx = bisect.bisect_left(sorted_list, target)
```

## Linear O(n)

- Single loop over collection
- Linear search
- List comprehension (single generator)
- String concatenation in a loop (amortized)

```python
# O(n) — single pass
total = sum(x for x in items)
```

## Linearithmic O(n log n)

- Comparison-based sorting (sorted, sort)
- Merge sort, quicksort (average)
- Heap construction + n extractions

```python
# O(n log n) — sorting
result = sorted(items, key=lambda x: x.score)
```

## Quadratic O(n^2)

- Nested loops over same collection
- Bubble sort, insertion sort, selection sort
- Nested list comprehension
- String building with `+=` in some languages

```python
# O(n^2) — nested iteration
for i in items:
    for j in items:
        if i.key == j.key:
            process(i, j)
```

## Cubic O(n^3)

- Triple nested loops
- Matrix multiplication (naive)
- Floyd-Warshall shortest paths

```python
# O(n^3) — matrix multiply
for i in range(n):
    for j in range(n):
        for k in range(n):
            C[i][j] += A[i][k] * B[k][j]
```

## Exponential O(2^n)

- Recursive subset generation
- Naive recursive Fibonacci
- Brute-force combinatorial search
- Power set generation

```python
# O(2^n) — recursive without memoization
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
```

## Common Traps

| Pattern | Appears | Actually |
|---------|---------|----------|
| `x in list` | O(1) | O(n) — use set for O(1) |
| `list.insert(0, x)` | O(1) | O(n) — use deque |
| `str += char` in loop | O(n) | O(n^2) in some impls — use join |
| `sorted()` in a loop | O(n log n) | O(n^2 log n) total |
| `dict.items()` filter | O(1) | O(n) — full iteration |
| Recursive without memo | O(n) | Often O(2^n) |
| `.count()` in loop | O(n) | O(n^2) — use Counter |
| Regex in loop | O(n) | O(n * m) — compile once |

**Data structure operation costs:**

| Operation | list | deque | set | dict |
|-----------|------|-------|-----|------|
| Append | O(1)* | O(1) | — | — |
| Prepend | O(n) | O(1) | — | — |
| Lookup | O(n) | O(n) | O(1)* | O(1)* |
| Delete | O(n) | O(n) | O(1)* | O(1)* |
| Insert(i) | O(n) | O(n) | O(1)* | O(1)* |
| Sort | O(n log n) | — | — | — |

*Amortized
