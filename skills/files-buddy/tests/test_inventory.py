"""Behavioral inventory tests use only isolated temporary filesystem fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import files_buddy_inventory as inventory
import pytest
from files_buddy_inventory import InventoryError, ScanOptions, dedupe, scan, watch

CLI = Path(__file__).resolve().parents[1] / "scripts" / "storage-audit.py"


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "scope"
        self.root.mkdir()
        self.database = self.base / "inventory.sqlite"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, data: bytes = b"same data") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_metadata_only_and_no_claimed_savings(self) -> None:
        self.write("a.txt")
        self.write("b.txt")
        with patch("files_buddy_inventory.os.read", side_effect=AssertionError("content read")):
            result = scan(self.root, self.database)
        assert result["counts"]["files_seen"] == 2
        assert result["savings"]["logical_bytes"] == 18
        assert result["savings"]["verified_reclaimed_bytes"] is None
        assert result["savings"]["candidate_bytes"] is None
        assert not result["inventory"]["read_content"]

    def test_hidden_and_git_policy_is_explicit(self) -> None:
        self.write(".hidden")
        self.write(".git/config")
        self.write("visible")
        result = scan(self.root, self.database)
        assert [Path(row["path"]).name for row in result["files"]] == ["visible"]
        assert not result["inventory"]["policy"]["include_hidden"]
        other = self.base / "hidden.sqlite"
        result = scan(self.root, other, options=ScanOptions(include_hidden=True))
        assert {Path(row["path"]).name for row in result["files"]} == {"visible", ".hidden"}
        assert all(not row["content_candidate"] for row in result["files"])

    def test_symlink_and_fifo_are_not_followed(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "secret").write_bytes(b"do not read")
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        os.mkfifo(self.root / "pipe")
        result = scan(self.root, self.database)
        assert result["counts"]["links_seen"] == 1
        assert result["counts"]["special_seen"] == 1
        assert not any("secret" in row["path"] for row in result["files"])
        assert dedupe(self.database, read_content=True)["duplicates"] == []

    def test_symlink_scope_rejected(self) -> None:
        alias = self.base / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with pytest.raises(InventoryError, match="symlink"):
            scan(alias, self.database)

    def test_database_inside_scope_or_symlink_is_rejected(self) -> None:
        with pytest.raises(InventoryError, match="outside"):
            scan(self.root, self.root / "inventory.sqlite")
        target = self.base / "target"
        target.write_text("untouched")
        self.database.symlink_to(target)
        with pytest.raises(InventoryError, match="symlink"):
            scan(self.root, self.database)
        assert target.read_text() == "untouched"

    def test_database_parent_traversal_is_rejected_before_source_tree_changes(self) -> None:
        original = self.write("original.txt")
        sibling = self.base / "sibling"
        database = sibling / ".." / self.root.name / "inventory.sqlite"
        with pytest.raises(InventoryError, match="without '\\.\\.'"):
            scan(self.root, database)
        assert list(self.root.iterdir()) == [original]
        assert original.read_bytes() == b"same data"
        assert not sibling.exists()

    def test_multiply_linked_database_is_rejected_before_sqlite_access(self) -> None:
        scan(self.root, self.database)
        linked = self.root / "linked.sqlite"
        os.link(self.database, linked)
        before = linked.read_bytes()
        with patch("files_buddy_inventory.sqlite3.connect", side_effect=AssertionError("SQLite opened linked file")):
            with pytest.raises(InventoryError, match="singly linked"):
                scan(self.root, self.database, resume=True)
            with pytest.raises(InventoryError, match="singly linked"):
                dedupe(self.database, read_content=True)
        assert linked.read_bytes() == before
        assert list(self.root.iterdir()) == [linked]

    def test_sqlite_sidecar_symlinks_and_hardlinks_are_rejected(self) -> None:
        scan(self.root, self.database)
        original = self.write("original.txt")
        for suffix in ("-journal", "-wal", "-shm"):
            sidecar = self.database.with_name(self.database.name + suffix)
            for link_kind in ("symlink", "hardlink"):
                with self.subTest(suffix=suffix, link_kind=link_kind):
                    if link_kind == "symlink":
                        sidecar.symlink_to(original)
                    else:
                        os.link(original, sidecar)
                    try:
                        with pytest.raises(InventoryError, match="singly linked"):
                            scan(self.root, self.database, resume=True)
                        assert original.read_bytes() == b"same data"
                    finally:
                        sidecar.unlink()

    def test_relocated_inventory_cannot_update_its_observed_source_tree(self) -> None:
        self.write("a")
        self.write("b")
        scan(self.root, self.database)
        relocated = self.root / "inventory.sqlite"
        self.database.rename(relocated)
        before = relocated.read_bytes()
        with pytest.raises(InventoryError, match="outside"):
            dedupe(relocated, read_content=True)
        assert relocated.read_bytes() == before
        assert {path.name for path in self.root.iterdir()} == {"a", "b", "inventory.sqlite"}

    def test_missing_dedupe_database_is_not_created(self) -> None:
        with pytest.raises(InventoryError, match="does not exist"):
            dedupe(self.database, read_content=True)
        assert not self.database.exists()

    def test_non_inventory_database_is_preserved(self) -> None:
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE unrelated (value TEXT)")
        before = self.database.read_bytes()
        with pytest.raises(InventoryError, match="Not a Files Buddy"):
            scan(self.root, self.database)
        assert before == self.database.read_bytes()

    def test_resume_revalidates_child_when_parent_mtime_unchanged(self) -> None:
        a = self.write("folder/a.txt", b"same")
        self.write("folder/b.txt", b"same")
        scan(self.root, self.database)
        assert len(dedupe(self.database, read_content=True)["duplicates"]) == 1
        parent_before = a.parent.stat()
        a.write_bytes(b"diff")
        os.utime(a.parent, ns=(parent_before.st_atime_ns, parent_before.st_mtime_ns))
        resumed = scan(self.root, self.database, resume=True)
        fresh = scan(self.root, self.base / "fresh.sqlite")
        assert resumed["inventory"]["metadata_digest"] == fresh["inventory"]["metadata_digest"]
        assert dedupe(self.database, read_content=True)["duplicates"] == []

    def test_changed_content_invalidates_cached_hash_even_without_scan(self) -> None:
        a = self.write("a", b"same")
        self.write("b", b"same")
        scan(self.root, self.database)
        dedupe(self.database, read_content=True)
        a.write_bytes(b"diff")
        result = dedupe(self.database, read_content=True)
        assert result["coverage"]["status"] == "partial"
        assert result["duplicates"] == []
        assert any("metadata changed" in line for line in result["coverage"]["omissions"])

    def test_resume_budget_progresses_and_drops_removed_entries_on_completion(self) -> None:
        for index in range(7):
            self.write(f"file-{index}")
        options = ScanOptions(max_entries=2)
        result = scan(self.root, self.database, options=options)
        assert result["coverage"]["status"] == "partial"
        for _ in range(4):
            result = scan(self.root, self.database, options=options, resume=True)
            if result["coverage"]["status"] == "complete":
                break
        assert result["coverage"]["status"] == "complete"
        assert result["counts"]["files_seen"] == 7
        (self.root / "file-0").unlink()
        result = scan(self.root, self.database, options=options, resume=True)
        assert result["counts"]["files_seen"] == 6
        assert result["counts"]["deleted_entries"] == 1

    def test_resume_requires_same_scope_and_policy(self) -> None:
        scan(self.root, self.database)
        with pytest.raises(InventoryError, match="already"):
            scan(self.root, self.database)
        with pytest.raises(InventoryError, match="policy"):
            scan(self.root, self.database, options=ScanOptions(include_hidden=True), resume=True)
        other = self.base / "other"
        other.mkdir()
        with pytest.raises(InventoryError, match="scope"):
            scan(other, self.database, resume=True)

    def test_partial_access_is_not_reported_as_empty_complete(self) -> None:
        with patch("files_buddy_inventory.os.scandir", side_effect=PermissionError("fixture denied")):
            result = scan(self.root, self.database)
        assert result["coverage"]["status"] == "partial"
        assert result["counts"]["errors"] == 1
        assert result["coverage"]["omissions"]

    def test_large_report_caps_do_not_truncate_counts(self) -> None:
        for index in range(7):
            self.write(f"file-{index}", bytes(index + 1))
        result = scan(self.root, self.database, options=ScanOptions(max_rows=2))
        assert result["counts"]["files_seen"] == 7
        assert len(result["files"]) == 2
        assert result["inventory"]["file_rows_truncated"]

    def test_project_cloud_bundle_and_sidecar_are_not_content_candidates(self) -> None:
        self.write("project/package.json", b"{}")
        self.write("project/a", b"same")
        self.write("project/b", b"same")
        self.write("Library/CloudStorage/provider/a", b"same")
        self.write("Library/CloudStorage/provider/b", b"same")
        self.write("Photo.photoslibrary/a", b"same")
        self.write("image.jpg", b"same")
        self.write("image.xmp", b"same")
        self.write("normal.txt", b"same")
        result = scan(self.root, self.database)
        candidates = [Path(row["path"]).name for row in result["files"] if row["content_candidate"]]
        assert candidates == ["normal.txt"]
        with patch("files_buddy_inventory.os.read", side_effect=AssertionError("no paired eligible files")):
            assert dedupe(self.database, read_content=True)["duplicates"] == []

    def test_secret_variants_and_owner_managed_stores_never_read_content(self) -> None:
        names = (
            ".env.production",
            ".env.backup",
            "Library/Application Support/TestApp/state",
            "Library/Application Support/TestApp/backup",
            ".ollama/models/a",
            ".ollama/models/b",
            ".docker/a",
            ".docker/b",
            ".config/a",
            ".config/b",
        )
        for name in names:
            self.write(name, b"managed data")
        result = scan(self.root, self.database, options=ScanOptions(include_hidden=True))
        assert result["files"]
        assert all(not row["content_candidate"] for row in result["files"])
        assert {row["category"] for row in result["files"]} >= {"protected", "app-data", "model"}
        # A poisoned eligibility bit still cannot bypass fresh path policy.
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE entries SET eligible=1 WHERE kind='file'")
        with patch("files_buddy_inventory.os.read", side_effect=AssertionError("managed content read")):
            result = dedupe(self.database, read_content=True)
        assert result["duplicates"] == []
        assert result["counts"]["bytes_hashed"] == 0
        assert result["coverage"]["status"] == "partial"

    def test_poisoned_candidate_paths_cannot_escape_scope_or_open_content(self) -> None:
        self.write("a")
        self.write("b")
        outside = self.base / "outside"
        outside.mkdir()
        for name in ("a", "b"):
            (outside / name).write_bytes(b"outside content")
        prefixes = (f"{self.root}/../outside", str(outside), "../outside", f"{self.root}/./../outside")
        for index, prefix in enumerate(prefixes):
            with self.subTest(prefix=prefix):
                database = self.base / f"poisoned-{index}.sqlite"
                scan(self.root, database)
                with sqlite3.connect(database) as connection:
                    for name in ("a", "b"):
                        info = (outside / name).stat()
                        connection.execute(
                            "UPDATE entries SET path=?,fingerprint=?,size=? WHERE path=?",
                            (f"{prefix}/{name}", inventory._fingerprint(info), info.st_size, str(self.root / name)),
                        )
                with patch("files_buddy_inventory.os.read", side_effect=AssertionError("out-of-scope content read")):
                    result = dedupe(database, read_content=True)
                assert result["coverage"]["status"] == "partial"
                assert result["counts"]["bytes_hashed"] == 0
                assert result["duplicates"] == []

    def test_regular_file_handle_rejects_traversal_before_open(self) -> None:
        for relative in (Path("../outside/a"), Path("/outside/a"), Path(".")):
            with (
                self.subTest(relative=relative),
                patch("files_buddy_inventory.os.open", side_effect=AssertionError("invalid path opened")),
                pytest.raises(InventoryError, match="relative path"),
                inventory._open_regular(self.root, relative, options=ScanOptions()),
            ):
                pytest.fail("invalid content path entered")

    def test_additional_provider_roots_are_excluded(self) -> None:
        self.write("custom-sync/a")
        self.write("custom-sync/b")
        options = ScanOptions(cloud_roots=(str(self.root / "custom-sync"),))
        scan(self.root, self.database, options=options)
        assert dedupe(self.database, read_content=True)["duplicates"] == []

    def test_cloud_root_policy_rejects_parent_traversal(self) -> None:
        options = ScanOptions(cloud_roots=(str(self.root / "nested" / ".." / "provider"),))
        with pytest.raises(InventoryError, match="Cloud-root"):
            scan(self.root, self.database, options=options)
        assert not self.database.exists()

    def test_case_variants_cannot_bypass_cloud_protected_or_cache_policy(self) -> None:
        self.write("library/cloudstorage/provider/a")
        self.write("library/cloudstorage/provider/b")
        self.write(".SSH/private")
        self.write("cAcHeS/blob")
        self.write("custom-sync/a")
        self.write("custom-sync/b")
        options = ScanOptions(include_hidden=True, cloud_roots=(str(self.root / "CUSTOM-SYNC"),))
        result = scan(self.root, self.database, options=options)
        assert all(not row["content_candidate"] for row in result["files"])
        with patch("files_buddy_inventory.os.read", side_effect=AssertionError("managed content read")):
            assert dedupe(self.database, read_content=True)["duplicates"] == []

    def test_video_caption_and_uppercase_sidecar_families_are_excluded(self) -> None:
        self.write("movie.mp4")
        self.write("movie.SRT", b"captions")
        self.write("image.jpg")
        self.write("image.XMP", b"metadata")
        self.write("normal.bin")
        result = scan(self.root, self.database)
        candidates = {Path(row["path"]).name for row in result["files"] if row["content_candidate"]}
        assert candidates == {"normal.bin"}

    def test_hardlinks_use_device_inode_identity_and_do_not_inflate_totals(self) -> None:
        a = self.write("a")
        os.link(a, self.root / "hardlink")
        self.write("independent")
        result = scan(self.root, self.database)
        assert result["savings"]["logical_bytes"] == 18
        assert dedupe(self.database, read_content=True)["duplicates"] == []

    def test_category_totals_share_unique_inode_accounting(self) -> None:
        a = self.write("a.txt")
        os.link(a, self.root / "archive.zip")
        self.write("independent.txt")
        result = scan(self.root, self.database)
        assert sum(row["bytes"] for row in result["categories"]) == result["savings"]["logical_bytes"] == 18
        assert any(row["name"] == "hardlink-shared" for row in result["categories"])

    def test_fresh_project_marker_blocks_cached_hashes(self) -> None:
        self.write("a")
        self.write("b")
        scan(self.root, self.database)
        dedupe(self.database, read_content=True)
        self.write("package.json", b"{}")
        with patch("files_buddy_inventory.os.read", side_effect=AssertionError("project content read")):
            result = dedupe(self.database, read_content=True)
        assert result["duplicates"] == []
        assert result["coverage"]["status"] == "partial"

    def test_fresh_ancestor_project_and_sidecar_are_checked(self) -> None:
        self.write("a.jpg")
        self.write("b.jpg")
        scan(self.root, self.database)
        self.write("a.xmp", b"metadata")
        result = dedupe(self.database, read_content=True)
        assert result["duplicates"] == []
        assert result["counts"]["bytes_hashed"] == 9
        (self.base / "pyproject.toml").write_text("[project]")
        with patch("files_buddy_inventory.os.read", side_effect=AssertionError("ancestor project read")):
            result = dedupe(self.database, read_content=True)
        assert result["duplicates"] == []
        assert result["counts"]["bytes_hashed"] == 0

    def test_corrupt_metadata_counter_fails_structurally(self) -> None:
        scan(self.root, self.database)
        with sqlite3.connect(self.database) as connection:
            metadata = json.loads(connection.execute("SELECT value FROM metadata WHERE key='scan'").fetchone()[0])
            metadata["errors"] = {}
            connection.execute("UPDATE metadata SET value=? WHERE key='scan'", (json.dumps(metadata),))
        with pytest.raises(InventoryError, match="counter"):
            scan(self.root, self.database, resume=True)

    def test_exact_group_is_review_only_and_content_read_is_explicit(self) -> None:
        payload = b"exact comparison"
        self.write("-a\nname", payload)
        self.write("unicod\u00e9", payload)
        scan(self.root, self.database)
        with pytest.raises(InventoryError, match="--read-content"):
            dedupe(self.database)
        result = dedupe(self.database, read_content=True)
        group = result["duplicates"][0]
        assert group["hash"] == hashlib.sha256(payload).hexdigest()
        assert group["hash_algorithm"] == "sha256"
        assert group["keeper"] is None
        assert group["risk"] == "unknown"
        assert group["review_only"]
        assert result["savings"]["candidate_bytes"] == len(payload)
        assert result["savings"]["verified_reclaimed_bytes"] is None

    def test_hash_budget_never_uses_unchecked_cached_rows(self) -> None:
        self.write("a", b"same")
        self.write("b", b"same")
        scan(self.root, self.database)
        result = dedupe(self.database, read_content=True, max_bytes=4)
        assert result["coverage"]["status"] == "partial"
        assert result["duplicates"] == []
        assert result["counts"]["bytes_hashed"] == 4

    def test_replaced_symlink_is_not_followed_by_hashing(self) -> None:
        a = self.write("a", b"same")
        self.write("b", b"same")
        external = self.base / "external"
        external.write_bytes(b"same")
        scan(self.root, self.database)
        a.unlink()
        a.symlink_to(external)
        result = dedupe(self.database, read_content=True)
        assert result["coverage"]["status"] == "partial"
        assert result["duplicates"] == []

    def test_depth_limit_is_partial_and_directory_sizes_are_not_subtree_sizes(self) -> None:
        self.write("a/b/c")
        result = scan(self.root, self.database, options=ScanOptions(max_depth=1))
        assert result["coverage"]["status"] == "partial"
        assert result["directories"][0]["size"] is None

    def test_watch_is_bounded_and_does_not_apply_rules(self) -> None:
        path = self.write("inbox.txt")
        result = watch(self.root, self.database, cycles=2, interval=0.1)
        assert result["watch"]["proposal_only"]
        assert not result["watch"]["background_service"]
        assert len(result["events"]) == 2
        assert path.is_file()
        assert result["savings"]["acted_bytes"] == 0
        assert result["counts"]["settled_files"] == 1
        assert result["watch"]["settled_candidates"][0]["observations"] == 2

    def test_watch_changed_file_is_not_settled(self) -> None:
        path = self.write("inbox.txt", b"before")
        with patch("files_buddy_inventory.time.sleep", side_effect=lambda _: path.write_bytes(b"after!")):
            result = watch(self.root, self.database, cycles=2, interval=0.1)
        assert result["watch"]["settled_candidates"] == []
        assert result["counts"]["settled_files"] == 0

    def test_watch_settlement_is_explicitly_partial_when_rows_capped(self) -> None:
        self.write("a")
        self.write("b")
        result = watch(self.root, self.database, cycles=2, interval=0.1, options=ScanOptions(max_rows=1))
        assert result["counts"]["settled_files"] == 1
        assert result["coverage"]["status"] == "partial"
        assert result["watch"]["settlement_coverage"] == "partial"

    def test_watch_total_processing_budget_is_bounded(self) -> None:
        with pytest.raises(InventoryError, match="Combined watch"):
            watch(self.root, self.database, cycles=100, interval=1)

    def test_cli_bad_budget_returns_json_and_no_overwrite(self) -> None:
        process = subprocess.run(
            [sys.executable, str(CLI), "scan", str(self.root), "--database", str(self.database), "--max-entries", "0"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert process.returncode == 1
        assert "error" in json.loads(process.stdout)
        output = self.base / "existing.json"
        output.write_text("keep me")
        process = subprocess.run(
            [sys.executable, str(CLI), "tools", "--output", str(output)], capture_output=True, text=True, check=False
        )
        assert process.returncode == 1
        assert output.read_text() == "keep me"

    def test_cli_output_scope_and_parent_traversal_fail_before_scan_writes(self) -> None:
        original = self.write("original.txt")
        for output in (self.root / "report.json", self.base / "sibling" / ".." / "scope" / "report.json"):
            with self.subTest(output=output):
                process = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "scan",
                        str(self.root),
                        "--database",
                        str(self.database),
                        "--output",
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert process.returncode == 1
                assert "error" in json.loads(process.stdout)
                assert not self.database.exists()
                assert list(self.root.iterdir()) == [original]
                assert original.read_bytes() == b"same data"
        assert not (self.base / "sibling").exists()

    def test_cli_output_symlink_parent_does_not_create_external_directories(self) -> None:
        alias = self.base / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        process = subprocess.run(
            [sys.executable, str(CLI), "tools", "--output", str(alias / "new" / "report.json")],
            capture_output=True,
            text=True,
            check=False,
        )
        assert process.returncode == 1
        assert "symlink" in json.loads(process.stdout)["error"]
        assert not list(self.root.iterdir())


if __name__ == "__main__":
    unittest.main()
