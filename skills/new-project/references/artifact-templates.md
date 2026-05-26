# Artifact Templates

Use templates as skeletons, not as mandatory full files.

Recommended artifact skeletons:

- `README.md`: purpose, quickstart, development, validation, deployment, license.
- `AGENTS.md`: exact commands, safety boundaries, package manager, test policy.
- `DESIGN.md`: design brief, mobile-first rules, typography, color, accessibility, anti-slop checklist.
- `.github/workflows/validate.yml`: least-privilege CI mirroring local gates.
- `justfile`: concise wrappers around existing package manager commands.

Never replace an existing artifact without approval.
