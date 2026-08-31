"""Hermetic protocol tests for opaque, single-use Things++ mutation receipts."""

from __future__ import annotations

import asyncio
import base64
import os
import sqlite3
import stat
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Barrier
from typing import TYPE_CHECKING, Any, Literal

import pytest

import things_common.mutation as mutation_module
from things_common import (
    MutationAmbiguousError,
    MutationBusyError,
    MutationCoordinator,
    MutationIntent,
    MutationReceiptError,
    MutationStateError,
    SecureRuntimePaths,
    SecurityViolation,
)

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class _ManualClock:
    value: float = 1_000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _intent(**changes: Any) -> MutationIntent:
    values: dict[str, Any] = {
        "principal": "principal-alpha",
        "client_id": "client-alpha",
        "resource": "https://mcp.example.test/mcp/things",
        "tool": "update_todo",
        "target_ids": ("todo-alpha",),
        "arguments": {"title": "Synthetic private title", "completed": True},
        "minimum_scope": "things.write",
    }
    values.update(changes)
    return MutationIntent(**values)


@pytest.fixture
def manual_clock() -> _ManualClock:
    return _ManualClock()


@pytest.fixture
def runtime_paths(tmp_path: Path) -> SecureRuntimePaths:
    return SecureRuntimePaths.create(tmp_path / "runtime")


@pytest.fixture
def coordinator(runtime_paths: SecureRuntimePaths, manual_clock: _ManualClock) -> MutationCoordinator:
    return MutationCoordinator(
        runtime_paths,
        receipt_ttl_seconds=10.0,
        lock_timeout_seconds=1.0,
        clock=manual_clock,
    )


def test_receipt_is_256_bit_opaque_short_lived_and_store_files_are_private(
    coordinator: MutationCoordinator, runtime_paths: SecureRuntimePaths, manual_clock: _ManualClock
) -> None:
    preview = coordinator.preview(_intent(), lambda: {"revision": 1})
    padding = "=" * (-len(preview.mutation_receipt) % 4)
    decoded = base64.urlsafe_b64decode(preview.mutation_receipt + padding)

    assert len(decoded) == 32
    assert preview.expires_at == manual_clock.value + 10.0
    assert preview.target_count == 1
    assert len(preview.receipt_id) == 16
    assert preview.receipt_id not in preview.mutation_receipt
    assert stat.S_IMODE(runtime_paths.receipt_key.stat().st_mode) == 0o600
    assert stat.S_IMODE(runtime_paths.receipts_db.stat().st_mode) == 0o600


def test_preview_execute_readback_and_replay_mutates_exactly_once(coordinator: MutationCoordinator) -> None:
    intent = _intent()
    calls = {"read": 0, "mutate": 0, "verify": 0}

    def read_state() -> dict[str, int]:
        calls["read"] += 1
        return {"revision": 1}

    def mutate() -> dict[str, str]:
        calls["mutate"] += 1
        return {"id": "todo-alpha"}

    def verify(result: dict[str, str]) -> dict[str, Any]:
        calls["verify"] += 1
        assert result == {"id": "todo-alpha"}
        return {"changed": 1, "skipped": 0, "failed": 0, "ambiguous": 0, "ids": ("todo-alpha",)}

    preview = coordinator.preview(intent, read_state)
    execution = coordinator.execute(intent, preview.mutation_receipt, read_state, mutate, verify)

    assert execution.status == "changed"
    assert execution.receipt_id == preview.receipt_id
    assert execution.changed == 1
    assert execution.skipped == execution.failed == execution.ambiguous == 0
    assert execution.verification_hash is not None
    assert coordinator.receipt_status(preview.mutation_receipt) == "consumed"
    assert calls == {"read": 2, "mutate": 1, "verify": 1}

    with pytest.raises(MutationReceiptError, match="replayed"):
        coordinator.execute(intent, preview.mutation_receipt, read_state, mutate, verify)
    assert calls == {"read": 2, "mutate": 1, "verify": 1}


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("principal", "principal-beta"),
        ("client_id", "client-beta"),
        ("resource", "https://mcp.example.test/mcp/other"),
        ("tool", "delete_todo"),
        ("target_ids", ("todo-beta",)),
        ("arguments", {"title": "Different synthetic title", "completed": True}),
        ("minimum_scope", "things.admin"),
    ],
)
def test_receipt_rejects_every_binding_substitution_before_backend_mutation(
    tmp_path: Path, field: str, replacement: Any
) -> None:
    coordinator = MutationCoordinator(SecureRuntimePaths.create(tmp_path / field), receipt_ttl_seconds=10.0)
    original = _intent()
    substituted = _intent(**{field: replacement})
    preview = coordinator.preview(original, lambda: {"revision": 1})
    backend_calls = 0

    def mutate() -> None:
        nonlocal backend_calls
        backend_calls += 1

    with pytest.raises(MutationReceiptError, match="binding"):
        coordinator.execute(
            substituted,
            preview.mutation_receipt,
            lambda: {"revision": 1},
            mutate,
            lambda _result: {"changed": 1},
        )
    assert backend_calls == 0
    assert coordinator.receipt_status(preview.mutation_receipt) == "issued"


def test_stale_state_is_rejected_before_mutation(coordinator: MutationCoordinator) -> None:
    intent = _intent()
    preview = coordinator.preview(intent, lambda: {"revision": 1})
    mutated = False

    def mutate() -> None:
        nonlocal mutated
        mutated = True

    with pytest.raises(MutationStateError, match="changed after preview"):
        coordinator.execute(
            intent,
            preview.mutation_receipt,
            lambda: {"revision": 2},
            mutate,
            lambda _result: {"changed": 1},
        )
    assert not mutated


def test_expired_receipt_is_rejected_and_releases_reservation(
    coordinator: MutationCoordinator, manual_clock: _ManualClock
) -> None:
    intent = _intent()
    preview = coordinator.preview(intent, lambda: {"revision": 1})
    manual_clock.advance(10.01)
    mutated = False

    def mutate() -> None:
        nonlocal mutated
        mutated = True

    with pytest.raises(MutationReceiptError, match="expired"):
        coordinator.execute(
            intent,
            preview.mutation_receipt,
            lambda: {"revision": 1},
            mutate,
            lambda _result: {"changed": 1},
        )
    assert not mutated
    assert coordinator.receipt_status(preview.mutation_receipt) == "expired"
    replacement = coordinator.preview(_intent(target_ids=("todo-beta",)), lambda: {"revision": 1})
    assert replacement.status == "preview"


def test_reservation_is_global_across_coordinators_and_can_be_abandoned(
    runtime_paths: SecureRuntimePaths, manual_clock: _ManualClock
) -> None:
    first = MutationCoordinator(runtime_paths, receipt_ttl_seconds=10.0, clock=manual_clock)
    second = MutationCoordinator(runtime_paths, receipt_ttl_seconds=10.0, clock=manual_clock)
    intent = _intent()
    preview = first.preview(intent, lambda: {"revision": 1})

    with pytest.raises(MutationBusyError, match="reservation"):
        second.preview(_intent(target_ids=("todo-beta",)), lambda: {"revision": 1})
    with pytest.raises(MutationReceiptError, match="binding"):
        second.abandon(_intent(client_id="other-client"), preview.mutation_receipt)

    first.abandon(intent, preview.mutation_receipt)
    assert first.receipt_status(preview.mutation_receipt) == "abandoned"
    replacement = second.preview(_intent(target_ids=("todo-beta",)), lambda: {"revision": 1})
    assert replacement.status == "preview"


def test_mutation_or_verification_failure_becomes_ambiguous_and_never_replays(
    coordinator: MutationCoordinator,
) -> None:
    intent = _intent()
    preview = coordinator.preview(intent, lambda: {"revision": 1})
    mutation_calls = 0

    def fail_after_possible_write() -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        raise RuntimeError("backend response contained private title")

    with pytest.raises(MutationAmbiguousError, match="do not retry") as exc_info:
        coordinator.execute(
            intent,
            preview.mutation_receipt,
            lambda: {"revision": 1},
            fail_after_possible_write,
            lambda _result: {"changed": 1},
        )
    assert "private title" not in str(exc_info.value)
    assert mutation_calls == 1
    assert coordinator.receipt_status(preview.mutation_receipt) == "ambiguous"

    with pytest.raises(MutationReceiptError):
        coordinator.execute(
            intent,
            preview.mutation_receipt,
            lambda: {"revision": 1},
            fail_after_possible_write,
            lambda _result: {"changed": 1},
        )
    assert mutation_calls == 1


@pytest.mark.parametrize(
    ("verified_status", "stored_status"),
    [("changed", "consumed"), ("unchanged", "ambiguous"), ("ambiguous", "ambiguous")],
)
def test_ambiguous_receipt_recovery_verifies_without_replaying(
    tmp_path: Path,
    verified_status: Literal["changed", "unchanged", "ambiguous"],
    stored_status: str,
) -> None:
    coordinator = MutationCoordinator(SecureRuntimePaths.create(tmp_path / verified_status))
    intent = _intent()
    preview = coordinator.preview(intent, lambda: {"revision": 1})

    with pytest.raises(MutationAmbiguousError):
        coordinator.execute(
            intent,
            preview.mutation_receipt,
            lambda: {"revision": 1},
            lambda: (_ for _ in ()).throw(RuntimeError("unknown backend outcome")),
            lambda _result: {"changed": 1},
        )

    recovery = coordinator.recover(
        preview.mutation_receipt,
        lambda: (verified_status, {"observed": verified_status}),
    )
    assert recovery.status == verified_status
    assert recovery.receipt_id == preview.receipt_id
    assert recovery.verification_hash is not None
    assert coordinator.receipt_status(preview.mutation_receipt) == stored_status


def test_two_concurrent_executes_have_one_winner_and_one_backend_call(coordinator: MutationCoordinator) -> None:
    intent = _intent()
    preview = coordinator.preview(intent, lambda: {"revision": 1})
    mutation_calls = 0
    start = Barrier(3)

    def execute_once() -> str:
        nonlocal mutation_calls
        start.wait(timeout=2)

        def mutate() -> dict[str, bool]:
            nonlocal mutation_calls
            mutation_calls += 1
            return {"ok": True}

        try:
            return coordinator.execute(
                intent,
                preview.mutation_receipt,
                lambda: {"revision": 1},
                mutate,
                lambda _result: {"changed": 1, "skipped": 0, "failed": 0, "ambiguous": 0},
            ).status
        except MutationReceiptError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(execute_once) for _ in range(2)]
        start.wait(timeout=2)
        outcomes = sorted(future.result() for future in futures)

    assert outcomes == ["changed", "rejected"]
    assert mutation_calls == 1


def test_async_preview_execute_preserves_counts_and_single_use(coordinator: MutationCoordinator) -> None:
    intent = _intent(target_ids=("todo-alpha", "todo-beta", "todo-gamma"))
    calls = {"read": 0, "mutate": 0, "verify": 0}

    async def read_state() -> dict[str, int]:
        calls["read"] += 1
        await asyncio.sleep(0)
        return {"revision": 1}

    async def mutate() -> dict[str, bool]:
        calls["mutate"] += 1
        await asyncio.sleep(0)
        return {"ok": True}

    async def verify(result: dict[str, bool]) -> dict[str, int]:
        calls["verify"] += 1
        assert result == {"ok": True}
        await asyncio.sleep(0)
        return {"changed": 1, "skipped": 1, "failed": 1, "ambiguous": 0}

    async def scenario() -> None:
        preview = await coordinator.apreview(intent, read_state)
        execution = await coordinator.aexecute(intent, preview.mutation_receipt, read_state, mutate, verify)
        assert execution.status == "changed"
        assert (execution.changed, execution.skipped, execution.failed, execution.ambiguous) == (1, 1, 1, 0)
        assert coordinator.receipt_status(preview.mutation_receipt) == "consumed"
        with pytest.raises(MutationReceiptError):
            await coordinator.aexecute(intent, preview.mutation_receipt, read_state, mutate, verify)

    asyncio.run(scenario())
    assert calls == {"read": 2, "mutate": 1, "verify": 1}


def test_receipt_database_contains_no_raw_receipt_binding_state_or_verification_content(
    coordinator: MutationCoordinator, runtime_paths: SecureRuntimePaths
) -> None:
    private_values = {
        "principal": "principal-secret-4dc0a40b",
        "client_id": "client-secret-e8af4577",
        "resource": "https://private.example.test/mcp/things/5becb73f",
        "tool": "update_todo",
        "target": "todo-secret-a0ab3dd9",
        "argument": "Synthetic secret task 34594471",
        "state": "Synthetic secret state 77dd5956",
        "verification": "Synthetic secret verification 8f641f01",
    }
    intent = _intent(
        principal=private_values["principal"],
        client_id=private_values["client_id"],
        resource=private_values["resource"],
        target_ids=(private_values["target"],),
        arguments={"title": private_values["argument"]},
    )
    preview = coordinator.preview(intent, lambda: {"title": private_values["state"]})
    coordinator.execute(
        intent,
        preview.mutation_receipt,
        lambda: {"title": private_values["state"]},
        lambda: {"id": private_values["target"]},
        lambda _result: {
            "changed": 1,
            "skipped": 0,
            "failed": 0,
            "ambiguous": 0,
            "observed": private_values["verification"],
        },
    )

    database_bytes = runtime_paths.receipts_db.read_bytes()
    forbidden = [preview.mutation_receipt, *private_values.values()]
    for value in forbidden:
        assert value.encode("utf-8") not in database_bytes

    with sqlite3.connect(runtime_paths.receipts_db) as db:
        row = db.execute(
            "SELECT receipt_hash,binding_hash,state_hash,verification_hash,status FROM receipts"
        ).fetchone()
    assert row is not None
    receipt_hash, binding_hash, state_hash, verification_hash, status = row
    assert status == "consumed"
    assert all(len(value) == 64 for value in (receipt_hash, binding_hash, state_hash, verification_hash))
    assert preview.mutation_receipt != receipt_hash


@pytest.mark.parametrize("ttl", [0.0, 0.999, 300.001, 301.0])
def test_receipt_ttl_is_bounded(tmp_path: Path, ttl: float) -> None:
    with pytest.raises(ValueError, match="between 1 and 300"):
        MutationCoordinator(SecureRuntimePaths.create(tmp_path / f"runtime-{ttl}"), receipt_ttl_seconds=ttl)


def test_receipt_key_is_reused_by_multiple_coordinators_without_exposure(runtime_paths: SecureRuntimePaths) -> None:
    MutationCoordinator(runtime_paths)
    key_before = runtime_paths.receipt_key.read_bytes()
    MutationCoordinator(runtime_paths)

    assert len(key_before) == 32
    assert runtime_paths.receipt_key.read_bytes() == key_before
    assert os.access(runtime_paths.receipt_key, os.R_OK | os.W_OK)


@pytest.mark.parametrize("swap_kind", ["regular", "symlink"])
def test_sqlite_never_reopens_verified_runtime_path_and_swaps_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, swap_kind: str
) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    paths.receipts_db.write_bytes(b"")
    paths.receipts_db.chmod(0o600)
    swap_target = tmp_path / "swap-target.sqlite3"
    swap_target.write_bytes(b"sentinel")
    swap_target.chmod(0o600)
    real_connect = sqlite3.connect
    databases: list[str] = []

    def swap_before_connect(database: str, *args: Any, **kwargs: Any) -> sqlite3.Connection:
        databases.append(str(database))
        assert database == ":memory:"
        paths.receipts_db.unlink()
        if swap_kind == "symlink":
            paths.receipts_db.symlink_to(swap_target)
        else:
            paths.receipts_db.write_bytes(b"replacement")
            paths.receipts_db.chmod(0o600)
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(mutation_module.sqlite3, "connect", swap_before_connect)
    with pytest.raises(SecurityViolation):
        MutationCoordinator(paths)
    assert databases == [":memory:"]
    assert swap_target.read_bytes() == b"sentinel"
    if swap_kind == "regular":
        assert paths.receipts_db.read_bytes() == b"replacement"


@pytest.mark.parametrize(
    "verification",
    [
        {"changed": 1},
        {"changed": 1, "skipped": 0, "failed": 0, "ambiguous": 1},
        {"changed": True, "skipped": 0, "failed": 0, "ambiguous": 0},
    ],
)
def test_verification_counts_must_be_explicit_typed_and_reconcile(tmp_path: Path, verification: dict[str, Any]) -> None:
    coordinator = MutationCoordinator(SecureRuntimePaths.create(tmp_path / "runtime"))
    intent = _intent()
    preview = coordinator.preview(intent, lambda: {"revision": 1})

    with pytest.raises(MutationAmbiguousError, match="do not retry"):
        coordinator.execute(
            intent,
            preview.mutation_receipt,
            lambda: {"revision": 1},
            lambda: {"success": True},
            lambda _result: verification,
        )
    assert coordinator.receipt_status(preview.mutation_receipt) == "ambiguous"
