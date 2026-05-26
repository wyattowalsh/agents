# Adding Preferences

Add future preferences through data first.

1. Add a capability to `data/capabilities.json`.
2. Include dependencies, conflicts, implied capabilities, risk level, commands, artifacts, validation, handoff skills, and docs sources.
3. Add the capability to relevant presets in `data/presets.json`.
4. Add a reference note only when catalog metadata is not enough.
5. Add or update evals for dispatch, conflict, and safety behavior.
6. Run `validate_catalog.py`, `preferences.py validate`, `wagents eval validate`, and the skill audit.

Do not add broad setup prose to `SKILL.md` for a single new tool.
