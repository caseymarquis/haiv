# haiv-lib

The foundation. Every command, every helper, every path resolution passes through here. If haiv-core is where commands *live*, haiv-lib is the ground they stand on.

**Location:** `worktrees/main/haiv-lib/src/haiv/`

```
haiv/
├── paths.py              "The Port City"
├── cmd.py                "The Outfitter"
├── test.py               "The Proving Ground"
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

## `_infrastructure/` — "The Silk Road"

The full path a command travels from `hv <something>` to running code. Starts at `haiv-cli/__init__.py:main()`, searches user → project → core for a match, loads the file, builds context, runs the lifecycle. See `journeys/the-routing-table/` for the full story.

## Uncharted

Known to exist but not properly explored. Earn a reward, give them a name.

- `helpers/` — Utility functions shared across commands (minds, sessions, commands, packages, users, tui)
- `templates.py` — Jinja2 template rendering for `__assets__/`
- `wrappers/` — Wrappers around external tools (git, wezterm)
- `settings.py` — Project configuration
- `errors.py` — Error types
