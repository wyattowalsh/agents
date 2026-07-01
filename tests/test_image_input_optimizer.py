from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from wagents import image_inputs
from wagents.image_inputs import ImageOptimizationError, SourceIdentity, optimize_image_path


def test_optimizer_resizes_screenshot_text_profile_without_mutating_source(tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")

    result = optimize_image_path(source, context="ui screenshot with text", cache_dir=tmp_path / "cache").to_json()

    assert result["status"] == "optimized"
    assert result["profile"] == "screenshot-text"
    assert result["changed"] is True
    assert result["fits"] is True
    assert result["optimizedPath"] != str(source)
    assert Path(result["optimizedPath"]).exists()
    assert result["optimizedWidth"] <= 3000
    assert result["optimizedWidth"] * result["optimizedHeight"] <= 8000000
    with Image.open(source) as original:
        assert original.size == (4200, 2800)


def test_optimizer_preserves_transparent_profile_as_png(tmp_path):
    source = tmp_path / "transparent-logo.png"
    Image.new("RGBA", (3600, 1200), (200, 80, 40, 96)).save(source, format="PNG")

    result = optimize_image_path(source, cache_dir=tmp_path / "cache").to_json()

    assert result["profile"] == "transparent"
    assert result["optimizedFormat"] == "PNG"
    assert result["optimizedWidth"] <= 3000
    with Image.open(result["optimizedPath"]) as optimized:
        assert "A" in optimized.getbands()


def test_optimizer_check_only_reports_without_writing_cache(tmp_path):
    source = tmp_path / "large-photo.jpg"
    Image.new("RGB", (5000, 3500), (10, 20, 30)).save(source, format="JPEG", quality=95)

    result = optimize_image_path(source, cache_dir=tmp_path / "cache", check_only=True).to_json()

    assert result["status"] == "would-optimize"
    assert result["changed"] is True
    assert result["optimizedPath"] is None
    assert not (tmp_path / "cache").exists()


def test_optimizer_rejects_symlink_cache_hit(tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    cache = tmp_path / "cache"
    result = optimize_image_path(source, context="ui screenshot", cache_dir=cache).to_json()
    optimized = Path(result["optimizedPath"])
    optimized.unlink()
    outside = tmp_path / "outside.jpg"
    Image.new("RGB", (32, 32), (1, 2, 3)).save(outside, format="JPEG")
    optimized.symlink_to(outside)

    with pytest.raises(ImageOptimizationError, match="symlink"):
        optimize_image_path(source, context="ui screenshot", cache_dir=cache)


def test_optimizer_rejects_symlink_cache_root(tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    outside = tmp_path / "outside-cache"
    outside.mkdir()
    cache = tmp_path / "cache"
    cache.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ImageOptimizationError, match="symlink"):
        optimize_image_path(source, context="ui screenshot", cache_dir=cache)


def test_optimizer_rejects_symlink_source_path(tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    link = tmp_path / "source-link.png"
    link.symlink_to(source)

    with pytest.raises(ImageOptimizationError, match="symlink"):
        optimize_image_path(link, context="ui screenshot", cache_dir=tmp_path / "cache")


def test_optimizer_rejects_source_identity_mismatch(tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    file_stat = source.stat()
    stale_identity = SourceIdentity(
        device=file_stat.st_dev,
        inode=file_stat.st_ino,
        size=file_stat.st_size + 1,
        mtime_ns=file_stat.st_mtime_ns,
    )

    with pytest.raises(ImageOptimizationError, match="changed before optimization"):
        optimize_image_path(
            source,
            context="ui screenshot",
            cache_dir=tmp_path / "cache",
            expected_identity=stale_identity,
        )


def test_optimizer_writes_private_cache_permissions(tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    cache = tmp_path / "cache"

    result = optimize_image_path(source, context="ui screenshot", cache_dir=cache).to_json()
    optimized = Path(result["optimizedPath"])

    assert cache.stat().st_mode & 0o077 == 0
    assert optimized.parent.stat().st_mode & 0o077 == 0
    assert optimized.stat().st_mode & 0o077 == 0


def test_optimizer_validates_cache_file_after_successful_link(monkeypatch, tmp_path):
    source = tmp_path / "ui-screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    calls: list[Path] = []
    original = image_inputs._validate_cache_file

    def wrapped(path: Path, cache_root: Path) -> None:
        calls.append(path)
        original(path, cache_root)

    monkeypatch.setattr(image_inputs, "_validate_cache_file", wrapped)

    result = optimize_image_path(source, context="ui screenshot", cache_dir=tmp_path / "cache").to_json()

    assert Path(result["optimizedPath"]) in calls
