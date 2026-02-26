#!/usr/bin/env python3
"""
inbox-snapshot — Save an inbox stats snapshot for email-whiz analytics.

Usage:
  uv run python scripts/inbox_snapshot.py --inbox-count 12 --unread-count 5
  uv run python scripts/inbox_snapshot.py --list
  uv run python scripts/inbox_snapshot.py --trend 7

Writes snapshots to ~/.claude/email-whiz/snapshots.json.
Outputs JSON to stdout.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

SNAPSHOT_DIR = os.path.expanduser("~/.claude/email-whiz")
SNAPSHOT_FILE = os.path.join(SNAPSHOT_DIR, "snapshots.json")


def load_snapshots() -> list[dict]:
    if not os.path.exists(SNAPSHOT_FILE):
        return []
    with open(SNAPSHOT_FILE) as f:
        return json.load(f)


def save_snapshots(snapshots: list[dict]) -> None:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshots, f, indent=2)


def save_snapshot(inbox_count: int, unread_count: int) -> dict:
    snapshots = load_snapshots()
    snapshot = {
        "date": date.today().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "inbox_count": inbox_count,
        "unread_count": unread_count,
    }
    # Replace existing snapshot for today if present
    today = date.today().isoformat()
    snapshots = [s for s in snapshots if s.get("date") != today]
    snapshots.append(snapshot)
    # Keep last 90 days
    cutoff = (date.today() - timedelta(days=90)).isoformat()
    snapshots = [s for s in snapshots if s.get("date", "") >= cutoff]
    save_snapshots(snapshots)
    return snapshot


def list_snapshots(days: int = 30) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return [s for s in load_snapshots() if s.get("date", "") >= cutoff]


def compute_trend(days: int = 7) -> dict:
    recent = list_snapshots(days)
    if not recent:
        return {"trend": "no_data", "days": days, "snapshots": []}
    counts = [s["inbox_count"] for s in recent]
    avg = sum(counts) / len(counts)
    first = counts[0] if counts else 0
    last = counts[-1] if counts else 0
    delta = last - first
    if len(counts) < 2:
        trend = "stable"
    elif delta > first * 0.1:
        trend = "growing"
    elif delta < -(first * 0.1):
        trend = "declining"
    else:
        trend = "stable"
    return {
        "trend": trend,
        "days": days,
        "first_count": first,
        "last_count": last,
        "avg_count": round(avg, 1),
        "delta": delta,
        "snapshots": recent,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inbox stats snapshot tool")
    subparsers = parser.add_subparsers(dest="command")

    save_p = subparsers.add_parser("save", help="Save a snapshot")
    save_p.add_argument("--inbox-count", type=int, required=True)
    save_p.add_argument("--unread-count", type=int, default=0)

    list_p = subparsers.add_parser("list", help="List recent snapshots")
    list_p.add_argument("--days", type=int, default=30)

    trend_p = subparsers.add_parser("trend", help="Compute inbox trend")
    trend_p.add_argument("--days", type=int, default=7)

    # Legacy flat args for direct invocation
    parser.add_argument("--inbox-count", type=int)
    parser.add_argument("--unread-count", type=int, default=0)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--trend", type=int, metavar="DAYS")

    args = parser.parse_args()

    if args.command == "save" or (args.command is None and args.inbox_count is not None):
        count = args.inbox_count
        unread = args.unread_count
        result = save_snapshot(count, unread)
        print(json.dumps({"status": "saved", "snapshot": result}))

    elif args.command == "list" or (args.command is None and args.list):
        days = args.days if args.command == "list" else 30
        result = list_snapshots(days)
        print(json.dumps({"snapshots": result, "count": len(result)}))

    elif args.command == "trend" or (args.command is None and args.trend is not None):
        days = args.days if args.command == "trend" else args.trend
        result = compute_trend(days)
        print(json.dumps(result))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
