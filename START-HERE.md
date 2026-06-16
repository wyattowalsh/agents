# START HERE — 30-Minute Stranger Onboarding

Portable quick path for a fresh clone of this repository.

## Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- Node.js 22+ with `npx` (for skills install/sync)
- Optional: pnpm (docs site only)

## 0–5 min: Environment

```bash
git clone https://github.com/wyattowalsh/agents.git
cd agents
uv sync
uv run wagents validate
```

## 5–10 min: Discover skills

```bash
npx -y skills add github:wyattowalsh/agents --list
uv run wagents install honest-review -y -a claude-code   # example single-skill install
```

## 10–15 min: Preview harness sync (no writes)

```bash
uv run wagents skills sync --dry-run
```

## 15–25 min: Docs (optional)

```bash
uv run wagents docs init
uv run wagents docs generate --no-installed
uv run wagents docs dev
```

## 25–30 min: First contribution checklist

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md)
2. For non-trivial changes, use OpenSpec: `uv run wagents openspec doctor`
3. Before PR: `uv run wagents validate && uv run pytest && uv run wagents readme --check`

## Harness support honesty

All repo-present harnesses are **fixture-executable** or **plan-only** — see docs harness support page after `wagents docs generate`.

## MCP (optional, maintainer/advanced)

MCPHub is opt-in. Strangers can skip MCP entirely. See `docs/ai-tools/mcphub.md` after docs init.
