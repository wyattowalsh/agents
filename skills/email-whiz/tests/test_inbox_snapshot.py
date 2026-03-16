"""Tests for email-whiz inbox_snapshot module."""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path so we can import the module
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "scripts")
)

import inbox_snapshot

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_paths(tmp_path, monkeypatch):
    """Redirect all snapshot/cache paths to tmp_path for every test."""
    snapshot_dir = str(tmp_path)
    snapshot_file = str(tmp_path / "snapshots.json")
    cache_file = str(tmp_path / "session-cache.json")
    monkeypatch.setattr(inbox_snapshot, "SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(inbox_snapshot, "SNAPSHOT_FILE", snapshot_file)
    monkeypatch.setattr(inbox_snapshot, "CACHE_FILE", cache_file)


@pytest.fixture()
def frozen_today():
    """Return a fixed date for deterministic testing."""
    return date(2026, 3, 15)


@pytest.fixture()
def frozen_now():
    """Return a fixed datetime for deterministic testing."""
    return datetime(2026, 3, 15, 10, 30, 0)


# ---------------------------------------------------------------------------
# save_snapshot / load_snapshots round-trip
# ---------------------------------------------------------------------------


class TestSaveLoadRoundTrip:
    def test_save_and_load_single(self, frozen_today, frozen_now):
        with (
            patch.object(inbox_snapshot, "date") as mock_date,
            patch.object(inbox_snapshot, "datetime") as mock_dt,
        ):
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            mock_dt.now.return_value = frozen_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            snapshot = inbox_snapshot.save_snapshot(42, 7)

        assert snapshot["inbox_count"] == 42
        assert snapshot["unread_count"] == 7
        assert snapshot["date"] == "2026-03-15"
        assert snapshot["timestamp"] == frozen_now.isoformat()

        loaded = inbox_snapshot.load_snapshots()
        assert len(loaded) == 1
        assert loaded[0]["inbox_count"] == 42
        assert loaded[0]["unread_count"] == 7
        assert loaded[0]["date"] == "2026-03-15"

    def test_save_replaces_same_day(self, frozen_today, frozen_now):
        with (
            patch.object(inbox_snapshot, "date") as mock_date,
            patch.object(inbox_snapshot, "datetime") as mock_dt,
        ):
            mock_date.today.return_value = frozen_today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            mock_dt.now.return_value = frozen_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            inbox_snapshot.save_snapshot(10, 2)
            inbox_snapshot.save_snapshot(20, 5)

        loaded = inbox_snapshot.load_snapshots()
        assert len(loaded) == 1
        assert loaded[0]["inbox_count"] == 20

    def test_load_returns_empty_when_no_file(self):
        assert inbox_snapshot.load_snapshots() == []


# ---------------------------------------------------------------------------
# compute_trend
# ---------------------------------------------------------------------------


class TestComputeTrend:
    def _seed_snapshots(self, counts, base_date=None):
        """Helper: seed snapshots with given inbox_count values, one per day."""
        if base_date is None:
            base_date = date(2026, 3, 15)
        snapshots = []
        for i, count in enumerate(counts):
            d = base_date - timedelta(days=len(counts) - 1 - i)
            snapshots.append({
                "date": d.isoformat(),
                "timestamp": datetime(d.year, d.month, d.day, 12, 0).isoformat(),
                "inbox_count": count,
                "unread_count": 0,
            })
        inbox_snapshot.save_snapshots(snapshots)

    def test_growing_trend(self):
        base = date(2026, 3, 15)
        self._seed_snapshots([100, 110, 120, 130, 140, 150, 160], base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_trend(7)
        assert result["trend"] == "growing"
        assert result["delta"] == 60

    def test_stable_trend(self):
        base = date(2026, 3, 15)
        self._seed_snapshots([100, 101, 99, 100, 100, 101, 100], base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_trend(7)
        assert result["trend"] == "stable"

    def test_declining_trend(self):
        base = date(2026, 3, 15)
        self._seed_snapshots([200, 180, 160, 140, 120, 100, 80], base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_trend(7)
        assert result["trend"] == "declining"
        assert result["delta"] == -120

    def test_zero_baseline_growing(self):
        """first=0, last=500 should be 'growing', not 'stable'."""
        base = date(2026, 3, 15)
        self._seed_snapshots([0, 100, 200, 300, 400, 500], base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_trend(7)
        assert result["trend"] == "growing"
        assert result["first_count"] == 0
        assert result["last_count"] == 500

    def test_single_element_stable(self):
        base = date(2026, 3, 15)
        self._seed_snapshots([42], base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_trend(7)
        assert result["trend"] == "stable"

    def test_empty_no_data(self):
        base = date(2026, 3, 15)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_trend(7)
        assert result["trend"] == "no_data"
        assert result["snapshots"] == []


# ---------------------------------------------------------------------------
# save_cache / load_cache / clear_cache
# ---------------------------------------------------------------------------


class TestCache:
    def test_round_trip(self, frozen_now):
        with patch.object(inbox_snapshot, "datetime") as mock_dt:
            mock_dt.now.return_value = frozen_now
            mock_dt.fromisoformat = datetime.fromisoformat
            saved = inbox_snapshot.save_cache(
                labels='["INBOX", "UNREAD"]',
                filters='[{"id": "1"}]',
                inbox_count=42,
                unread_count=5,
                tier="moderate",
            )

        assert saved["inbox_count"] == 42
        assert saved["unread_count"] == 5
        assert saved["tier"] == "moderate"
        assert saved["labels"] == ["INBOX", "UNREAD"]
        assert saved["filters"] == [{"id": "1"}]

        with patch.object(inbox_snapshot, "datetime") as mock_dt:
            mock_dt.now.return_value = frozen_now
            mock_dt.fromisoformat = datetime.fromisoformat
            loaded = inbox_snapshot.load_cache(ttl_minutes=60)

        assert loaded is not None
        assert loaded["inbox_count"] == 42
        assert loaded["unread_count"] == 5
        assert loaded["tier"] == "moderate"

    def test_ttl_expiry(self, tmp_path, frozen_now):
        """Cache saved 2 hours ago should be expired with 60 min TTL."""
        two_hours_ago = frozen_now - timedelta(hours=2)
        with patch.object(inbox_snapshot, "datetime") as mock_dt:
            mock_dt.now.return_value = two_hours_ago
            mock_dt.fromisoformat = datetime.fromisoformat
            inbox_snapshot.save_cache(
                labels="[]", filters="[]",
                inbox_count=10, unread_count=1, tier="light",
            )

        with patch.object(inbox_snapshot, "datetime") as mock_dt:
            mock_dt.now.return_value = frozen_now
            mock_dt.fromisoformat = datetime.fromisoformat
            loaded = inbox_snapshot.load_cache(ttl_minutes=60)

        assert loaded is None

    def test_malformed_cache_file(self, tmp_path):
        """Invalid JSON in cache file should return None, not crash."""
        cache_path = Path(inbox_snapshot.CACHE_FILE)
        cache_path.write_text("not valid json {{{")
        loaded = inbox_snapshot.load_cache(ttl_minutes=60)
        assert loaded is None

    def test_missing_key(self, tmp_path):
        """JSON missing 'last_fetched' key should return None."""
        cache_path = Path(inbox_snapshot.CACHE_FILE)
        cache_path.write_text(json.dumps({"labels": [], "filters": []}))
        loaded = inbox_snapshot.load_cache(ttl_minutes=60)
        assert loaded is None

    def test_clear_removes_cache(self, frozen_now):
        with patch.object(inbox_snapshot, "datetime") as mock_dt:
            mock_dt.now.return_value = frozen_now
            mock_dt.fromisoformat = datetime.fromisoformat
            inbox_snapshot.save_cache(
                labels="[]", filters="[]",
                inbox_count=1, unread_count=0, tier="light",
            )

        assert inbox_snapshot.clear_cache() is True

        with patch.object(inbox_snapshot, "datetime") as mock_dt:
            mock_dt.now.return_value = frozen_now
            mock_dt.fromisoformat = datetime.fromisoformat
            loaded = inbox_snapshot.load_cache(ttl_minutes=60)

        assert loaded is None

    def test_clear_when_no_cache(self):
        assert inbox_snapshot.clear_cache() is False


# ---------------------------------------------------------------------------
# compute_baseline
# ---------------------------------------------------------------------------


class TestComputeBaseline:
    def _seed_snapshots(self, counts, base_date=None):
        """Helper: seed snapshots with given inbox_count values, one per day."""
        if base_date is None:
            base_date = date(2026, 3, 15)
        snapshots = []
        for i, count in enumerate(counts):
            d = base_date - timedelta(days=len(counts) - 1 - i)
            snapshots.append({
                "date": d.isoformat(),
                "timestamp": datetime(d.year, d.month, d.day, 12, 0).isoformat(),
                "inbox_count": count,
                "unread_count": 0,
            })
        inbox_snapshot.save_snapshots(snapshots)

    def test_normal_30_snapshots(self):
        base = date(2026, 3, 15)
        counts = list(range(10, 40))  # 30 values: 10..39
        self._seed_snapshots(counts, base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_baseline(days=30)

        assert result["baseline"] is not None
        assert result["snapshots"] == 30
        assert result["min"] == 10
        assert result["max"] == 39
        assert "wow_growth_pct" in result
        # With monotonically increasing values, wow_growth should be positive
        assert result["wow_growth_pct"] > 0

    def test_sparse_5_snapshots(self):
        """Fewer than 14 snapshots: wow_growth should be 0.0."""
        base = date(2026, 3, 15)
        counts = [50, 55, 60, 65, 70]
        self._seed_snapshots(counts, base)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_baseline(days=30)

        assert result["baseline"] is not None
        assert result["snapshots"] == 5
        assert result["wow_growth_pct"] == 0.0
        assert result["min"] == 50
        assert result["max"] == 70

    def test_empty_history(self):
        base = date(2026, 3, 15)
        with patch.object(inbox_snapshot, "date") as mock_date:
            mock_date.today.return_value = base
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            result = inbox_snapshot.compute_baseline(days=30)

        assert result["baseline"] is None
        assert result["fallback"] == 500
        assert result["snapshots"] == 0
