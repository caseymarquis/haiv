# Immediate Plan

## Done

- Built `hv chart explore` — cyclic guided exploration tool
- Moved existing journeys to `atlas/journeys/eras/001-the-founding/`
- Added `AtlasPaths` and `WorkPaths.exploration_file` to paths.py
- Converted `chart.py` to `chart/_index_.py` + `chart/explore.py`
- 9 templates in `__assets__/chart/`, 19 tests, all passing
- Merged to main, command is live
- Staged pulse to explore the resolver system as first real user

## Still Open

- Replace placeholder example journey with a real one (from pulse's journey or a future one)
- Hook point for project-level customization of the explore flow
- Update welcome.md template to reference `hv chart explore` instead of manual process
- Corrected my own journey entry (001) but the journey is incomplete — batched reads broke the flow
- Consider whether `hv chart` itself should mention `hv chart explore` as the way to start

## Design Decisions Made

- Exploration is cyclic: plan → embark → read → reflect → plan
- State stored as JSON in mind's work folder
- All prose lives in templates, command is pure logic + state management
- Example journey ships as bundled asset in __assets__/chart/
- Research log (001) created from template with skeleton sections
- --plan is for *thinking* (weighing options), --embark is for *committing* (picking one)
- Journal corrections use annotations, not rewrites
