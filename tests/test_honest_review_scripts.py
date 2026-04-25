from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "honest-review" / "scripts"


def load_script(name: str) -> ModuleType:
    path = SCRIPT_DIR / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_honest_review_scripts_are_importable() -> None:
    for script in [
        "finding-formatter.py",
        "learnings-store.py",
        "project-scanner.py",
        "review-store.py",
        "sarif-uploader.py",
    ]:
        load_script(script)


def test_project_scanner_skips_virtualenv_prefixes(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = []\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def app() -> str:\n    return 'ok'\n")
    (tmp_path / ".venv-copilot" / "lib").mkdir(parents=True)
    (tmp_path / ".venv-copilot" / "lib" / "vendor.py").write_text("def vendor():\n    return None\n")

    scanner = load_script("project-scanner.py")
    result = scanner.scan(tmp_path)
    paths = {entry["path"] for entry in result["files"]}

    assert "src/app.py" in paths
    assert not any(path.startswith(".venv-copilot/") for path in paths)
