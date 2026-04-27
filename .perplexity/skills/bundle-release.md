---
name: Bundle Release Prep
description: Prepare a skill bundle release — validate all assets, package with wagents, update changelogs.
---

## Task
Prepare a release of the skill bundle by validating assets, running the packaging tool, and updating release documentation.

## Pre-Release Checklist

1. **Asset validation**
   - Run `wagents validate` — ensure all skill and agent frontmatter passes
   - Verify every skill in `skills/` has a matching directory name and `SKILL.md`
   - Verify every agent in `agents/` has a filename matching frontmatter `name`
   - Check `agent-bundle.json` is up to date and references all assets
   - Confirm `.claude-plugin/` and `.codex-plugin/` manifests are in sync with repo contents

2. **Version and changelog review**
   - Check `CHANGELOG.md` or recent conventional commits for release-worthy changes
   - Ensure version bump follows semver based on commit types:
     - `feat:` → minor bump
     - `fix:` → patch bump
     - Breaking change → major bump
   - Verify `VERSION` file or git tag strategy is consistent

3. **Packaging with wagents**
   - Run `wagents package --dry-run` to check portability without creating ZIPs
   - Review any warnings about missing files or oversized skills
   - Run `wagents package --all` to generate release artifacts in `dist/`
   - Confirm each skill ZIP contains only: `SKILL.md` + `references/` (if present)

4. **Documentation sync**
   - Run `wagents readme --check` — fail if README is stale
   - Run `wagents docs generate` — ensure docs site content pages are current
   - Verify `AGENTS.md` reflects any workflow or convention changes since last release

5. **CI/CD verification**
   - Check `.github/workflows/release-skills.yml` triggers on `v*.*.*` tags
   - Validate the workflow packages and uploads artifacts correctly
   - Confirm no secrets or credentials are hardcoded in workflow files

## Post-Release Steps
- Create and push a version tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
- Verify GitHub Actions release workflow succeeds
- Check that generated ZIPs are attached to the release
- Announce in relevant channels if applicable

## Output Format
Return a release readiness report:
- **Status**: READY / BLOCKED / WARN
- **Validation results**: Output of `wagents validate` and `wagents package --dry-run`
- **Changelog preview**: Summary of changes since last tag
- **Blocking issues**: Any items that must be fixed before tagging
- **Next command**: Exact git tag and push command to execute the release
