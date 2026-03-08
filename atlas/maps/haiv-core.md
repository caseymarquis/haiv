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
    ├── chart.py             # hv chart — atlas exploration helper
    ├── help.py              # hv help — list commands
    ├── init.py              # hv init — initialize a haiv project
    └── mine.py              # hv mine — claim work
```

---

## `haiv_hook_points.py`

Single source of truth for hook points emitted by core commands. Defines request dataclasses and `HaivHookPoint` constants. Currently has one: `AFTER_WORKTREE_CREATED` (emitted by `hv minds stage`). See `journeys/the-hook-system/`.

## Uncharted

- `resolvers/` — param resolvers for `mind` and `session` types (see The Resolver Mystery quest)
- `__assets__/` — Jinja2 templates for mind scaffolding, pop AARs, roles
- Most commands beyond what's been read during journeys
