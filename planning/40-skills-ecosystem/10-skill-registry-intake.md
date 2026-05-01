# Skill Registry Intake

## Scope

This lane evaluates official and community skill registries as candidate sources only. It does not install or vendor skills.

## Source Classes

| Source Class | Examples | Intake Treatment |
| --- | --- | --- |
| Official/vendor | Google, Microsoft, Supabase, Cloudflare skill repos. | Higher-priority review, still pinned and audited before promotion. |
| Community catalogs | Awesome lists and open catalogs. | Discovery-only; entries require separate source verification. |
| Individual skills | Standalone upstream skill repos. | Candidate queue after provenance and executable-surface review. |

## Trust And Lock Fields

Every candidate record must include:

- Source URL and normalized repository id.
- Pinned revision or release.
- License and redistribution posture.
- Maintainer identity and activity signal.
- Files to copy or adapt.
- Hook/script/command substitution inventory.
- Network, filesystem, credential, and package-manager behavior.
- Fixtures, rollback, and re-audit triggers.

## Candidate Queue Rules

1. No default installs.
2. No promotion from an awesome list alone.
3. Quarantine any credential, browser-profile, proxy, offensive, or destructive behavior.
4. Require `wagents validate`, skill audit, package dry-run, and docs/readme freshness before promotion.
5. Preserve source provenance in a lane-owned manifest or reference file.

## Initial Queue Sources

Prioritize official/high-trust sources first, then community catalogs as discovery indices. External repos from C10 with `skill-registry-intake` target lane remain pending until this lock model is populated.
