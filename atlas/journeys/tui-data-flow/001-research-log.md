# 001 — Research Log

> **Annotation (2026-03-22):** This journey documents the *old* TUI data architecture. The exploration led directly to a redesign completed the same day. The architecture described in entries 002–007 no longer exists — `TuiModelSection`, `ConcurrencyError`, version-based diffing, `HudSection`, `ErrorsSection`, and the mutator-based `write()` API have all been replaced. See the updated haiv-tui and haiv-lib maps for the current architecture. The journey is preserved as history of how the old design was understood and why it needed to change.

**Explorer:** Wren (COO on field trip)
**Date:** 2026-03-22
**Goal:** Understand how the TUI assembles and stores data from multiple sources (sessions, git), and why the git branch display is flakey. Map the path toward separating data sources into independent locked models.

---

## What pulled me here

The git branch info in `hv sessions` output is unreliable — sometimes it shows stale data, sometimes it's wrong. Casey identified the root cause: we load data from multiple sources (session TOML, git) into a single locked model. When one source is slow or fails, it poisons the whole snapshot. The fix is architectural: separate locked models per data source, consolidate at render time.

I'm the COO. I don't usually explore. But this is a two-hour window, the territory is uncharted, and I want to understand the data flow myself before we start cutting.

## What I searched in the atlas

**Maps:** The haiv-tui overview shows the file layout but `store.py` ("TuiStore — signal dispatch from model snapshots") is explicitly listed as uncharted. `widgets/sessions.py` is also uncharted. The haiv-lib map covers `helpers/tui/` architecture (three-tier: tui.py facade → helpers.py logic → terminal.py WezTerm) but doesn't detail what data helpers.py assembles or how git info gets mixed in.

**Sessions map:** The Session dataclass has a `branch` field (the worktree branch) but no git tracking info (ahead/behind counts, remote status). That info must come from somewhere else and get merged in.

**Quest board:** Nothing about TUI data flow. The Settings System quest is adjacent but different territory.

**Journeys:** No prior exploration of TUI internals.

## What's missing

- How does `store.py` work? What's the "locked model" pattern?
- Where does git branch info get fetched? (`wrappers/git.py`? Inside a helper?)
- How/where does git data merge with session data?
- What does `widgets/sessions.py` consume — raw sessions, enriched sessions, something else?
- What's the poll loop doing? (app.py mentions 0.1s interval)

## Where I plan to go

1. `haiv-tui/src/haiv_tui/store.py` — the locked model. This is the heart of the problem.
2. `haiv-tui/src/haiv_tui/app.py` — the poll loop and data assembly.
3. `haiv-tui/src/haiv_tui/widgets/sessions.py` — what the widget expects.
4. `haiv-lib/src/haiv/wrappers/git.py` — the git wrapper.
5. `haiv-lib/src/haiv/helpers/tui/helpers.py` — where session + git data likely gets combined.

Starting with `store.py` because that's the locked model Casey wants to split. Need to understand the shape before I can redesign it.
