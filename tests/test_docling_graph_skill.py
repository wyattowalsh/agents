from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "docling-graph"


def load_script(name: str):
    path = SKILL_DIR / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_lint_template_accepts_stable_graph_template(tmp_path: Path) -> None:
    template = tmp_path / "template.py"
    template.write_text(
        '''
from pydantic import BaseModel, ConfigDict, Field
from docling_graph.utils import edge


class Organization(BaseModel):
    """An organization named in the document."""

    model_config = ConfigDict(json_schema_extra={"graph_id_fields": ["name"]})

    name: str = Field(description="Canonical organization name")


class FilingGraph(BaseModel):
    """Graph for one filing."""

    model_config = ConfigDict(json_schema_extra={"graph_id_fields": ["accession_number"]})

    accession_number: str = Field(description="Accession number")
    issuer: Organization = Field(description=edge("issued_by", "Primary issuer"))
''',
        encoding="utf-8",
    )

    lint_template = load_script("lint-template.py")
    report = lint_template.analyze(template, root="FilingGraph")

    assert report["ok"] is True
    assert report["root_model_candidates"] == ["FilingGraph"]
    codes = {finding["code"] for finding in report["findings"]}
    assert "missing-stable-id" not in codes
    assert "missing-field-description" not in codes


def test_lint_template_flags_contract_risks(tmp_path: Path) -> None:
    template = tmp_path / "template.py"
    template.write_text(
        '''
from typing import Any
from pydantic import BaseModel, Field


class Company(BaseModel):
    name: str = Field()
    metadata: dict[str, Any] = Field(description="Loose metadata")


class RootGraph(BaseModel):
    items: list[list[Company]] = Field(description="Nested observed companies")
''',
        encoding="utf-8",
    )

    lint_template = load_script("lint-template.py")
    report = lint_template.analyze(template, root="RootGraph")

    codes = {finding["code"] for finding in report["findings"]}
    assert "missing-stable-id" in codes
    assert "missing-field-description" in codes
    assert "loose-graph-field" in codes
    assert "deep-list-nesting" in codes
    assert "high-cardinality-field" in codes
    assert report["staged_delta_risks"]


def test_check_env_redacts_provider_secrets(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    check_env = load_script("check-env.py")

    report = check_env.build_report(
        Namespace(
            template=None,
            provider=["openai"],
            provider_env=["OPENAI_API_KEY"],
            check_cli_help=False,
            format="json",
        )
    )

    encoded = json.dumps(report)
    assert "sk-secret-value" not in encoded
    assert report["providers"][0]["ok"] is True
    assert report["providers"][0]["env"]["OPENAI_API_KEY"] == "set"
    assert report["provider_env"][0]["status"] == "set"
