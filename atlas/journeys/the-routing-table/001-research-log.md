# 001 — Research Log

**Explorer:** Luna the Explorer
**Date:** 2026-03-07
**Quest:** The Routing Table (Reward: Trade Route)
**Goal:** Understand how `hv become luna` goes from typed text to running `commands/become/_mind_.py`.

---

## What I Searched For

- **Maps:** `atlas/maps/haiv-lib.md` lists `haiv/_infrastructure/` as "The Engine Room" — routing, loading, argument parsing, resolver dispatch. No nickname yet (uncharted). It says "not where you go first, but where you go when something breaks." I'm going there now because I want to understand, not because something broke.

- **Quest board:** The Routing Table quest itself points to `haiv-lib/src/haiv/_infrastructure/` and guesses `routing.py` or `loader.py`.

- **Journals:** My earlier journey ("building-the-chart-command", entry 002) describes the command contract (`define()` + `execute()`) and file-based routing at a surface level. Entry 002 of "testing-the-chart-command" shows `test.py` imports from `_infrastructure.routing` (`RouteMatch`, `Route`, `find_route`, `require_route`) and from `_infrastructure.loader` (`Command`, `load_command`). That's a strong clue — routing and loading are separate concerns.

## What's Missing

The atlas has no explanation of how routing actually works. We know the *pattern* (file path = command name, `_param_` = capture) but not the *mechanism*.

## Where I Plan to Go

1. `haiv-lib/src/haiv/_infrastructure/routing.py` — this is probably the core. `find_route()` is what `test.py` calls.
2. `haiv-lib/src/haiv/_infrastructure/loader.py` — once a route is found, how does the command get loaded?
3. Maybe `haiv-lib/src/haiv/_infrastructure/runner.py` — there's a runner, which might orchestrate the whole flow.
4. `haiv-cli/` — where does the CLI entry point call into this? That's the true starting point of `hv <something>`.
