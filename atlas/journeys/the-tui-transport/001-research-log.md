# 001 — Research Log

**Explorer:** Luna
**Date:** 2026-03-24
**Goal:** Understand the TUI's data transport — how raw data gets from producers (commands, workers) into the running TUI. I need to know this well enough to design a command queue alongside it.

---

## What pulled me here

I've been assigned to build a command queue for the TUI — a channel that lets `hv` commands send instructions *into* the running app (focus a worktree, show a notification). The existing transport moves raw data *in* via `write_raw()`. My command queue needs to sit alongside it, following the same patterns.

But I've never opened `TuiServer` or `TuiLocalClient`. The atlas maps tell me the architecture — dirty tracking, poll loop, blinker signals — but not the mechanics. How does thread safety work? What does the server actually look like inside? I need to see the gears before I can add a new one.

## What I searched in the atlas

**Maps:** `haiv-lib/overview.md` has the `helpers/tui/` tree and describes each file's role. `TuiModel.py` holds raw data sections. `protocol.py` defines `ModelClient` with `read()` and `write_raw()`. `TuiClient.py` is remote IPC. The map says the command queue should integrate with the signal pattern.

`haiv-tui/overview.md` describes the data flow: raw data → TuiModel sections → TuiServer (dirty tracking) → poll loop drains dirty → TuiStore fires signals → widgets render. The poll loop in `app.py` runs at 0.1s intervals.

**Quest board:** The Widget Dependency Injection quest is adjacent but different — it's about how widgets receive deps, not how data flows in. No quest directly covers the transport internals.

**Journeys:** Nobody has explored TuiServer or TuiLocalClient internals. The data flow is described at the architecture level but the implementation is uncharted.

## What's missing

- What does `TuiServer` look like inside? How does dirty tracking work?
- What does `TuiLocalClient` look like? How does `write_raw()` work?
- The `ModelClient` protocol — what's the full interface?
- Thread safety — `write_raw()` can be called from any thread. What's the locking strategy?
- How does the poll loop in `app.py` drain and dispatch?

## Where I plan to go

1. `protocol.py` — the shared interface. This is where the command queue will live, so I need to understand what's there now.
2. `TuiServer` — the receiving end. Dirty tracking, snapshot management.
3. `TuiLocalClient` — the in-process sender. How `write_raw()` works.
4. `app.py` poll loop — how the app drains the server and feeds the store.

Starting with the protocol feels right. That's where both clients agree on what they can do.
