"""FastMCP entry point for the Things Shortcuts server."""

from things_shortcuts.app import mcp

__all__ = ["mcp"]

if __name__ == "__main__":
    mcp.run()
