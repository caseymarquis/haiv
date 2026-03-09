# 001 — Research Log

**Explorer:** Ember
**Date:** 2026-03-08
**Quest:** The Hook System (Reward: Compass)
**Goal:** Understand how haiv hooks work so we can extend `hv pop` with a hook point.

---

## What I Searched For

**Maps:** `maps/haiv-lib.md` lists `haiv_hooks.py` under `_infrastructure/` ("The Silk Road"). No description, no nickname — just a filename in the tree. The Silk Road section says it's "the full path a command travels from `hv <something>` to running code" and points to the routing-table journey, but that journey doesn't mention hooks.

**Quest board:** The Hook System quest was just posted (by me). No prior quests or completed work related to hooks.

**Journeys:** The routing-table journey maps the command lifecycle: routing → loading → context building → `setup → execute → teardown`. Hooks aren't mentioned. The mind-templates journey and my own crash-recovery journey don't touch hooks either.

**CLAUDE.md:** No mention of hooks.

## What's Missing

Everything. The atlas knows `haiv_hooks.py` exists and nothing else. No one has read this file or documented the hook mechanism.

## Where I Plan to Go

1. **`haiv-lib/src/haiv/_infrastructure/haiv_hooks.py`** — The hook system itself. What does it provide?
2. **Grep for usage** — Find where hooks are called from. The command lifecycle (`runner.py`) seems like a natural place. Also search for any existing hook points in commands.
3. **`haiv-lib/src/haiv/cmd.py`** — If hooks integrate with the command system, they might show up in `Def` or `Ctx`.
4. **Any tests** — Tests would show intended usage patterns.

Starting with the source file, then following the threads.
