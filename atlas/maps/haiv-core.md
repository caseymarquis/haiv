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

## `resolvers/` — "The Interpreters"

Concrete resolver implementations. Each file is a thin bridge: translates `ResolverContext` into helper-specific arguments and delegates. ~30-40 lines each.

- **`mind.py`** — Converts a mind name string to a `Mind` object via `resolve_mind()` from `helpers/minds.py`. Also runs `mind.ensure_structure(fix=True)` as a side effect — every mind resolution auto-repairs structural issues. Errors: `MindNotFoundError`, `DuplicateMindError` (hard stops); structural issues are warnings only.
- **`session.py`** — Converts a session identifier (short ID like `"3"` or partial/full UUID) to a `Session` object via `get_session()` from `helpers/sessions.py`. Defines its own `SessionNotFoundError`.

These are the only two resolvers in core. Communities can add their own by creating `resolvers/foo.py` in project or user packages. The resolver infrastructure (discovery, loading, dispatch) lives in haiv-lib's `_infrastructure/resolvers.py` — see "The Translators" in the haiv-lib map, and `journeys/the-resolver-system/` for the full story.

## Uncharted

- `__assets__/` — Jinja2 templates for mind scaffolding, pop AARs, roles
- Most commands beyond what's been read during journeys
