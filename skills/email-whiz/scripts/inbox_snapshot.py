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

from constants import EMAIL_WHIZ_DIR

SNAPSHOT_DIR = EMAIL_WHIZ_DIR
SNAPSHOT_FILE = os.path.join(SNAPSHOT_DIR, "snapshots.json")
CACHE_FILE = os.path.join(SNAPSHOT_DIR, "session-cache.json")


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
    if first == 0 and delta > 0:
        trend = "growing"
    elif first == 0 and delta < 0:
        trend = "declining"
    elif len(counts) < 2:
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


def save_cache(labels: str, filters: str, inbox_count: int, unread_count: int, tier: str) -> dict:
    """Save session cache with current timestamp."""
    try:
        parsed_labels = json.loads(labels) if isinstance(labels, str) else labels
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON for labels: {e}"}))
        sys.exit(1)
    try:
        parsed_filters = json.loads(filters) if isinstance(filters, str) else filters
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON for filters: {e}"}))
        sys.exit(1)
    cache = {
        "labels": parsed_labels,
        "filters": parsed_filters,
        "inbox_count": inbox_count,
        "unread_count": unread_count,
        "tier": tier,
        "last_fetched": datetime.now().isoformat(),
    }
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    return cache


def load_cache(ttl_minutes: int = 60) -> dict | None:
    """Load session cache if within TTL. Returns None if expired or missing."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        fetched = datetime.fromisoformat(cache["last_fetched"])
        if datetime.now() - fetched > timedelta(minutes=ttl_minutes):
            return None
        return cache
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def clear_cache() -> bool:
    """Remove session cache file."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        return True
    return False


def compute_baseline(days: int = 30) -> dict:
    """Compute rolling average inbox count from snapshot history."""
    recent = list_snapshots(days)
    if not recent:
        return {"baseline": None, "days": days, "snapshots": 0, "fallback": 500}
    counts = [s["inbox_count"] for s in recent]
    avg = sum(counts) / len(counts)
    # Week-over-week growth detection
    if len(counts) >= 14:
        week1_avg = sum(counts[-7:]) / 7
        week2_avg = sum(counts[-14:-7]) / 7
        wow_growth = ((week1_avg - week2_avg) / week2_avg * 100) if week2_avg > 0 else 0
    else:
        wow_growth = 0
    return {
        "baseline": round(avg, 1),
        "days": days,
        "snapshots": len(recent),
        "min": min(counts),
        "max": max(counts),
        "wow_growth_pct": round(wow_growth, 1),
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

    cache_p = subparsers.add_parser("cache", help="Session cache management")
    cache_sub = cache_p.add_subparsers(dest="cache_command")

    cache_save_p = cache_sub.add_parser("save", help="Save session cache")
    cache_save_p.add_argument("--labels", type=str, required=True)
    cache_save_p.add_argument("--filters", type=str, required=True)
    cache_save_p.add_argument("--inbox-count", type=int, required=True)
    cache_save_p.add_argument("--unread-count", type=int, required=True)
    cache_save_p.add_argument("--tier", type=str, required=True)

    cache_load_p = cache_sub.add_parser("load", help="Load session cache")
    cache_load_p.add_argument("--ttl", type=int, default=60)

    cache_sub.add_parser("clear", help="Clear session cache")

    baseline_p = subparsers.add_parser("baseline", help="Compute rolling baseline")
    baseline_p.add_argument("--days", type=int, default=30)

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

    elif args.command == "cache":
        if args.cache_command == "save":
            result = save_cache(args.labels, args.filters, args.inbox_count, args.unread_count, args.tier)
            print(json.dumps({"status": "saved", "cache": result}))
        elif args.cache_command == "load":
            cache = load_cache(args.ttl)
            if cache is not None:
                print(json.dumps({"status": "valid", "cache": cache}))
            elif os.path.exists(CACHE_FILE):
                print(json.dumps({"status": "expired"}))
            else:
                print(json.dumps({"status": "missing"}))
        elif args.cache_command == "clear":
            cleared = clear_cache()
            if cleared:
                print(json.dumps({"status": "cleared"}))
            else:
                print(json.dumps({"status": "no_cache"}))
        else:
            cache_p.print_help()
            sys.exit(1)

    elif args.command == "baseline":
        result = compute_baseline(args.days)
        print(json.dumps(result))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
