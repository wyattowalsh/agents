# Upstream tracking — package-version-check-mcp

## Wrapper debt

PyPI `package-version-check-mcp==1.2.20` fails on Python 3.11+ without injecting
`from __future__ import annotations` into `package_version_check_mcp/utils/version_parser.py`.

Repo mitigation: `scripts/mcphub/package-version-check-mcp.sh` patches cached `uvx`
installs and pins `package-version-check-mcp==1.2.20`.

## Removal criteria

1. Upstream wheel passes `uvx --from package-version-check-mcp==<fixed> package-version-check-mcp --help` on Python 3.11+ without patching.
2. Registry `command`/`args` can use direct `uvx` (no bash wrapper).
3. Delete launcher script and `upstream-tracking.md`; archive OpenSpec change.

## References

- Upstream: https://github.com/MShekow/package-version-check-mcp
- OpenSpec proposal: `proposal.md`