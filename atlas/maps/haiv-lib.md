# haiv-lib

The foundation. Every command, every helper, every path resolution passes through here. If haiv-core is where commands *live*, haiv-lib is the ground they stand on.

**Location:** `worktrees/main/haiv-lib/src/haiv/`

```
haiv/
├── paths.py              "The Port City"
├── cmd.py                "The Outfitter"
├── test.py               "The Proving Ground"
├── haiv_hooks.py         "The Signal Fires"
├── errors.py
├── settings.py
├── templates.py
├── util.py
├── _infrastructure/      → The Silk Road runs through here
│   ├── routing.py
│   ├── loader.py
│   ├── runner.py
│   ├── args.py
│   ├── resolvers.py
│   ├── identity.py
│   ├── env.py
│   └── haiv_hooks.py
├── helpers/
│   ├── minds.py
│   ├── sessions.py
│   ├── commands.py
│   ├── packages.py
│   ├── users.py
│   └── tui/
└── wrappers/
    ├── git.py
    └── wezterm.py
```

---

## `paths.py` — "The Port City"

The hub through which every command accesses the filesystem. Defines how the whole system sees its own shape — project root, user dirs, worktrees, packages, minds. If you understand this file, you know where everything is.

## `cmd.py` — "The Outfitter"

Where commands get equipped before they set out. Defines `Def` (what a command declares about itself), `Ctx` (the kit every command carries), and `Args` (what the caller asked for). Every command's `define()` and `execute()` speak this language.

## `test.py` — "The Proving Ground"

Where commands are tested. Three progressive levels: `routes_to()` (does the file exist?), `parse()` (does it define correctly?), `execute()` (does it run correctly?). Creates temp sandboxes so tests never touch real state.

## `haiv_hooks.py` — "The Signal Fires"

The hook system's public API. Commands define typed extension points (`HaivHookPoint[TReq, TRes]`) and emit them during execution. Other packages subscribe by placing `@haiv_hook`-decorated handlers in their `haiv_hook_handlers/` directory.

Two files, split by audience:
- **`haiv_hooks.py`** (public) — `HaivHookPoint`, `@haiv_hook` decorator, `HaivHookHandler` protocol. What command authors and handler authors use.
- **`_infrastructure/haiv_hooks.py`** (internal) — `HaivHookRegistry`, discovery pipeline (`discover` → `load` → `collect` → `configure`). What the CLI uses at startup.

Hook points are defined in each package's `haiv_hook_points.py`. Commands opt in with `enable_haiv_hooks=True` in `define()`. Discovery is lazy — only commands that opt in pay the cost. Handlers run in package order: core → project → user.

See `journeys/the-hook-system/` for the full story.

## `_infrastructure/` — "The Silk Road"

The full path a command travels from `hv <something>` to running code. Starts at `haiv-cli/__init__.py:main()`, searches user → project → core for a match, loads the file, builds context, runs the lifecycle. See `journeys/the-routing-table/` for the full story.

### `_infrastructure/resolvers.py` + `_infrastructure/args.py` — "The Translators"

The resolver system transforms raw string values into domain objects. It operates in three layers:

1. **Infrastructure** (`resolvers.py`) — Discovery, loading, composition. `make_resolver(pkg_roots)` scans `resolvers/` directories across all packages (core → project → user, last writer wins) and returns a single callback closure. No base classes — a resolver is just a `.py` file with `resolve(value: str, ctx: ResolverContext) -> Any`.

2. **Concrete resolvers** (in each package's `resolvers/` dir) — Thin bridges that translate `ResolverContext` into helper-specific arguments and delegate. ~30 lines each. See haiv-core's `resolvers/mind.py` and `resolvers/session.py`.

3. **Consumer** (`args.py`) — `build_ctx()` calls the resolver callback for both route params and flags. Creates `ResolveRequest(param, resolver, value)` and feeds it to the callback. Resolved values land in `args._values` alongside raw values — commands access both uniformly.

Key design choices:
- **Implicit vs explicit resolution.** `_mind_/` (param == resolver) is implicit: resolver is optional, raw value passes through if none exists. `_target_as_mind_/` (param != resolver) is explicit: resolver must exist or `UnknownResolverError`.
- **Graceful degradation.** Broken resolvers are skipped with warnings. Missing implicit resolvers silently pass through. The system never blocks the user unnecessarily.
- **Flags can have resolvers too.** Any `Flag(resolver="mind")` in a command definition resolves its values through the same pipeline as route params.

See `journeys/the-resolver-system/` for the full story.

## `helpers/tui/`

The TUI management layer. Three-tier architecture with strict separation:

- **`tui.py`** — Thin convenience facade. Holds pre-loaded dependencies (WezTerm, paths, client) so command authors can write `ctx.tui.start()`. Every method is a one-line passthrough to `helpers.py`. No logic belongs here.
- **`helpers.py`** — All real logic as standalone functions with explicit parameters. Independently testable, callable from both commands and the TUI app. Naming convention: `noun_verb` (e.g. `workspace_start`, `mind_launch`, `sessions_refresh`).
- **`terminal.py`** (`TerminalManager`) — Encapsulates WezTerm specifics: tab naming conventions (`hv({project})`, `hv({project}):mind`, `~mind`), pane splitting, parking minds, workspace lifecycle. Helpers take a TerminalManager but don't leak WezTerm details to their callers.

The TUI app (`haiv-tui`) calls `helpers.py` directly — it does NOT use the `tui.py` facade. This keeps the app decoupled from the command-side dependency bag.

See `journeys/hv-start-crash-recovery/` for how workspace detection and recovery works.

## `wrappers/wezterm.py`

Thin subprocess wrapper around `wezterm cli`. Educational by default — prints commands as they run, provides diagnostic prompts on failure. Use `quiet=True` to suppress. Key operations: `list_panes`, `spawn`, `split_pane`, `send_text`, `get_text`, `set_tab_title`, `activate_pane`, `kill_pane`. Also `run_external` for commands outside the CLI context (like `wezterm start`).

## Uncharted

Known to exist but not properly explored. Earn a reward, give them a name.

- `helpers/minds.py` — Mind scaffolding and management (see `journeys/mind-templates-atlas-integration/`)
- `helpers/sessions.py` — Session persistence and lookup
- `helpers/commands.py`, `helpers/packages.py`, `helpers/users.py` — Other helper modules
- `templates.py` — Jinja2 template rendering for `__assets__/`
- `wrappers/git.py` — Git subprocess wrapper
- `settings.py` — Project configuration
- `errors.py` — Error types
