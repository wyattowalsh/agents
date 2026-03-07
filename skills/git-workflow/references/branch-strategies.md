# Branch Strategies

Comparison guide for git branching strategies with migration paths and team sizing.

## Contents

1. [Strategy Overview](#strategy-overview)
2. [Detailed Comparison](#detailed-comparison)
3. [Team Size Alignment](#team-size-alignment)
4. [Release Cadence Matching](#release-cadence-matching)
5. [Migration Paths](#migration-paths)
6. [Anti-patterns](#anti-patterns)

---

## Strategy Overview

| Strategy | Core Idea | Best For |
|----------|-----------|----------|
| Trunk-based | Everyone commits to main, short-lived branches (<1 day) | Small teams, continuous deployment |
| GitHub Flow | main + feature branches, PR-based merge | Most teams, regular releases |
| Git Flow | develop + feature + release + hotfix branches | Large teams, versioned releases |

---

## Detailed Comparison

### Trunk-Based Development

**How it works:**
- Single main branch is always deployable
- Feature branches live < 1 day (ideally < 4 hours)
- Feature flags gate incomplete work
- CI runs on every push to main

**Pros:**
- Minimal merge conflicts (branches are short-lived)
- Continuous integration is genuine (not just CI on branches)
- Forces small, incremental changes
- Fastest path to production

**Cons:**
- Requires mature CI/CD pipeline
- Feature flags add complexity
- Risky without comprehensive test coverage
- Not suitable for projects needing parallel release trains

### GitHub Flow

**How it works:**
- main is always deployable
- Create feature branch from main
- Open PR when ready for review
- Merge to main after approval
- Deploy from main

**Pros:**
- Simple to understand and teach
- PR-based review is well-supported by tooling
- Works with any release cadence
- Good balance of safety and speed

**Cons:**
- No built-in release management
- Can accumulate long-lived branches if PRs stall
- No separation between "ready" and "released"

### Git Flow

**How it works:**
- `main` = production, `develop` = integration
- Feature branches from develop
- Release branches for stabilization
- Hotfix branches from main for urgent fixes
- Strict merge direction rules

**Pros:**
- Clear separation of concerns
- Supports parallel release preparation
- Well-defined hotfix process
- Good for versioned software (libraries, mobile apps)

**Cons:**
- Complex, many branches to manage
- Merge conflicts between long-lived branches
- Slow feedback loop (develop -> release -> main)
- Overhead not justified for web apps with CD

---

## Team Size Alignment

| Team Size | Recommended | Why |
|-----------|-------------|-----|
| 1-3 devs | Trunk-based | Low coordination overhead, fast iteration |
| 4-10 devs | GitHub Flow | PR reviews manageable, good balance |
| 10-20 devs | GitHub Flow or Git Flow | Depends on release model |
| 20+ devs | Git Flow or Trunk-based with feature flags | Need formal release process or strong CI |

**Monorepo considerations:**
- Trunk-based scales well with code ownership (CODEOWNERS)
- GitHub Flow works with per-package CI scoping
- Git Flow becomes unwieldy in monorepos (branch per package?)

---

## Release Cadence Matching

| Cadence | Recommended | Rationale |
|---------|-------------|-----------|
| Continuous (multiple/day) | Trunk-based | Branches add friction to CD |
| Weekly/biweekly | GitHub Flow | PR batching aligns naturally |
| Monthly/quarterly | GitHub Flow or Git Flow | Release branches help stabilization |
| Versioned releases (semver) | Git Flow | Release branches support parallel versions |
| Mobile app releases | Git Flow | App store review requires release branches |

---

## Migration Paths

### Git Flow -> GitHub Flow

1. Stop creating new feature branches from `develop`
2. Create features from `main` instead
3. Merge PRs directly to `main`
4. Phase out `develop` branch (stop merging to it)
5. Delete `develop` after all in-flight features merge
6. Update CI to deploy from `main` instead of release branches

### GitHub Flow -> Trunk-Based

1. Set up feature flag infrastructure
2. Reduce PR size (target < 200 lines)
3. Increase review speed target (< 4 hours to review)
4. Enable auto-merge for approved PRs
5. Strengthen CI (must be fast and reliable)
6. Gradually shorten branch lifetimes

### Any -> Git Flow

1. Create `develop` branch from `main`
2. Configure branch protection rules for both
3. Update CI for develop and release branch patterns
4. Document the workflow for the team
5. Set up merge direction rules in branch protection

---

## Anti-patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Long-lived feature branches | Merge conflicts, divergence | Time-box to < 1 week |
| No branch protection | Accidental force-push to main | Enable required reviews |
| Cherry-pick sprawl | Lost changes, duplicate commits | Use proper merge/rebase |
| Release branch without deadline | Branch lives forever | Set release date at creation |
| Develop branch in CD pipeline | Unnecessary indirection | Switch to GitHub Flow |
| Manual deployment from branches | Error-prone, no audit trail | Automate from main/release |
