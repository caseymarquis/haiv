# haiv-cli

The front door. A single file that turns `hv <something>` into a running command. Everything passes through here, nothing lives here.

**Location:** `worktrees/main/haiv-cli/src/haiv_cli/`

```
haiv_cli/
└── __init__.py       # main() — the entire CLI
```

---

## `__init__.py`

Contains `main()` — the entry point for every `hv` invocation. Orchestrates the full command lifecycle:

1. **Discovery** (`_find_command()`) — searches user → project → core for a matching command file. First match wins. This is user-first precedence, opposite of the conceptual layering.
2. **Loading** — dynamically imports the matched `.py` file via `load_command()`.
3. **Hook setup** — if `definition.enable_haiv_hooks` is true, runs `configure_haiv_hooks(pkg_roots)` to discover and register handlers.
4. **Context building** — `build_ctx()` assembles the `Ctx` object from the route, definition, resolver, and hook registry.
5. **Execution** — `run_command()` runs the `setup → execute → teardown` lifecycle.

Error handling: if the command isn't found, prints which sources were checked and why each failed. Helpful for debugging shadowing issues.

See `journeys/the-routing-table/` for the full story.
