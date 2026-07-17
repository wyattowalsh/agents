# Candidate Corpus July 2026 Decision Log

> Final overlay-aware decision state. Historical intake risk labels are retained below for auditability; `full-integration-state.md` owns the final completion counters.

- Raw entries: 293
- Unique normalized targets: 289
- Duplicates deduped: 4
- Historical conservative hard blocks: 4
- Integrated quarantine references: 4
- Active install blocks: 4

## Risk-Sensitive Sources

- `012` `Eronred/aso-skills`: review-required - Skill-like source routed through curated catalog install metadata and source-list evidence.
- `015` `zubair-trabzada/ai-legal-claude`: review-required - Source routed to a repo-native terminal integration surface.
- `023` `onvoyage-ai/gtm-engineer-skills`: review-required - Skill-like source routed through curated catalog install metadata and source-list evidence.
- `044` `zubair-trabzada/ai-sales-team-claude`: review-required - Source routed to a repo-native terminal integration surface.
- `045` `Bhanunamikaze/Agentic-SEO-Skill`: review-required - Existing repo catalog surface already covers this source/domain.
- `046` `agi-now/buffett-skills`: review-required - Skill-like source routed through curated catalog install metadata and source-list evidence.
- `050` `lawve-ai/awesome-legal-skills`: review-required - Collection source routed through bounded catalog guidance; wholesale vendoring is avoided.
- `054` `JeffLi1993/seo-audit-skill`: review-required - Existing repo catalog surface already covers this source/domain.
- `057` `Affitor/affiliate-skills`: review-required - Existing repo catalog surface already covers this source/domain.
- `077` `rorkai/app-store-connect-cli-skills`: review-required - Existing repo catalog surface already covers this source/domain.
- `078` `timbroddin/app-store-aso-skill`: review-required - Existing repo catalog surface already covers this source/domain.
- `093` `NVIDIA/skills`: review-required - Existing repo catalog surface already covers this source/domain.
- `099` `RKiding/Awesome-finance-skills`: review-required - Collection source routed through bounded catalog guidance; wholesale vendoring is avoided.
- `103` `himself65/finance-skills`: review-required - Skill-like source routed through curated catalog install metadata and source-list evidence.
- `114` `AgriciDaniel/claude-seo`: review-required - Source routed to a repo-native terminal integration surface.
- `134` `ComposioHQ/awesome-codex-skills`: quarantine - Read-only source-list evidence found `competitive-ads-extractor`, which extracts and analyzes competitors' ads from ad libraries. Keep hard-blocked without explicit legal, ToS, credential, rate-limit, and anti-abuse approval.
- `152` `ComposioHQ/awesome-codex-skills`: quarantine - Read-only source-list evidence found `youtube-downloader`, which downloads YouTube videos and audio. Keep hard-blocked without rights, ToS, copyright, and source-content approval.
- `157` `Panniantong/Agent-Reach`: review-required - Existing repo catalog surface already covers this source/domain.
- `169` `BestLemoon/codex-seo`: review-required - Existing repo catalog surface already covers this source/domain.
- `173` `avalonreset/seo-dungeon`: review-required - Existing repo catalog surface already covers this source/domain.
- `205` `jihe520/social-push`: quarantine - Read-only source-list evidence found `social-push` plus `agent-browser` automation for posting content to social platforms. Keep hard-blocked without account-owner, ToS, anti-spam, and manual per-post approval.
- `228` `pedronauck/skills`: review-required - Existing repo catalog surface already covers this source/domain.
- `236` `pedronauck/skills`: review-required - Existing repo catalog surface already covers this source/domain.
- `280` `klajdikkolaj/upwork-autopilot`: quarantine - Read-only source-list evidence found `upwork-application-session`, which can search roles, draft proposals, and submit applications through Chrome CDP. Keep hard-blocked without account-owner, ToS, budget, and manual submission approval.

## Integrated Quarantine References

- `https://github.com/ComposioHQ/awesome-codex-skills/tree/master/competitive-ads-extractor`: integrated as a non-installable quarantine reference
- `https://github.com/ComposioHQ/awesome-codex-skills/tree/master/video-downloader`: integrated as a non-installable quarantine reference
- `https://github.com/jihe520/social-push`: integrated as a non-installable quarantine reference
- `https://github.com/klajdikkolaj/upwork-autopilot`: integrated as a non-installable quarantine reference

## Active Install Blocks

- `https://github.com/ComposioHQ/awesome-codex-skills/tree/master/competitive-ads-extractor`: `hard_blocked_quarantine`
- `https://github.com/ComposioHQ/awesome-codex-skills/tree/master/video-downloader`: `hard_blocked_quarantine`
- `https://github.com/jihe520/social-push`: `hard_blocked_quarantine`
- `https://github.com/klajdikkolaj/upwork-autopilot`: `hard_blocked_quarantine`
