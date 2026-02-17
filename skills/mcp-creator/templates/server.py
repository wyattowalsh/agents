"""Minimal FastMCP v3 server template.

Copy to mcp/<name>/server.py and customize.
"""

from typing import Annotated

from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

mcp = FastMCP(
    "service-name",
    instructions="[REQUIRED] Describe what this server provides and when to use it.",
)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": False,
    },
)
async def example_tool(
    query: Annotated[str, Field(description="Search term to find items.", min_length=1)],
    ctx: Context | None = None,
) -> dict:
    """Search for items matching the query.

    Use this tool when you need to find specific items by keyword.
    Returns a dictionary with matching results and count.
    """
    if ctx:
        await ctx.info(f"Processing: {query}")
    return {"result": query, "count": 1}


if __name__ == "__main__":
    mcp.run()
