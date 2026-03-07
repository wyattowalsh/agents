#!/usr/bin/env python3
"""Generate benchmark skeleton from function signature."""
from __future__ import annotations

import argparse
import json

TEMPLATES = {
    "python": {
        "setup": (
            "import timeit\n"
            "from {module} import {function}\n\n"
            "# Setup: create representative test data\n"
            "data = {setup_data}"
        ),
        "benchmark": '''def bench():
    """Benchmark {function} with representative data."""
    result = {function}({call_args})
    return result

# Warmup
for _ in range({warmup}):
    bench()

# Measure
times = timeit.repeat(bench, number={iterations}, repeat={repeats})
print(f"Mean: {{sum(times)/len(times)*1000/{iterations}:.4f}} ms/call")
print(f"Min:  {{min(times)*1000/{iterations}:.4f}} ms/call")
print(f"Max:  {{max(times)*1000/{iterations}:.4f}} ms/call")
print(f"Stddev: {{(sum((t-sum(times)/len(times))**2 for t in times)/len(times))**0.5*1000/{iterations}:.4f}} ms")''',
        "iterations": 1000,
        "warmup": 100,
        "repeats": 5,
    },
    "javascript": {
        "setup": (
            'const {{ {function} }} = require("{module}");\n\n'
            "// Setup: create representative test data\n"
            "const data = {setup_data};"
        ),
        "benchmark": '''// Warmup
for (let i = 0; i < {warmup}; i++) {{
  {function}({call_args});
}}

// Measure
const times = [];
for (let r = 0; r < {repeats}; r++) {{
  const start = performance.now();
  for (let i = 0; i < {iterations}; i++) {{
    {function}({call_args});
  }}
  times.push(performance.now() - start);
}}
const mean = times.reduce((a, b) => a + b) / times.length / {iterations};
console.log(`Mean: ${{mean.toFixed(4)}} ms/call`);
console.log(`Min:  ${{Math.min(...times) / {iterations}}} ms/call`);''',
        "iterations": 1000,
        "warmup": 100,
        "repeats": 5,
    },
}


def generate_skeleton(function: str, language: str, module: str = "__main__") -> dict:
    """Generate a benchmark skeleton for the given function."""
    tmpl = TEMPLATES.get(language, TEMPLATES["python"])
    setup_data = '[]  # TODO: replace with representative test data'
    call_args = 'data  # TODO: replace with actual arguments'

    setup_code = tmpl["setup"].format(
        module=module, function=function, setup_data=setup_data
    )
    benchmark_code = tmpl["benchmark"].format(
        function=function, call_args=call_args,
        warmup=tmpl["warmup"], iterations=tmpl["iterations"],
        repeats=tmpl["repeats"],
    )

    return {
        "function": function,
        "language": language,
        "module": module,
        "setup_code": setup_code,
        "benchmark_code": benchmark_code,
        "iterations": tmpl["iterations"],
        "warmup": tmpl["warmup"],
        "repeats": tmpl["repeats"],
        "expected_metrics": [
            "mean_time_per_call_ms",
            "min_time_per_call_ms",
            "max_time_per_call_ms",
            "stddev_ms",
        ],
        "methodology_notes": [
            "Replace setup data with representative production-scale input",
            "Adjust iterations based on function speed (fast=10000, slow=100)",
            "Run in isolated environment (no background processes)",
            "Compare across multiple runs for stability",
            "Report percentiles (p50, p95, p99) for latency-sensitive code",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark skeleton")
    parser.add_argument("--function", "-f", required=True, help="Function name to benchmark")
    parser.add_argument("--language", "-l", default="python",
                        choices=["python", "javascript"], help="Target language")
    parser.add_argument("--module", "-m", default="__main__", help="Module containing the function")
    args = parser.parse_args()

    result = generate_skeleton(args.function, args.language, args.module)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
