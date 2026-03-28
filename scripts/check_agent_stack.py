#!/usr/bin/env python3
from __future__ import annotations

import sys

from sync_agent_stack import main as sync_main

if __name__ == "__main__":
    raise SystemExit(sync_main(["--check", "--targets", "all", *sys.argv[1:]]))
