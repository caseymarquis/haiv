# helpers

Domain logic for haiv. Commands handle user interaction; helpers do the actual work. Every helper follows the same pattern: standalone functions with explicit `Path` parameters, no `ctx` dependency, reusable from any command or other helper.

**Location:** `worktrees/main/haiv-lib/src/haiv/helpers/`

```
helpers/
├── sessions.py     # Session persistence and lifecycle
├── minds.py        # Mind scaffolding and management
├── commands.py     # Command discovery
├── packages.py     # Package discovery
├── users.py        # User discovery
└── tui/            # TUI management (see haiv-lib map)
```

## The pattern

- **Standalone functions** — no classes with state, no singletons
- **Explicit parameters** — functions take `Path` to a file or directory, not `ctx`
- **One domain concept per file** — `sessions.py` is entirely about sessions, `minds.py` entirely about minds
- **No command awareness** — helpers don't know which command called them
- **Return data, not display strings** — commands decide what to show

This pattern is well-established and consistent. See `journeys/charting-tools-local-examples/006` for the original exploration.

## Helper maps

- [sessions](sessions.md) — Session dataclass, CRUD, lifecycle

## Uncharted

- `minds.py` — `scaffold_mind()`, `Mind` class, `ensure_structure()` (partially explored in `journeys/charting-tools-local-examples/007`)
- `commands.py`, `packages.py`, `users.py`
- `tui/` — covered in the haiv-lib map
