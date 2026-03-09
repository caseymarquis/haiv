# 003 — loader.py

**Explorer:** Luna the Explorer
**Date:** 2026-03-07

---

## Why I Came Here

Routing finds the file. Loading turns the file into something you can call. I needed to see how `commands/chart.py` becomes an object with `.define()` and `.execute()`.

## What I Found

`haiv-lib/src/haiv/_infrastructure/loader.py` — surprisingly small. Two things:

### `load_command(file: Path) -> Command`
Uses `importlib.util` to dynamically load a `.py` file as a module. Wraps it in a `Command` object. Each load gets a unique module name (`haiv_command_{stem}_{id}`) to avoid Python's module cache.

### `Command` class
A thin wrapper that provides a consistent lifecycle interface:
- `define()` → required, calls `module.define()`
- `setup(ctx)` → optional, no-op if absent
- `execute(ctx)` → required, calls `module.execute()`
- `teardown(ctx)` → optional, no-op if absent

So a command can optionally have `setup()` and `teardown()` — I didn't know that. My chart command doesn't use them, but a command that needs to register dependencies or clean up resources could.

There's also `load_commands_module()` which loads a `commands/__init__.py` — this is how the routing system loads command packages from directories not on `sys.path` (like `haiv_project/commands/`).

## The Trade Route So Far

The path from text to execution is becoming clear:

1. **CLI receives** `"hv become luna"` → strips `"hv"`, passes `"become luna"` onward
2. **`find_route()`** walks the filesystem tree, matches `become/_mind_.py`, captures `mind="luna"`
3. **`load_command()`** dynamically imports the matched `.py` file, wraps in `Command`
4. **Something** builds the `Ctx` with parsed args and resolved params — this is `args.py` probably
5. **`command.execute(ctx)`** runs the actual command

I have steps 2 and 3 mapped. Steps 1, 4, and 5 are the gaps.

## Where I'm Going Next

`runner.py` — there's a runner module that might orchestrate the full flow. Or I should look at the CLI entry point to see who kicks this all off.
