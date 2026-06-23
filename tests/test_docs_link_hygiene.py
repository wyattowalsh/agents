"""Golden tests: generated skill catalog prose must not emit invalid markdown links."""

import re

from wagents.catalog import CatalogNode
from wagents.rendering import render_skill_page

_BAD_LINK = re.compile(r"(?<![`])\[[^\]]+\]\((?:#|references/|assets/|[^)/\s#]+\.(?:md|py|go|ts|js|json|yaml)(?:#|\)))")


def _prose_outside_details(mdx: str) -> str:
    if "<details>" in mdx:
        return mdx.split("<details>", 1)[0]
    return mdx


def _node(body: str, *, source: str = "installed") -> CatalogNode:
    return CatalogNode(
        kind="skill",
        id="fixture-skill",
        title="Fixture Skill",
        description="Fixture skill for link hygiene tests.",
        metadata={"name": "fixture-skill", "user-invocable": True},
        body=body,
        source_path="/tmp/fixture/SKILL.md",
        source=source,
    )


class TestDocsLinkHygiene:
    def test_aws_serverless_routing_skipped_for_installed(self):
        body = (
            "---\nname: aws-serverless\n---\n"
            "# AWS Serverless\n"
            "## Overview\n"
            "\n"
            "Domain expertise for serverless on AWS.\n"
            "\n"
            "## Routing\n"
            "| need | action |\n"
            "| --- | --- |\n"
            "| build | Read [architecture.md](references/architecture.md) |\n"
            "| start | Use [handler.py](assets/powertools-handler.py) |\n"
        )
        mdx = render_skill_page(_node(body), [], [])
        prose = _prose_outside_details(mdx)
        assert "## Routing" not in prose
        assert "Domain expertise for serverless on AWS." in prose
        assert _BAD_LINK.search(prose) is None

    def test_golang_cli_asset_links_neutralized_in_prose(self):
        body = "# Golang CLI\n\n## Core Principles\n\nSee [main.go](assets/examples/main.go) for layout.\n"
        mdx = render_skill_page(_node(body), [], [])
        prose = _prose_outside_details(mdx)
        assert "`main.go`" in prose
        assert _BAD_LINK.search(prose) is None

    def test_custom_routing_table_links_neutralized(self):
        body = (
            "# Custom Skill\n\n## Routing\n\n| need | doc |\n| --- | --- |\n| debug | [guide](references/guide.md) |\n"
        )
        mdx = render_skill_page(_node(body, source="custom"), [], [])
        prose = _prose_outside_details(mdx)
        assert "## Routing" in prose
        assert "`guide`" in prose
        assert _BAD_LINK.search(prose) is None
