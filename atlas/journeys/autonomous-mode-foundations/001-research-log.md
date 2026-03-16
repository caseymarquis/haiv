# 001 — Research Log

**Explorer:** arc
**Date:** 2026-03-15
**Goal:** Understand the current staging, session, and pop infrastructure deeply enough to design autonomous mode — a new launch mode where minds run unsupervised with optional worktrees.

---

## What pulled me here

I'm tasked with three interconnected features: autonomous launch mode, optional worktrees, and session metadata that tracks mode so all tools can adapt. Before I can design anything, I need to understand what exists. The session system is the connective tissue — it's where mode metadata would live, and both `stage` and `pop` depend on it.

## What I searched in the atlas

**Maps:** `haiv-core.md` lists `commands/minds/stage.py`, `commands/pop.py`, and `resolvers/session.py`. `haiv-lib.md` lists `helpers/sessions.py` and `helpers/minds.py` as partially explored / uncharted. The TUI layer (`helpers/tui/`) is well-mapped — relevant because `hv start` launches minds through it.

**Quest board:** The Port City quest (paths.py) and The Context Factory quest (args.py) are adjacent but not blocking. The Settings System quest is interesting — session metadata might interact with settings.

**Journeys:**
- `mind-templates-atlas-integration/002` — Best existing coverage of `stage.py`. Describes the 6-step flow: pick name → determine branch → create worktree → scaffold mind → create session → print next steps. But this is a summary, not a deep read.
- `charting-tools-local-examples/006` — Partial exploration of `helpers/sessions.py`. Confirms the helper pattern (standalone functions, `Path` params, no `ctx`). Mentions `Session` dataclass. Doesn't detail the session schema or what fields exist.
- `charting-tools-local-examples/007` — Partial exploration of `helpers/minds.py`. Covers `scaffold_mind()` and `ensure_structure()`. Good for understanding mind creation but doesn't cover what I need for optional worktrees.
- `the-hook-system/005` — Shows how `stage.py` emits `AFTER_WORKTREE_CREATED`. Relevant because optional worktrees means this hook might not fire.

**What nobody has done:** A deep read of `pop.py`, or the full `Session` dataclass and its fields, or how sessions track state transitions.

## What's missing

1. **The `Session` dataclass** — what fields exist today? This is where mode metadata would live.
2. **`stage.py` internals** — I have summaries but need to see the actual code to understand where to inject autonomous/no-worktree logic.
3. **`pop.py`** — completely unexplored. How does wind-down work? What does it assume about worktrees?
4. **Session lifecycle** — how do sessions move through states? Who updates them and when?

## Where I might go

1. `helpers/sessions.py` — the `Session` dataclass and CRUD operations. This is the foundation of any metadata design.
2. `commands/minds/stage.py` — the full staging flow, with an eye on where worktree creation and session creation happen.
3. `commands/pop.py` — the wind-down flow, with an eye on worktree assumptions.
4. `helpers/minds.py` — specifically `scaffold_mind()` to understand what changes for no-worktree minds.

Starting with sessions because it's the data layer everything else builds on.
