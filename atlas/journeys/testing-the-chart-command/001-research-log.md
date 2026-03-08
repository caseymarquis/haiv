# 001 — Research Log

**Explorer:** Luna
**Date:** 2026-03-07
**Goal:** Write tests for `hv chart`.

---

## What I Searched For

- **Maps:** None exist yet.
- **Quest board:** Three open quests (Port City, Routing Table, Resolver Mystery). None directly about testing, but the Routing Table quest is adjacent — understanding how commands get routed might matter for test setup.
- **Journals:** My earlier journey ("building-the-chart-command") entry 002 mentions `haiv.test` provides progressive testing: `routes_to()`, `parse()`, `execute()`. But I never actually read `haiv.test` or looked at an existing test file. That's the gap.

## What's Missing from the Atlas

There's nothing in the atlas about how to test commands. Not in the maps (none exist), not in any journal. This is uncharted territory.

## Where I Plan to Go

1. `haiv-lib/src/haiv/test.py` — the testing framework itself. I need to understand `routes_to()`, `parse()`, and `execute()` and what they expect.
2. Existing tests in `haiv-core/tests/` — see how other commands are tested. Find a simple example to follow.
3. Write the tests.
