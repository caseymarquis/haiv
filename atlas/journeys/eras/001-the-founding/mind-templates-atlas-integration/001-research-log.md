# 001 — Research Log

**Goal:** Update mind creation templates so new minds are instructed to run `hv chart` as part of their planning process.

## What I searched in the atlas

**Maps:** Checked `maps/haiv-lib.md`. It covers the foundation layer — paths, commands, infrastructure, helpers. `templates.py` is listed under "Uncharted" — noted as Jinja2 template rendering for `__assets__/`. The helpers section mentions `minds.py` but it's also uncharted.

**Quest board:** No quests related to mind templates or staging. The Resolver Mystery and Context Factory quests touch command infrastructure but not the staging flow.

**Journeys:** Luna's journeys covered routing and the chart command itself. No journeys through the staging/mind-creation path.

## What's missing

The atlas has no map of:
- How `hv minds stage` works — what it creates, what templates it uses, where they live
- The `__assets__/` template system — how templates are found, rendered, and written
- The role templates (worker, PM, COO) and welcome templates

## Where I plan to go

1. The stage command: `haiv-core/src/haiv_core/commands/minds/stage.py` — this is where minds get created
2. The `__assets__/` directories — project-level and core-level, looking for templates used during staging
3. `haiv-lib/src/haiv/templates.py` — the template rendering system
4. Any welcome.md templates or role-related assets

I need to understand the current template pipeline before I can know where to add the `hv chart` instruction.
