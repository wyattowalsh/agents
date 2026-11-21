"""Keep the portable Files Buddy regression suite in the repository CI gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_files_buddy_behavioral_suite() -> None:
    skill = Path(__file__).resolve().parents[1] / "skills" / "files-buddy"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=skill,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
