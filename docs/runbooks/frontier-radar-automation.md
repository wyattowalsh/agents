# Frontier Radar recurring automation

This runbook defines the recurring control plane for discovering, verifying, and governing new agentic-engineering capabilities for `wyattowalsh/agents`.

The persistent review queue is GitHub issue `#5`. The machine-readable schedule is `config/frontier-radar-schedules.json`.

## Authority boundary

Research and deterministic scans are not promotion. Promotion is not implementation. Implementation is not activation.

No recurring lane may install or execute an external candidate, authenticate to third-party services, access or write secrets, mutate canonical registries or generated surfaces, push, merge, release, deploy, or widen permissions. An isolated, policy-gated OpenSpec draft is the maximum unattended canonical write.

## Shadow week

From August 22 through August 29, 2026, run only:

| Lane | Executor | Schedule |
| --- | --- | --- |
| Official delta | ChatGPT Scheduled Task | Weekdays, 07:45 America/New_York |
| Weekly synthesis | ChatGPT Scheduled Task | Sunday, 17:00 America/New_York |
| Frontier curator | Codex Automation | Daily, 02:30 America/New_York |
| Promoted research review | Human promotion gate | Sunday, 18:00 America/New_York |

Review every emitted observation. Measure duplicate rate, false-positive rate, source independence, missing-run rate, and the fraction of promoted candidates later rejected by maximum-depth research.

## Expanded cadence

Enable after the shadow week:

| Lane | Executor | Schedule |
| --- | --- | --- |
| Ecosystem delta | ChatGPT Scheduled Task | Tuesday and Thursday, 12:15 |
| Paradigm scout | ChatGPT Scheduled Task | Wednesday, 16:00 |
| Monthly landscape | ChatGPT Scheduled Task | First Saturday, 09:00 |
| Quarterly horizon | ChatGPT Scheduled Task | First Saturday of Jan/Apr/Jul/Oct, 10:00 |
| Freshness audit | Codex Automation | Sunday, 20:30 |
| Control-plane audit | Codex Automation | First Monday, 03:00 |

## Pro-native handoff

The weekly synthesis emits exact Deep Research packets only for candidates that cross the configured score and hard-gate thresholds. At the Sunday promotion gate:

1. Check the current in-product Deep Research allowance.
2. Preserve the configured 10% reserve.
3. Batch tightly related candidates when that improves evidence quality.
4. Run maximum-depth Deep Research with the generated packet and verifier prompt.
5. Export the complete Markdown report.
6. Ingest it through the curator.
7. Record the decision and reasons in issue `#5`.

Research approval never grants implementation or activation authority.

## GitHub Actions substrate

`.github/workflows/frontier-radar-deterministic.yml` supplies the repository-side deterministic substrate:

- daily read-only W0 discovery scans at 02:30 Eastern;
- weekly validation and projection-drift checks at 20:30 Eastern on Sunday;
- monthly control checks at 03:00 Eastern on the first Monday.

GitHub cron is UTC. The workflow schedules both possible UTC offsets and routes the nominal cron timestamp through `America/New_York`, suppressing the DST-mismatched candidate. It does not infer the lane from delayed runner start time.

When `wagents frontier` is present, the workflow runs its verification and ledger checks. Until then, the daily lane falls back to the existing `harness-master` W0 scripts. Failed executed lanes append a compact incident comment to issue `#5`; successful and DST-suppressed runs remain quiet.

## Noise policy

Remain silent for routine version bumps, popularity changes, repeated marketing claims, README churn, and candidates already covered by a stronger repository owner. A research monitor should notify only for a material repository-relevant delta, an official breaking or security change, a stale assumption, or a candidate crossing a configured decision threshold.

## Kill switch

Disable the corresponding ChatGPT or Codex task, or disable the GitHub Actions workflow. Keep issue `#5` open to preserve decision memory. Do not delete prior evidence to silence the system.
