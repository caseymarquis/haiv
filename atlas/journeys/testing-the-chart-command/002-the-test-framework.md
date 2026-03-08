# 002 — The Test Framework

**Explorer:** Luna
**Date:** 2026-03-07
**Goal:** Understand how to test a command so I can test `hv chart`.

---

## `haiv-lib/src/haiv/test.py`

This is the testing toolkit. Three progressive levels:

- **`test.require_routes_to("chart")`** — Verifies file-based routing. Does `chart` resolve to a file? Doesn't load or run anything.
- **`test.parse("chart --goal foo")`** — Routes, loads `define()`, parses args. Returns a `cmd.Ctx` you can inspect.
- **`test.execute("chart")`** — Routes, parses, and runs `execute()`. Returns `ExecuteResult` with the ctx. Uses `capsys` to capture printed output.

The framework auto-discovers the commands module by walking up from the test file to find `src/<package>/commands/`. No manual wiring needed.

It creates a temp directory as a fake haiv root, with a test user ("testinius"). This means `ctx.paths.root` points to a temp dir — my command creates `atlas/` under there, so tests won't touch the real atlas.

There's also a `Sandbox` class for integration tests that need more control, but the simple `test.execute()` is enough for `hv chart`.

## `haiv-core/tests/test_help.py`

Good example to follow. Pattern:
- `TestHelpRouting` — one test, checks the file routes correctly
- `TestHelpListing` — runs `test.execute("help")`, uses `capsys.readouterr()` to check output
- Grouped by behavior, not by function

The tests are clean and direct. No over-mocking. They test what the user sees (output), not internal state.

## Where I'm Going Next

Writing `test_chart.py`. I need to test:
1. Routing — `chart` routes to `chart.py`
2. Output without goal — contains the key sections (FINDING, RULES, REWARDS)
3. Output with goal — includes the goal in output
4. Atlas directory creation — running the command should create `atlas/`, `journeys/`, `maps/`
