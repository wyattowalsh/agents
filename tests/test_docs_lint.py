"""Tests for docs verbosity lint."""

from pathlib import Path

from wagents.docs_lint import lint_docs_content


def _write(tmp_path: Path, rel: str, body: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_detects_duplicate_dispatch_above_details(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.docs_lint.CONTENT_DIR", tmp_path)
    body = (
        "---\ntitle: x\n---\n{/* HAND-MAINTAINED */}\n"
        "## Dispatch\n| a | b |\n"
        "<details><summary>s</summary>\n## Dispatch\nbody\n</details>\n"
    )
    _write(tmp_path, "skills/catalog/custom/example.mdx", body)
    report = lint_docs_content()
    rules = [f.rule for f in report.findings]
    assert "duplicate-section" in rules


def test_detects_forbidden_boilerplate(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.docs_lint.CONTENT_DIR", tmp_path)
    _write(tmp_path, "index.mdx", "---\ntitle: Home\n---\n## Related Pages\n")
    report = lint_docs_content()
    assert any(f.rule == "forbidden-boilerplate" for f in report.findings)


def test_line_cap_for_generated_skill(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.docs_lint.CONTENT_DIR", tmp_path)
    lines = "---\ntitle: x\n---\n" + "\n".join(f"line {i}" for i in range(700))
    _write(tmp_path, "skills/catalog/custom/big.mdx", lines)
    report = lint_docs_content()
    assert any(f.rule == "line-cap" for f in report.findings)
