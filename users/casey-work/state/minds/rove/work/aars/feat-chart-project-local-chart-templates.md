# AAR: feat(chart): project-local chart templates

## Summary

Moved chart Jinja templates from bundled `__assets__/chart/` to project-local `atlas/templates/chart/` with per-file copy-on-first-run semantics. Projects can now customize how chart output looks by editing templates in place. Missing templates are restored individually from bundled defaults — no all-or-nothing behavior.

### Deliverables

- **`ensure_chart_templates()`**: New helper in `helpers/chart.py` that checks each `.j2` file individually and copies missing ones from bundled defaults.
- **`AtlasPaths.templates_dir`**: New property returning `atlas/templates/`, following `examples_dir` precedent.
- **Updated commands**: Both `_index_.py` and `explore.py` create a `TemplateRenderer` pointed at the project-local chart templates directory instead of using `ctx.templates`.
- **8 new tests**: Cover copying, per-file preservation, partial restoration, idempotency, and edge cases.

## Key Decisions

- **Per-file checks instead of directory-level** — Human collaborator's call. A directory-level "has content" check (like `ensure_example_journey()`) would silently skip restoration if even one file existed, leading to cryptic Jinja `TemplateNotFound` errors when a specific template was missing. Checking each file individually means partial deletions recover gracefully.
- **Templates nest under `atlas/templates/chart/`**, not flat `atlas/templates/` — leaves room for other command families to have their own project-local templates without collisions.
- **Commands create their own `TemplateRenderer`** — `ctx.templates` still points at the package's `__assets__/` for other commands. Only chart commands switch to the project-local path. This avoids touching the shared infrastructure.
- **Template paths shortened** from `"chart/briefing.md.j2"` to `"briefing.md.j2"` — since the renderer root shifts from `__assets__/` to `atlas/templates/chart/`, the `chart/` prefix is no longer needed.

## Open Items

### Pre-existing test failures

Same as nova's previous AAR — unrelated to this work:

- **haiv-lib**: 6 failures + 17 errors in `test_terminal_manager`, `test_tui_server`, `test_git`, `test_tui_helpers` (WezTerm/git subprocess dependencies).
- **haiv-core**: 2 failures + 88 errors in `test_pop` and related tests.

None.

## Commits and Files Changed

- f5c0260 feat(chart): use project-local templates with copy-on-first-run
  - `haiv-lib/src/haiv/paths.py` (added `templates_dir` to `AtlasPaths`)
  - `haiv-lib/src/haiv/helpers/chart.py` (added `ensure_chart_templates()`, updated template paths)
  - `haiv-lib/tests/test_chart_helper.py` (8 new tests for `TestEnsureChartTemplates`)
  - `haiv-core/src/haiv_core/commands/chart/_index_.py` (use project-local templates)
  - `haiv-core/src/haiv_core/commands/chart/explore.py` (use project-local templates)
