"""Tests for email-whiz memory module."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# Add scripts directory to path so we can import the module
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "scripts")
)

import memory

runner = CliRunner()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_paths(tmp_path, monkeypatch):
    """Redirect all memory paths to tmp_path for every test."""
    memory_dir = str(tmp_path)
    memory_file = str(tmp_path / "memory.json")
    monkeypatch.setattr(memory, "MEMORY_DIR", memory_dir)
    monkeypatch.setattr(memory, "MEMORY_FILE", memory_file)


@pytest.fixture()
def frozen_today():
    """Return a fixed date for deterministic testing."""
    return date(2026, 3, 15)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _invoke(*args: str) -> dict:
    """Invoke a CLI command and parse JSON stdout."""
    result = runner.invoke(memory.app, list(args))
    assert result.exit_code == 0, f"exit_code={result.exit_code}\n{result.output}"
    return json.loads(result.output)


def _invoke_expect_error(*args: str) -> dict:
    """Invoke a CLI command that is expected to fail and parse JSON stdout."""
    result = runner.invoke(memory.app, list(args))
    assert result.exit_code != 0, f"Expected failure but got exit_code=0\n{result.output}"
    return json.loads(result.output)


# ---------------------------------------------------------------------------
# _empty_memory / load_memory / save_memory
# ---------------------------------------------------------------------------


class TestEmptyMemory:
    def test_returns_base_structure(self):
        m = memory._empty_memory()
        assert m["version"] == 1
        assert m["correction_sequence"] == 0
        assert m["senders"] == {"vip": [], "noise": []}
        assert m["triage"] == {"overrides": []}
        assert m["corrections"] == []
        assert m["filters"] == {"effective": [], "failed": []}
        assert m["labels"] == {}
        assert m["inbox_patterns"] == {}
        assert "updated_at" in m


class TestLoadSaveRoundTrip:
    def test_load_returns_empty_when_no_file(self):
        data = memory.load_memory()
        assert data["version"] == 1
        assert data["senders"] == {"vip": [], "noise": []}
        assert data["corrections"] == []

    def test_save_then_load(self):
        data = memory.load_memory()
        data["senders"]["vip"].append({"email": "boss@co.com", "reason": "boss"})
        memory.save_memory(data)

        loaded = memory.load_memory()
        assert len(loaded["senders"]["vip"]) == 1
        assert loaded["senders"]["vip"][0]["email"] == "boss@co.com"

    def test_corrupt_json_returns_empty(self, tmp_path):
        Path(memory.MEMORY_FILE).write_text("{{not valid json!!!")
        data = memory.load_memory()
        assert data["version"] == 1
        assert data["senders"] == {"vip": [], "noise": []}

    def test_load_fills_missing_keys(self, tmp_path):
        """A JSON file missing some top-level keys gets them filled in."""
        Path(memory.MEMORY_FILE).write_text(json.dumps({"version": 1}))
        data = memory.load_memory()
        assert data["senders"] == {"vip": [], "noise": []}
        assert data["corrections"] == []

    def test_non_dict_json_returns_empty(self, tmp_path):
        """A JSON file containing null/list/string returns empty structure."""
        Path(memory.MEMORY_FILE).write_text("null")
        data = memory.load_memory()
        assert data["version"] == 1
        assert data["senders"] == {"vip": [], "noise": []}

    def test_nested_null_replaced_with_defaults(self, tmp_path):
        """A JSON file with null nested values gets them replaced."""
        Path(memory.MEMORY_FILE).write_text(json.dumps({
            "version": 1,
            "senders": None,
            "triage": {"overrides": None},
            "filters": {"effective": [], "failed": None},
        }))
        data = memory.load_memory()
        assert data["senders"] == {"vip": [], "noise": []}
        assert data["triage"] == {"overrides": []}
        assert isinstance(data["filters"]["failed"], list)

    def test_correction_sequence_migrated_from_existing_ids(self, tmp_path):
        """Loading a file without correction_sequence sets it from max existing ID."""
        Path(memory.MEMORY_FILE).write_text(json.dumps({
            "version": 1,
            "senders": {"vip": [], "noise": []},
            "triage": {"overrides": []},
            "corrections": [{"id": "C-003"}, {"id": "C-007"}],
            "filters": {"effective": [], "failed": []},
            "labels": {},
            "inbox_patterns": {},
        }))
        data = memory.load_memory()
        assert data["correction_sequence"] == 7

    def test_save_is_atomic(self, tmp_path):
        """After save_memory, exactly one memory file exists (no leftover .tmp)."""
        memory.save_memory(memory._empty_memory())
        json_files = list(tmp_path.glob("*.json"))
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(json_files) == 1
        assert len(tmp_files) == 0


# ---------------------------------------------------------------------------
# _next_correction_id
# ---------------------------------------------------------------------------


class TestNextCorrectionId:
    def test_first_id_from_zero(self):
        data = {"correction_sequence": 0}
        assert memory._next_correction_id(data) == "C-001"
        assert data["correction_sequence"] == 1

    def test_increments_monotonically(self):
        data = {"correction_sequence": 5}
        assert memory._next_correction_id(data) == "C-006"
        assert data["correction_sequence"] == 6

    def test_never_reuses_after_prune(self):
        """After prune removes high IDs, sequence counter keeps incrementing."""
        data = {"correction_sequence": 10}
        assert memory._next_correction_id(data) == "C-011"
        assert data["correction_sequence"] == 11

    def test_missing_sequence_defaults_to_zero(self):
        data = {}
        assert memory._next_correction_id(data) == "C-001"
        assert data["correction_sequence"] == 1


# ---------------------------------------------------------------------------
# _file_size_warning
# ---------------------------------------------------------------------------


class TestFileSizeWarning:
    def test_no_warning_small_file(self):
        memory.save_memory(memory._empty_memory())
        assert memory._file_size_warning({}) is None

    def test_warning_large_file(self, tmp_path):
        """File larger than 50KB should trigger warning."""
        Path(memory.MEMORY_FILE).write_text("x" * (51 * 1024))
        result = memory._file_size_warning({})
        assert result is not None
        assert "warning" in result
        assert "50KB" in result["warning"]


# ---------------------------------------------------------------------------
# CLI: save-sender round-trip and upsert
# ---------------------------------------------------------------------------


class TestSaveSender:
    def test_save_vip(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "my boss",
                "--source", "triage",
            )
        assert result["status"] == "saved"
        assert result["type"] == "vip"

        loaded = _invoke("load", "--topic", "senders")
        assert len(loaded["memory"]["senders"]["vip"]) == 1
        assert loaded["memory"]["senders"]["vip"][0]["email"] == "boss@co.com"

    def test_save_noise(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-sender",
                "--email", "spam@junk.com",
                "--type", "noise",
                "--reason", "promotional",
                "--source", "auto-scan",
            )
        assert result["status"] == "saved"
        assert result["type"] == "noise"

        loaded = _invoke("load", "--topic", "senders")
        entry = loaded["memory"]["senders"]["noise"][0]
        assert entry["domain"] == "junk.com"

    def test_upsert_same_email(self, frozen_today):
        """Saving same email twice should update, not duplicate."""
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "my boss",
                "--source", "triage",
                "--confidence", "0.7",
            )
            result = _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "definitely my boss",
                "--source", "triage",
                "--confidence", "0.95",
            )
        assert result["status"] == "updated"

        loaded = _invoke("load", "--topic", "senders")
        vips = loaded["memory"]["senders"]["vip"]
        assert len(vips) == 1
        assert vips[0]["reason"] == "definitely my boss"
        assert vips[0]["confidence"] == 0.95

    def test_save_with_name(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "boss",
                "--source", "triage",
                "--name", "The Boss",
            )
        loaded = _invoke("load", "--topic", "senders")
        assert loaded["memory"]["senders"]["vip"][0]["name"] == "The Boss"


# ---------------------------------------------------------------------------
# CLI: save-override round-trip and upsert
# ---------------------------------------------------------------------------


class TestSaveOverride:
    def test_save_and_load(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-override",
                "--pattern", "from:hr@co.com subject:survey",
                "--bucket", "NOISE",
                "--reason", "always irrelevant",
            )
        assert result["status"] == "saved"
        assert result["bucket"] == "NOISE"

        loaded = _invoke("load", "--topic", "triage")
        overrides = loaded["memory"]["triage"]["overrides"]
        assert len(overrides) == 1
        assert overrides[0]["pattern"] == "from:hr@co.com subject:survey"

    def test_upsert_same_pattern(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-override",
                "--pattern", "from:hr@co.com",
                "--bucket", "NOISE",
                "--reason", "irrelevant",
            )
            result = _invoke(
                "save-override",
                "--pattern", "from:hr@co.com",
                "--bucket", "DEFER",
                "--reason", "actually might matter",
            )
        assert result["status"] == "updated"
        assert result["bucket"] == "DEFER"

        loaded = _invoke("load", "--topic", "triage")
        overrides = loaded["memory"]["triage"]["overrides"]
        assert len(overrides) == 1
        assert overrides[0]["bucket"] == "DEFER"


# ---------------------------------------------------------------------------
# CLI: save-correction round-trip and auto-increment
# ---------------------------------------------------------------------------


class TestSaveCorrection:
    def test_save_and_auto_id(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            r1 = _invoke(
                "save-correction",
                "--mode", "triage",
                "--what", "newsletter classified as DO",
                "--correction", "should be NOISE",
                "--pattern", "from:news@example.com",
                "--action", "NOISE",
            )
        assert r1["status"] == "saved"
        assert r1["id"] == "C-001"

        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            r2 = _invoke(
                "save-correction",
                "--mode", "triage",
                "--what", "alert classified as DEFER",
                "--correction", "should be DO",
                "--pattern", "from:alerts@infra.com",
                "--action", "DO",
            )
        assert r2["id"] == "C-002"

    def test_upsert_same_pattern(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-correction",
                "--mode", "triage",
                "--what", "newsletter",
                "--correction", "NOISE",
                "--pattern", "from:news@example.com",
                "--action", "NOISE",
            )
            r2 = _invoke(
                "save-correction",
                "--mode", "triage",
                "--what", "newsletter v2",
                "--correction", "DEFER",
                "--pattern", "from:news@example.com",
                "--action", "DEFER",
            )
        assert r2["status"] == "updated"
        assert r2["id"] == "C-001"

        loaded = _invoke("load", "--topic", "corrections")
        corrections = loaded["memory"]["corrections"]
        assert len(corrections) == 1
        assert corrections[0]["action"] == "DEFER"
        assert corrections[0]["applied_count"] == 1


# ---------------------------------------------------------------------------
# CLI: save-filter
# ---------------------------------------------------------------------------


class TestSaveFilter:
    def test_effective_filter(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-filter",
                "--filter-id", "f-123",
                "--description", "Archive newsletters",
                "--monthly-matches", "50",
                "--effectiveness", "high",
            )
        assert result["status"] == "saved"
        assert result["filter_id"] == "f-123"

        loaded = _invoke("load", "--topic", "filters")
        effective = loaded["memory"]["filters"]["effective"]
        assert len(effective) == 1
        assert effective[0]["monthly_matches"] == 50

    def test_failed_filter(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-filter",
                "--filter-id", "rejected",
                "--description", "Bad filter suggestion",
                "--effectiveness", "failed",
            )
        assert result["status"] == "saved"
        assert result["type"] == "failed"

        loaded = _invoke("load", "--topic", "filters")
        assert len(loaded["memory"]["filters"]["failed"]) == 1

    def test_failed_filter_dedup(self, frozen_today):
        """Saving same failed description twice should produce one entry."""
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-filter",
                "--filter-id", "rejected",
                "--description", "Bad filter",
                "--effectiveness", "failed",
            )
            _invoke(
                "save-filter",
                "--filter-id", "rejected-2",
                "--description", "Bad filter",
                "--effectiveness", "failed",
            )
        loaded = _invoke("load", "--topic", "filters")
        assert len(loaded["memory"]["filters"]["failed"]) == 1

    def test_upsert_effective_filter(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-filter",
                "--filter-id", "f-123",
                "--description", "Archive newsletters",
                "--effectiveness", "medium",
            )
            result = _invoke(
                "save-filter",
                "--filter-id", "f-123",
                "--description", "Archive newsletters v2",
                "--effectiveness", "high",
            )
        assert result["status"] == "updated"

        loaded = _invoke("load", "--topic", "filters")
        effective = loaded["memory"]["filters"]["effective"]
        assert len(effective) == 1
        assert effective[0]["effectiveness"] == "high"
        assert effective[0]["description"] == "Archive newsletters v2"


# ---------------------------------------------------------------------------
# CLI: save-labels
# ---------------------------------------------------------------------------


class TestSaveLabels:
    def test_structure_and_convention(self):
        result = _invoke(
            "save-labels",
            "--structure", "_projects/, _dev/",
            "--convention", "underscore-prefix",
        )
        assert result["status"] == "saved"
        assert result["labels"]["preferred_structure"] == "_projects/, _dev/"
        assert result["labels"]["naming_convention"] == "underscore-prefix"

    def test_avoid_list(self):
        result = _invoke(
            "save-labels",
            "--avoid", '["Old Label", "Deprecated"]',
        )
        assert result["status"] == "saved"
        assert result["labels"]["avoid"] == ["Old Label", "Deprecated"]

    def test_invalid_avoid_json(self):
        result = _invoke_expect_error(
            "save-labels",
            "--avoid", "not json",
        )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# CLI: save-patterns
# ---------------------------------------------------------------------------


class TestSavePatterns:
    def test_daily_volume(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-patterns",
                "--daily-volume", "120",
            )
        assert result["status"] == "saved"
        assert result["inbox_patterns"]["typical_daily_volume"] == 120

    def test_busy_and_quiet(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke(
                "save-patterns",
                "--busy", '["Monday mornings"]',
                "--quiet", '["Weekends"]',
            )
        assert result["inbox_patterns"]["busy_periods"] == ["Monday mornings"]
        assert result["inbox_patterns"]["quiet_periods"] == ["Weekends"]

    def test_invalid_busy_json(self, frozen_today):
        result = _invoke_expect_error(
            "save-patterns",
            "--busy", "not json",
        )
        assert result["status"] == "error"

    def test_invalid_quiet_json(self):
        result = _invoke_expect_error(
            "save-patterns",
            "--quiet", "not json",
        )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# CLI: load --mode
# ---------------------------------------------------------------------------


class TestLoadMode:
    def test_triage_mode_returns_correct_topics(self, frozen_today):
        """Triage mode should return senders, triage, and corrections."""
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "boss",
                "--source", "triage",
            )
            _invoke(
                "save-override",
                "--pattern", "from:spam@junk.com",
                "--bucket", "NOISE",
                "--reason", "spam",
            )

        loaded = _invoke("load", "--mode", "triage")
        mem = loaded["memory"]
        assert "senders" in mem
        assert "triage" in mem
        assert "corrections" in mem
        # Triage mode should NOT include filters, labels, or inbox_patterns
        assert "filters" not in mem
        assert "labels" not in mem
        assert "inbox_patterns" not in mem

    def test_labels_mode(self):
        _invoke("save-labels", "--convention", "slash")
        loaded = _invoke("load", "--mode", "labels")
        assert "labels" in loaded["memory"]
        assert "senders" not in loaded["memory"]

    def test_unknown_mode_errors(self):
        result = _invoke_expect_error("load", "--mode", "nonexistent")
        assert result["status"] == "error"
        assert "Unknown mode" in result["message"]

    def test_load_no_args_returns_all(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "boss",
                "--source", "triage",
            )
        loaded = _invoke("load")
        mem = loaded["memory"]
        assert "senders" in mem
        assert "triage" in mem
        assert "corrections" in mem
        assert "filters" in mem
        assert "labels" in mem
        assert "inbox_patterns" in mem

    def test_load_unknown_topic_errors(self):
        result = _invoke_expect_error("load", "--topic", "nonexistent")
        assert result["status"] == "error"
        assert "Unknown topic" in result["message"]

    @pytest.mark.parametrize("mode,expected_topics", [
        ("triage", {"senders", "triage", "corrections"}),
        ("inbox-zero", {"senders", "triage", "corrections", "inbox_patterns"}),
        ("filters", {"senders", "filters", "corrections"}),
        ("auto-rules", {"senders", "filters", "corrections"}),
        ("analytics", {"inbox_patterns", "senders"}),
        ("senders", {"senders", "corrections"}),
        ("cleanup", {"senders", "triage"}),
        ("newsletters", {"senders", "filters"}),
        ("labels", {"labels"}),
        ("audit", {"senders", "triage", "corrections", "filters", "labels", "inbox_patterns"}),
        ("auto-scan", {"senders", "triage", "corrections", "filters", "labels", "inbox_patterns"}),
        ("search", set()),
        ("digest", set()),
    ])
    def test_load_mode_returns_correct_topics(self, mode, expected_topics):
        """Each mode returns exactly the topics defined in MODE_TOPICS."""
        loaded = _invoke("load", "--mode", mode)
        assert loaded["status"] == "ok"
        assert set(loaded["memory"].keys()) == expected_topics


# ---------------------------------------------------------------------------
# CLI: remove
# ---------------------------------------------------------------------------


class TestRemove:
    def test_remove_sender(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "boss@co.com",
                "--type", "vip",
                "--reason", "boss",
                "--source", "triage",
            )
        result = _invoke("remove", "--topic", "senders", "--email", "boss@co.com")
        assert result["status"] == "removed"

        loaded = _invoke("load", "--topic", "senders")
        assert loaded["memory"]["senders"]["vip"] == []

    def test_remove_correction(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-correction",
                "--mode", "triage",
                "--what", "newsletter",
                "--correction", "NOISE",
                "--pattern", "from:news@co.com",
                "--action", "NOISE",
            )
        result = _invoke("remove", "--topic", "corrections", "--id", "C-001")
        assert result["status"] == "removed"

        loaded = _invoke("load", "--topic", "corrections")
        assert loaded["memory"]["corrections"] == []

    def test_remove_override(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-override",
                "--pattern", "from:hr@co.com",
                "--bucket", "NOISE",
                "--reason", "irrelevant",
            )
        result = _invoke("remove", "--topic", "triage", "--pattern", "from:hr@co.com")
        assert result["status"] == "removed"

    def test_remove_filter(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-filter",
                "--filter-id", "f-123",
                "--description", "Archive newsletters",
                "--effectiveness", "high",
            )
        result = _invoke("remove", "--topic", "filters", "--filter-id", "f-123")
        assert result["status"] == "removed"

        loaded = _invoke("load", "--topic", "filters")
        assert loaded["memory"]["filters"]["effective"] == []

    def test_remove_noise_sender(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "spam@junk.com",
                "--type", "noise",
                "--reason", "spam",
                "--source", "triage",
            )
        result = _invoke("remove", "--topic", "senders", "--email", "spam@junk.com")
        assert result["status"] == "removed"

        loaded = _invoke("load", "--topic", "senders")
        assert loaded["memory"]["senders"]["noise"] == []

    def test_remove_failed_filter(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-filter",
                "--filter-id", "rejected",
                "--description", "Bad suggestion",
                "--effectiveness", "failed",
            )
        result = _invoke("remove", "--topic", "filters", "--filter-id", "rejected")
        assert result["status"] == "removed"

        loaded = _invoke("load", "--topic", "filters")
        assert loaded["memory"]["filters"]["failed"] == []

    def test_remove_not_found(self):
        result = _invoke("remove", "--topic", "senders", "--email", "nobody@co.com")
        assert result["status"] == "not_found"

    def test_remove_invalid_args(self):
        result = _invoke_expect_error("remove", "--topic", "senders")
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# CLI: prune
# ---------------------------------------------------------------------------


class TestPrune:
    def _seed_stale_data(self, frozen_today):
        """Seed memory with entries that are stale (200 days old)."""
        data = memory.load_memory()
        stale_date = (frozen_today - timedelta(days=200)).isoformat()
        fresh_date = frozen_today.isoformat()

        data["senders"]["vip"] = [
            {"email": "stale-vip@co.com", "last_confirmed": stale_date, "reason": "old"},
            {"email": "fresh-vip@co.com", "last_confirmed": fresh_date, "reason": "current"},
        ]
        data["senders"]["noise"] = [
            {"email": "stale-noise@co.com", "last_confirmed": stale_date, "reason": "old"},
        ]
        data["triage"]["overrides"] = [
            {"pattern": "from:stale@co.com", "last_used": stale_date, "bucket": "NOISE"},
            {"pattern": "from:fresh@co.com", "last_used": fresh_date, "bucket": "DO"},
        ]
        data["corrections"] = [
            {"id": "C-001", "last_used": stale_date, "pattern": "old-pattern"},
            {"id": "C-002", "last_used": fresh_date, "pattern": "new-pattern"},
        ]
        memory.save_memory(data)

    def test_prune_removes_stale(self, frozen_today):
        self._seed_stale_data(frozen_today)

        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke("prune")

        assert result["status"] == "pruned"
        assert result["total_removed"] == 4  # 1 vip + 1 noise + 1 override + 1 correction (all 200 days old)

        # Verify fresh entries remain
        loaded = _invoke("load", "--topic", "senders")
        assert len(loaded["memory"]["senders"]["vip"]) == 1
        assert loaded["memory"]["senders"]["vip"][0]["email"] == "fresh-vip@co.com"
        assert loaded["memory"]["senders"]["noise"] == []

    def test_prune_dry_run_no_modification(self, frozen_today):
        self._seed_stale_data(frozen_today)

        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke("prune", "--dry-run")

        assert result["status"] == "dry_run"
        assert result["total_removed"] > 0

        # File should still have all entries
        loaded = _invoke("load", "--topic", "senders")
        assert len(loaded["memory"]["senders"]["vip"]) == 2
        assert len(loaded["memory"]["senders"]["noise"]) == 1

    def test_prune_nothing_stale(self, frozen_today):
        """When nothing is stale, prune should remove 0."""
        data = memory.load_memory()
        fresh_date = frozen_today.isoformat()
        data["senders"]["vip"] = [
            {"email": "fresh@co.com", "last_confirmed": fresh_date, "reason": "current"},
        ]
        memory.save_memory(data)

        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke("prune")

        assert result["total_removed"] == 0

    def test_prune_entry_without_date_is_stale(self, frozen_today):
        """Entries missing the date field should be considered stale."""
        data = memory.load_memory()
        data["senders"]["vip"] = [{"email": "nodate@co.com", "reason": "no date"}]
        memory.save_memory(data)

        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke("prune")

        assert result["total_removed"] == 1

    def test_prune_custom_thresholds(self, frozen_today):
        """Custom stale-days thresholds should be respected."""
        data = memory.load_memory()
        # 50 days old — within default 90 but outside custom 30
        borderline_date = (frozen_today - timedelta(days=50)).isoformat()
        data["senders"]["vip"] = [
            {"email": "borderline@co.com", "last_confirmed": borderline_date, "reason": "test"},
        ]
        memory.save_memory(data)

        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.fromisoformat = date.fromisoformat
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = _invoke("prune", "--vip-stale-days", "30")

        assert result["total_removed"] == 1


# ---------------------------------------------------------------------------
# CLI: stats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats_empty(self):
        result = _invoke("stats")
        assert result["status"] == "ok"
        assert result["counts"]["vip_senders"] == 0
        assert result["counts"]["noise_senders"] == 0
        assert result["counts"]["triage_overrides"] == 0
        assert result["counts"]["corrections"] == 0
        assert result["counts"]["effective_filters"] == 0
        assert result["counts"]["failed_filters"] == 0
        assert result["counts"]["has_label_prefs"] is False
        assert result["counts"]["has_inbox_patterns"] is False

    def test_stats_oldest_uses_created_fallback(self):
        """When entries have 'created' but no 'first_seen', oldest_entry uses the fallback."""
        data = memory.load_memory()
        data["triage"]["overrides"] = [
            {"pattern": "from:old@co.com", "created": "2025-01-01", "last_used": "2026-03-01", "bucket": "NOISE"},
        ]
        data["corrections"] = [
            {"id": "C-001", "created": "2025-06-01", "last_used": "2026-03-01", "pattern": "x"},
        ]
        memory.save_memory(data)

        result = _invoke("stats")
        assert result["oldest_entry"] == "2025-01-01"

    def test_stats_with_data(self, frozen_today):
        with patch.object(memory, "date") as mock_date:
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            _invoke(
                "save-sender",
                "--email", "vip@co.com",
                "--type", "vip",
                "--reason", "important",
                "--source", "triage",
            )
            _invoke(
                "save-sender",
                "--email", "noise@junk.com",
                "--type", "noise",
                "--reason", "spam",
                "--source", "auto-scan",
            )
            _invoke(
                "save-correction",
                "--mode", "triage",
                "--what", "newsletter",
                "--correction", "NOISE",
                "--pattern", "from:news@co.com",
                "--action", "NOISE",
            )

        result = _invoke("stats")
        assert result["counts"]["vip_senders"] == 1
        assert result["counts"]["noise_senders"] == 1
        assert result["counts"]["corrections"] == 1


# ---------------------------------------------------------------------------
# Invalid enum values
# ---------------------------------------------------------------------------


class TestInvalidEnums:
    def test_invalid_sender_type(self):
        result = runner.invoke(memory.app, [
            "save-sender",
            "--email", "x@y.com",
            "--type", "INVALID",
            "--reason", "test",
            "--source", "test",
        ])
        assert result.exit_code != 0

    def test_invalid_bucket(self):
        result = runner.invoke(memory.app, [
            "save-override",
            "--pattern", "from:x@y.com",
            "--bucket", "INVALID",
            "--reason", "test",
        ])
        assert result.exit_code != 0

    def test_invalid_effectiveness(self):
        result = runner.invoke(memory.app, [
            "save-filter",
            "--filter-id", "f-1",
            "--description", "test",
            "--effectiveness", "INVALID",
        ])
        assert result.exit_code != 0
