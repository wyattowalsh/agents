"""FastMCP entry point for the Things native server."""

from things_native.app import mcp

__all__ = ["mcp"]

if __name__ == "__main__":
    mcp.run()
