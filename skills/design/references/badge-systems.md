# Badge Systems

Use this reference when the request is about README badges, ShieldCN/shields
rows, status indicators, package/version badges, workflow badges, or visual
trust/status chips in docs. Treat badges as compact interface elements: they
need truthful data, accessible labels, stable links, visual consistency, and
bounded edits.

## Classification

| Signal | Route |
| --- | --- |
| README badge row, shields.io, ShieldCN, `BADGES:START`, status indicators | `/design` Badge Surface |
| General README rewrite, docs IA, install guide copy | `docs-steward` |
| CI workflow creation or status publishing setup | DevOps/CI workflow, not `/design` |
| Security scorecard, coverage, package, or quality badge with unknown public data | Ask or verify before inserting |

Badge-only work can be single-lane. Badge work touching README structure,
generated docs, package metadata, and CI status must serialize shared files
behind one owner.

## Selection Rules

- Prefer dynamic endpoints for live values: package version/downloads, CI
  status, release, coverage, docs build, license, security posture, and
  supported platform signals.
- Keep a normal row to 3-8 badges. Use grouped rows only when a mature project
  has enough truthful status surfaces.
- Link every badge to the source it represents: package page, workflow run,
  release page, docs site, coverage report, security policy, or repository
  page.
- Match existing badge style, size, casing, icon grammar, and layout before
  introducing a new provider.
- Do not add public API badges for private repositories, private package names,
  hidden workflows, secret-bearing JSON endpoints, or services that require
  credentials to resolve.
- Avoid vanity badges that do not help readers decide trust, installability,
  support, status, or technology fit.
- Order badges by reader decision flow: Status, Quality, Package, Tech Stack,
  Social.
- Use native CI/status badge URLs when they are more accurate or private-repo
  compatible, especially GitHub Actions, GitLab CI, CircleCI, Codecov, Coveralls,
  pkg.go.dev, Read the Docs, OpenSSF, and SonarCloud.
- If the repo has many truthful badge candidates, keep Status, Quality, and
  Package visible, then group or collapse secondary Tech Stack and Social rows.

## Detection Signals

Inspect before proposing badges:

| Signal | Evidence |
| --- | --- |
| Repo identity | Git remote owner/repo, platform, default branch, public/private visibility when known. |
| README target | Existing README path, format, H1 placement, current badge block, marker boundaries. |
| Status | `.github/workflows`, GitLab/CircleCI config, CI badge already present. |
| Package | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, gemspec, NuGet, Packagist, Hex/Elixir metadata. |
| Quality | Coverage config, CodeQL, Codecov, Coveralls, SonarCloud, Snyk, OpenSSF, linters, formatters, type checkers. |
| Tech stack | Language manifests, framework dependencies, infra files, docs framework, database/dev-tool signals. |
| Existing badge state | Provider style, dead services, duplicate service/metric paths, placeholders, broken links. |

Do not infer owner, repo, package, workflow, branch, or service project IDs when
the evidence is absent. Ask or skip the badge.

## Badge Catalog Families

| Family | Typical Badges | Notes |
| --- | --- | --- |
| Status | GitHub Actions, GitLab CI, CircleCI, Travis | Prefer native URLs for private repos and workflow-specific truth. |
| Quality | Codecov, Coveralls, Code Climate, Snyk, CodeQL, SonarCloud, OpenSSF | Add only when the backing service exists or is enrolled. |
| Package | npm, PyPI, crates.io, Go reference, GitHub release, NuGet, Packagist, RubyGems, Hex | Use package registry pages as links. |
| License | GitHub license or package-registry license | Public API may be required. |
| Language/framework | Python, TypeScript, Rust, Go, React, Next.js, FastAPI, Django, Rails, Laravel, etc. | Useful after status/package badges; avoid long technology walls. |
| Infrastructure/docs | Docker, Kubernetes, Terraform, cloud hosts, Read the Docs, MkDocs, Docusaurus, TypeDoc | Add when repo evidence exists. |
| Social/community | Stars, forks, issues, contributors, discussions, Discord, sponsors | Usually last; omit for private or internal repos. |

## Provider Guidance

| Provider | Use | Caution |
| --- | --- | --- |
| shields.io | Default broad ecosystem coverage and dynamic endpoints. | Verify icon slugs and endpoint visibility. |
| ShieldCN | shadcn-like visual style for README/docs badge rows. | Use `.svg`, real links, and accessible alt text; do not install or call hosted tooling from the skill. |
| badgen.net | Simple compact badges when already used by the repo. | Avoid mixing styles in one row without reason. |
| forthebadge | Decorative project personality badges. | Rarely appropriate for professional docs; never use for trust signals. |

## URL And Style Rules

- `flat-square` is a solid default for technical projects; `flat` matches GitHub
  defaults; `social` is only for social counters; `for-the-badge` is large and
  should be limited to hero/landing contexts.
- Always set `logoColor` explicitly for shields-style badges. Use white on dark
  or saturated backgrounds and black on very light backgrounds.
- Encode static shield URL text carefully: spaces as `%20` or `_`, literal
  hyphen as `--`, literal underscore as `__`, plus as `%2B`, hash as `%23`.
- For custom JSON metrics, use shields dynamic JSON badges only when the JSON
  endpoint is public and non-secret:
  `https://img.shields.io/badge/dynamic/json?url=<encoded>&query=<jsonpath>&label=<label>`.
- For GitHub dark-mode badge variants, `<picture>` markup is acceptable in
  GitHub README files, but do not use it for npm/PyPI/crates renderers unless
  the target renderer supports it.
- `forthebadge.com` is decorative only. For large dynamic badges, prefer
  shields.io with `style=for-the-badge`.

## Dead Or Risky Services

| Service | Action |
| --- | --- |
| `david-dm.org` | Remove or replace with maintained dependency/security status. |
| `godoc.org` | Replace with `pkg.go.dev`. |
| `travis-ci.org` | Migrate to `travis-ci.com` or current CI when possible. |
| Private Codecov/Coveralls/Sonar endpoints | Use tokenized/native URLs only when the project already exposes them safely; never invent tokens. |

## Marker Safety

Use explicit markers when inserting or replacing badges:

```md
<!-- BADGES:START -->
...
<!-- BADGES:END -->
```

If markers exist, edit only inside them. If markers do not exist, propose the
placement before changing the README unless the user explicitly asked for an
implementation and the existing README has a clear H1/header badge slot.

Preserve all README content outside the approved badge block. Never move install
commands, warnings, project status notes, or security disclosures to make a
badge row look cleaner.

## Preview Contract

Before changing badge rows, present a compact preview:

```text
Badge Plan
+ build status -> workflow URL
+ npm version -> package URL
= license -> existing badge retained
- stale unsupported service badge

Placement
- Inside existing BADGES markers in README.md
```

For implementation, show the diff or line references and list any unverifiable
badges that were skipped.

## Validation Workflow

- Extract badge URLs from Markdown image syntax and HTML `<img src>`.
- Validate only known badge/image hosts unless the user asks for a broader link
  check.
- Bound network checks with short timeouts and retries; report broken, slow, and
  skipped URLs separately.
- Never run validation against private or credentialed endpoints without user
  approval.
- Treat HEAD/redirect behavior as evidence, not authority; if a service blocks
  HEAD, fall back to a browser/rendered check or mark validation inconclusive.

## Visual And Accessibility Checks

- Alt text should name the represented signal, not repeat raw URL text.
- Badge rows should wrap cleanly on mobile and not force horizontal scrolling.
- Centering is acceptable for project README headers; dense docs pages may be
  left-aligned for scanability.
- Use consistent provider, style, size, and icon treatment in one row.
- Confirm dark/light readability when using custom colors or ShieldCN variants.

## Proof

Static proof is usually enough for README badge generation:

- Links are meaningful and do not contain placeholders.
- Badge URLs end in `.svg` when required by the provider.
- Dynamic endpoints are public and source-compatible.
- Marker boundaries are preserved.
- The scanner reports badge signals and artifact/noise risks.

Rendered proof is required when badges are part of a docs page, product UI, or
status dashboard rather than plain README markdown.
