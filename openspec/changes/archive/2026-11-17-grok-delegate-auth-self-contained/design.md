## Architecture

Parent harness → `/grok-delegate` → `preflight.sh` → `doctor.py` + `auth_lib.py` → JSON gate → native `grok -p` nodes.

## Fast vs deep preflight

| Mode | Entry | Blocks dispatch |
| --- | --- | --- |
| Fast | `preflight.sh` / `doctor.py` | Any `fail` check |
| Deep | `auth_verify.sh` | `grok -p` smoke failure |

## Auth policy

1. OAuth via `grok login` is default (SuperGrok subscription billing path).
2. `auth_lib` reads `~/.grok/auth.json` without logging secrets.
3. `XAI_API_KEY` allowed only when user explicitly requests and `GROK_DELEGATE_ALLOW_API_KEY=1`.

## Tier-T

Bounded leaf offload when fast preflight passes. Parent retains synthesis; ineligible for graphs with overlapping writers.