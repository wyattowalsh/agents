"""Regression tests for yt-dlp skill helper scripts."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "skills" / "yt-dlp" / "scripts"


def _load_module(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_module("yt_dlp_doctor", "doctor.py")
probe_url = _load_module("yt_dlp_probe_url", "probe_url.py")


def _run_doctor(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "doctor.py"), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_doctor_json_shape_with_stubbed_binaries(monkeypatch) -> None:
    def fake_which(name: str) -> str | None:
        if name in {"yt-dlp", "ffmpeg"}:
            return f"/usr/local/bin/{name}"
        return None

    monkeypatch.setattr(doctor.shutil, "which", fake_which)
    monkeypatch.setattr(doctor, "_run_version", lambda _binary, _args, timeout=15: (0, "2026.01.01"))

    report = doctor.build_report(doctor.collect_checks())

    assert report["ok"] is True
    assert report["summary"]["total"] == 3
    names = {check["name"] for check in report["checks"]}
    assert names == {"yt-dlp-binary", "yt-dlp-version", "ffmpeg-binary"}


def test_doctor_cli_emits_json() -> None:
    result = _run_doctor("--format", "json")
    payload = json.loads(result.stdout)

    assert "ok" in payload
    assert "summary" in payload
    assert "checks" in payload
    if shutil.which("yt-dlp") is not None:
        assert {check["name"] for check in payload["checks"]} == {
            "yt-dlp-binary",
            "yt-dlp-version",
            "ffmpeg-binary",
        }


def test_probe_url_cookies_expanduser(monkeypatch, tmp_path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    cookies_dir = home / ".config" / "yt-dlp"
    cookies_dir.mkdir(parents=True)
    cookie_file = cookies_dir / "cookies.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))

    captured: dict[str, Path | None] = {}

    def fake_probe_url(
        url: str,
        *,
        cookies: Path | None = None,
        allow_playlist: bool = False,
        timeout: int = 120,
    ) -> dict:
        captured["cookies"] = cookies
        return {
            "ok": True,
            "url": url,
            "entry_count": 1,
            "info": {},
            "summary": {},
        }

    monkeypatch.setattr(probe_url, "probe_url", fake_probe_url)

    rc = probe_url.main(
        [
            "--url",
            "https://www.youtube.com/watch?v=example",
            "--cookies",
            "~/.config/yt-dlp/cookies.txt",
        ]
    )

    assert rc == 0
    assert captured["cookies"] == cookie_file.resolve()


def test_probe_url_cli_includes_allow_playlist() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "probe_url.py"), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--allow-playlist" in result.stdout


def test_doctor_missing_yt_dlp_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: None)

    report = doctor.build_report(doctor.collect_checks())

    assert report["ok"] is False
    yt_check = next(c for c in report["checks"] if c["name"] == "yt-dlp-binary")
    assert yt_check["status"] == "fail"
    ffmpeg_check = next(c for c in report["checks"] if c["name"] == "ffmpeg-binary")
    assert ffmpeg_check["status"] == "warn"