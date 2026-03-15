# AAR: feat(chart): use project-local example journey folder

## Summary

Moved example journeys from bundled `__assets__/chart/example-journey/` to a project-local folder at `atlas/journeys/examples/`. On first run, the bundled examples are copied into the project-local folder. Subsequent runs use whatever the project has — projects can replace or extend the examples.

### Deliverables

- **`helpers/chart.py`**: New helper module in haiv-lib containing all chart domain logic. Both chart commands are now thin shells that read args, call helpers, and print results.
- **Project-local examples**: `AtlasPaths.examples_dir` property, `ensure_example_journey()` helper with copy-if-empty semantics.
- **Briefing template**: Moved hardcoded briefing text from `_index_.py` into `briefing.md.j2`. Added encouragement to invent new reward types.
- **Dynamic example listing**: Start template now lists whatever files are in the examples folder instead of hardcoding specific filenames.
- **Atlas maps updated**: Created `maps/commands/` subfolder with `chart.md`. Updated haiv-core map with "Deeper maps" cross-reference. Completed "The Charting Tools" quest.
- **Exploration journey**: Full `charting-tools-local-examples` journey in the atlas (7 entries).

## Key Decisions

- **Helper named `chart.py`**, not `atlas.py` — matches the command namespace. If atlas helpers grow beyond chart, they can get their own module later.
- **Examples live at `atlas/journeys/examples/`** — under journeys because examples *are* journeys. Follows the precedent of `eras/` living under `journeys/`.
- **Path conventions in `AtlasPaths`**, not hardcoded — `examples_dir` property ensures the convention lives in one place. Tests use the paths object too.
- **Maps organized conceptually, not by package** — `maps/commands/` groups by what things are, not where they live in code. Atlas structure is independent from codebase structure.
- **Commands as thin shells** — all domain logic in the helper. Commands only read args, call helpers, print results. No `ctx` crosses into the helper layer.

## Open Items

### Pre-existing test failures

These exist on main and are not related to this work:

- **`test_become` and `test_mine`**: 2 failures — Windows path separator issue, tests assert forward-slash paths but Windows produces backslashes.
- **`test_minds_stage` and `test_pop`**: 88 errors, cause not investigated.

### Template duplication

The briefing content in `briefing.md.j2` overlaps with `atlas/welcome.md`. This was noted during exploration (journey entry 005) but is out of scope for this task.

## Commits and Files Changed

- 7bbc6a1 feat: use project-local example journeys in hv chart
  - `haiv-lib/src/haiv/helpers/chart.py` (new — all domain logic)
  - `haiv-lib/src/haiv/paths.py` (added `examples_dir` to `AtlasPaths`)
  - `haiv-lib/tests/test_chart_helper.py` (new — 16 helper tests)
  - `haiv-core/src/haiv_core/commands/chart/_index_.py` (thinned to 27 lines)
  - `haiv-core/src/haiv_core/commands/chart/explore.py` (thinned to 88 lines)
  - `haiv-core/src/haiv_core/__assets__/chart/briefing.md.j2` (new)
  - `haiv-core/src/haiv_core/__assets__/chart/explore-start.md.j2` (dynamic file list)
  - `haiv-core/tests/test_chart.py` (use paths objects)
  - `haiv-core/tests/test_chart_explore.py` (use paths objects, new example tests)
