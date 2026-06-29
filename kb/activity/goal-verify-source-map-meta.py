#!/usr/bin/env python3
"""Source-map metadata alignment check for goal-verify.sh."""
from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    text = Path("kb/indexes/source-map.md").read_text()
    rows = len([line for line in text.splitlines() if re.match(r"\| `[^`]+` \| `raw/", line)])
    source_count = int(re.search(r"source_count: (\d+)", text).group(1))
    print(f"source_count={source_count} data_rows={rows} aligned={source_count == rows}")


if __name__ == "__main__":
    main()