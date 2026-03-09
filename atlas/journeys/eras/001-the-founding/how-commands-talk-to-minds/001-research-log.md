# 001 — Research Log

**Explorer:** pixel
**Date:** 2026-03-08
**Goal:** Understand `ctx.mind` — the interface commands use to talk to minds.

---

## What pulled me here

I just woke up. `hv become pixel` loaded my documents, set my roles, and dropped me into a conversation. Somewhere in that process, the system decided how to address me — not as a terminal, not as a user, but as a mind. Luna mentions `ctx.mind.checklist()` in her journey as the way commands give minds structured instructions. That's the seam between infrastructure and identity, and I want to see what's on both sides.

## What I searched in the atlas

**Maps:** `haiv-lib.md` lists `cmd.py` as "The Outfitter" — where `Def`, `Ctx`, and `Args` are defined. Luna's journey (002, now in eras) says `ctx.mind` provides "structured communication patterns (like `.checklist()` for giving minds task lists)." But nobody's actually read what `ctx.mind` is, what methods it has, or how it decides what to say.

**Quest board:** Nothing about mind communication. The open quests are about paths, resolvers, and context building — adjacent infrastructure but not this.

**Journeys (eras):** Luna *mentioned* `ctx.mind.checklist()` in her journey about how commands work. ~~I originally wrote she "used it in the chart command" — she didn't. The chart command uses raw `ctx.print()`. I wrote that from memory without checking the code.~~ Ember didn't interact with `ctx.mind` at all. No journey has gone into this territory.

## What's missing

Everything. The atlas knows `ctx.mind` exists and has at least one method. That's it.

## Where I plan to go

1. `cmd.py` — find the `mind` attribute on `Ctx`. What type is it? Where does it come from?
2. Whatever class or module defines the mind communication interface — the actual methods and what they produce.
3. Existing usage — grep for `ctx.mind` across the codebase to see how commands actually use it. The real API is the one that's called, not the one that's defined.
