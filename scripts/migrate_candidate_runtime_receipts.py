#!/usr/bin/env python3
"""Check or migrate candidate runtime receipts to the transactional v2 store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "planning/manifests/candidate-corpus-jul2026/runtime-activation-receipts.json"
RUNTIME_STATE = Path.home() / ".local/share/wagents/candidate-runtime"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    document = store.load(allow_v1=True)
    required = document["version"] == 1
    if not args.apply:
        print(
            json.dumps(
                {
                    "ok": not required,
                    "migration_required": required,
                    "version": document["version"],
                    "revision": document["revision"],
                    "receipt_count": len(document["receipts"]),
                    "closure_receipt_count": len(document["closure_receipts"]),
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 1 if args.check and required else 0

    result = store.migrate_v1()
    print(
        json.dumps(
            {
                "ok": True,
                "migrated": result.migrated,
                "version": 2,
                "revision": result.revision,
                "transaction_id": result.transaction_id,
                "document_sha256": result.document_sha256,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
