# Session Commands Reference

Detailed protocols for in-session commands and facilitated mode.

## Export Protocol

When the user types `export` or `dashboard`:
1. Copy `templates/dashboard.html` to `/tmp/wargame-dashboard-{turn}.html` using bash `cp` (do NOT read the HTML template into context — it is 676 lines of static HTML/CSS/JS)
2. Generate the JSON data block matching the current state and view. For field reference, use `references/dashboard-schema.md`.
3. Insert JSON into the `<script id="data">` block
4. Render using the cross-platform flow from `references/visualizations.md`:
   Playwright screenshot → browser open → Unicode fallback

**Additional export formats** (specify after `export`):

| Format | Command | Output | Use Case |
|--------|---------|--------|----------|
| HTML dashboard | `export` (default) | Interactive HTML file | Visual review, presentations |
| JSON | `export json` | Structured game state | External tools, data analysis |
| CSV | `export csv` | Decisions + outcomes table | Spreadsheet analysis |
| Slide outline | `export slides` | Markdown slide deck outline | Presenting findings to stakeholders |

**JSON export:** Full game state including all turns, actor states, decisions, outcomes, and AAR. Saved to `~/.claude/wargames/{slug}-export.json`.

**CSV export:** One row per turn with columns: Turn, Decision, Outcome, Criteria Scores, Surprise. Saved to `~/.claude/wargames/{slug}-export.csv`.

**Slide outline:** Markdown outline with: title slide, scenario overview, key decision points (1 slide each), findings, action bridge. Saved to `~/.claude/wargames/{slug}-slides.md`.

## Meta Command

When the user types `meta` (no active session required):

1. Read all journals from `~/.claude/wargames/`
2. Analyze across journals for patterns:
   - **Recurring biases:** Which human/LLM biases appear most frequently?
   - **Domain performance:** Which domains show strongest/weakest decision quality?
   - **Criteria priorities:** How do criteria rankings shift across scenarios?
   - **Risk tendency:** Is the user consistently risk-seeking, risk-averse, or balanced?
   - **Calibration drift:** Are probability estimates improving over time?
3. Present as a "Decision Fitness Report" using the Meta Analysis Display from `references/output-formats-commands.md`

Requires 3+ completed journals. If fewer exist, inform user: "Need at least 3 completed journals for cross-session analysis. You have {N}."

## Compare Command

When the user types `compare [journal1] [journal2]` (by number from `list` or keyword):

1. Read both journals
2. Present side-by-side comparison:
   - **Decisions made:** Turn-by-turn decision differences
   - **Outcomes:** Which strategy produced better results per criterion
   - **Common patterns:** Shared decision tendencies across both runs
   - **Divergence points:** Where strategies differed most and the consequences
   - **Verdict:** Which strategy dominated, with caveats
3. Use the Compare Display from `references/output-formats-commands.md`

Both journals must be for the same or similar scenario. If domains differ significantly, warn but proceed.

## Summary Command

When the user types `summary [N]` (journal number from `list`):

1. Read journal N
2. Present a condensed 10-20 line summary:
   - Scenario and tier (1 line)
   - Key decisions and outcomes (3-5 lines)
   - Top insight or transferable principle (2-3 lines)
   - Action Bridge status: which Probe/Position/Commit actions were taken (2-3 lines)
   - Final assessment: what went well, what to do differently (2-3 lines)
3. Does NOT start an active session — read-only review

## Facilitated Mode

When `$ARGUMENTS` is `facilitated`:

LLM serves as game master and adjudicator only. All actors are controlled by human players. For tabletop exercises (TTX) and group decision-making workshops.

### Setup
1. **Scenario setup** — Same as standard Interactive Wargame: classification, criteria, actor definitions
2. **Player assignment** — Assign each actor to a human player (or group). The facilitator (LLM) does NOT control any actors.
3. **Rules briefing** — Explain the turn structure and available commands to all players

### Turn Structure (Facilitated)
1. **Situation brief** — LLM presents the current state
2. **Player prompts** — Prompt each player for their actor's action: "Player controlling {Actor}: What does {Actor} do this turn?"
3. **Collect all actions** — Wait for all players to submit
4. **Adjudicate** — LLM adjudicates using the standard Adjudication Protocol
5. **Generate consequences** — LLM generates unexpected consequences
6. **Present results** — Show outcomes and updated state to all players
7. **Decision point** — If an inject fires, present it. Prompt next round of player actions.

### Facilitator Guidelines
- The LLM maintains neutrality — does not favor any player
- Adjudication follows the standard protocol strictly
- Injects are pre-seeded but deployment timing adapts to dramatic moments
- The LLM may call for a "time-out" for group discussion before critical decisions
- All standard in-session commands are available to any player

## Tutorial Mode

When `$ARGUMENTS` is `tutorial`:

Run a pre-scripted 2-turn Complicated tier scenario with inline pedagogical annotations. Purpose: teach the wargame system to new users.

**Scenario:** "Your company's main competitor just poached your VP of Sales. You have 48 hours before the board meeting."

**Structure:**
1. **Classification** — Show the scoring rubric with annotations explaining each dimension: _"This scores 1 on Adversary because the competitor is actively hostile. Here's why that matters..."_
2. **Criteria elicitation** — Walk through the ranking process: _"We'll use these criteria to evaluate your options. Ranking them forces you to articulate what matters most."_
3. **Turn 1** — Present options with annotations on choice architecture: _"Notice the options are randomized and show both success and failure probabilities. This counteracts framing bias."_
4. **Turn 2** — Deploy one inject, complete with annotation: _"Injects create dilemmas — they force trade-offs between competing objectives, not just add problems."_
5. **Mini-AAR** — Condensed review with annotations: _"The AAR is where learning happens. We look for biases, extract principles, and plan next moves."_

Total output: ~200 lines. Ends with: "Ready to try your own scenario? Paste it or type `guide me`."

## Research Command

When the user types `research` during an active session:

1. Identify the most relevant research question for the current decision point
2. Run 1-2 targeted `WebSearch` queries focused on the specific domain and decision context
3. Present findings using the Intelligence Research Display from `references/output-formats-commands.md`
4. Return to the current decision point — does not advance the turn

If `WebSearch` is unavailable, inform user: "Web research requires search access. Not available in this session."

## State Snapshot

Append a YAML state snapshot as an HTML comment at the end of the journal after each turn save:

```
<!-- STATE
turn_number: {current_turn}
difficulty: {difficulty_level}
verbosity: {brief | standard | detailed}
criteria: [{ranked criteria list}]
branches: [{branch_id, fork_turn, current_turn}]
actors:
  - name: {actor}
    resources: {resource_map}
    stance: {stance}
    beliefs: {what this actor believes about the situation}
    information_state: {knows | thinks-they-know | doesn't-know}
    relationships: {relationship status with other actors}
    risk_posture: {current risk tolerance}
    attention_style: {reactive | adaptive | agile}
active_injects: [{inject_ids}]
inject_history: [{previously deployed inject_ids}]
-->
```

**Resume flow:** Read frontmatter + last `<!-- STATE ... -->` block for fast resume. Fall back to full-journal reconstruction if no snapshot found.

## Rewind Protocol

When the user types `rewind [N]` (default N=1):
1. **Load state snapshot** from N turns back by finding the corresponding `<!-- STATE ... -->` block in the journal
2. **Fork the journal** with a branch marker: `## Branch: Turn {T} Alternative` header inserted after the original turn's content
3. **Restore the loaded state** as the active game state and continue play from that point
4. **Preserve the original path** — all content above the branch point remains intact in the journal

If the requested turn does not exist or has no state snapshot, inform the user and show available turn numbers.

**Branch limits:**
- Maximum 3 active branches per wargame. If the user tries to create a 4th, prompt: "You have 3 active branches. Prune one with `branches prune [N]` or continue on the current branch."
- Active branches are tracked in the state snapshot: `branches: [{branch_id, fork_turn, current_turn}]`

**Branch navigation:**
- `branches` — List all active branches with their fork points and current turns
- `branches switch [N]` — Switch to branch N, loading its latest state snapshot
- `branches prune [N]` — Remove branch N (keeps journal content but marks as pruned)

Branches from abandoned sessions (status: Abandoned) are auto-pruned on next `resume`.

## Canonical Terms

Use these exact string values throughout:

- **Tiers:** "Clear", "Complicated", "Complex", "Chaotic"
- **Modes:** "Quick Analysis", "Structured Analysis", "Interactive Wargame", "Facilitated Wargame", "Tutorial"
- **Persona archetypes:** "hawk", "dove", "pragmatist", "ideologue", "bureaucrat", "opportunist", "disruptor", "custom"
- **Difficulty levels:** "optimistic", "realistic", "adversarial", "worst-case"
- **Dispatch commands:** "resume", "list", "archive", "delete", "meta", "compare", "summary", "tutorial", "facilitated"
- **In-session commands:** "red team", "what if", "criteria", "explore", "sensitivity", "delphi", "forecast", "negotiate", "calibrate", "options", "cause", "morph", "research", "rewind", "branches", "status", "export", "verbose", "meta", "compare", "summary", "?"
- **Verbosity levels:** "brief", "standard", "detailed"
- **Action Bridge levels:** "Probe", "Position", "Commit"
- **Journal statuses:** "In Progress", "Complete", "Abandoned"
- **Domain tags (predefined):** "biz", "career", "crisis", "geo", "personal", "startup", "negotiation", "tech", "custom" — plus auto-detected custom tags from scenario context
