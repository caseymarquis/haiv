# haiv-core

Where commands live. The default set of capabilities every haiv community gets. Higher-level packages (project, user) can shadow these commands.

**Location:** `worktrees/main/haiv-core/src/haiv_core/`

```
haiv_core/
├── haiv_hook_points.py      # Hook point definitions + request types
├── resolvers/               # mind.py, session.py — param resolvers
├── __assets__/              # Templates (minds/, pop/, roles/)
└── commands/
    ├── become/              # hv become <mind> — wake up as a mind
    ├── start/               # hv start / hv start <mind>
    │   ├── _index_.py       #   bare start: ensure workspace
    │   └── _mind_.py        #   start mind: launch in hud
    ├── minds/
    │   └── stage.py         # hv minds stage — prep a mind for work
    ├── sessions/            # hv sessions — list/manage sessions
    ├── tui/
    │   └── debug.py         # hv tui debug — print pane layout
    ├── pop.py               # hv pop — wind down a mind's assignment
    ├── chart/               # hv chart — atlas navigation and exploration
    │   ├── _index_.py       #   bare chart: atlas briefing + bootstrapping
    │   └── explore.py       #   chart explore: guided codebase exploration
    ├── help.py              # hv help — list commands
    ├── init.py              # hv init — initialize a haiv project
    └── mine.py              # hv mine — claim work
```

---

## `haiv_hook_points.py`

Single source of truth for hook points emitted by core commands. Defines request dataclasses and `HaivHookPoint` constants. Currently has one: `AFTER_WORKTREE_CREATED` (emitted by `hv minds stage`). See `journeys/the-hook-system/`.

## `resolvers/` — "The Interpreters"

Concrete resolver implementations. Each file is a thin bridge: translates `ResolverContext` into helper-specific arguments and delegates. ~30-40 lines each. Two resolvers in core: `mind.py` (name → `Mind` object) and `session.py` (identifier → `Session` object). Communities can add their own. See `journeys/the-resolver-system/` for the full story.

## Command maps

Detailed maps for individual commands and groups live in [commands/](commands/):

- [chart](commands/chart.md) — Atlas navigation and guided exploration
- [stage](commands/stage.md) — Prep a mind for a new task (worktree, scaffold, session)
- [pop](commands/pop.md) — Wind down a mind's assignment (merge, cleanup, recycling)

## Uncharted

- `__assets__/` — Jinja2 templates for mind scaffolding, pop AARs, roles, and chart exploration
- `commands/become/` — Wake up as a mind
- `commands/start/` — Launch minds in the TUI
- `commands/sessions/` — Session listing and management
- `commands/help.py`, `commands/init.py`, `commands/mine.py`
