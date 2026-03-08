# 004 — The Full Journey of a Command

**Explorer:** Luna the Explorer
**Date:** 2026-03-07

---

## Why I Came Here

I read `runner.py` (tiny — just `setup → execute → teardown` in a try/finally) and then went to the CLI entry point to see who orchestrates everything. `haiv-cli/src/haiv_cli/__init__.py` is a single file that contains the entire CLI. This is where text becomes action.

## The Complete Trade Route

Here's the full journey of `hv become luna`, start to finish:

### 1. Entry (`main()`)
The shell runs `hv become luna`. `sys.argv` is `["hv", "become", "luna"]`. The CLI joins args into `"become luna"`.

### 2. Discovery (`_find_command()`)
The CLI searches for a matching command across three sources, **in this order**:
1. **haiv_user** (highest precedence) — `users/{user}/src/haiv_user/commands/`
2. **haiv_project** — `src/haiv_project/commands/`
3. **haiv_core** (fallback, always available) — installed package

This is the opposite of what I assumed! CLAUDE.md says resolution is `haiv_core → haiv_project → haiv_user`, but the *search* order is user-first. User commands override project commands, which override core. The CLAUDE.md description is about the conceptual layering (core is the foundation), not the precedence.

Each source calls `find_route()` from `routing.py`. First match wins.

### 3. Loading (`load_command()`)
The matched `.py` file is dynamically imported and wrapped in a `Command` object.

### 4. Context Building (`build_ctx()`)
This is in `args.py` (which I haven't read yet). It takes the route (with captured params and raw flags), the command's `define()` (which declares what flags exist), and builds the `Ctx` object. Resolvers transform raw param values into rich objects here.

### 5. Execution (`run_command()`)
`setup(ctx)` → `execute(ctx)` → `teardown(ctx)`, with teardown in a `finally`.

### An Important Detail: Resolver Assembly

Before building the context, the CLI collects resolver directories from all three package levels (core, project, user). It calls `make_resolver(pkg_roots)` to build a single resolver callback. This means resolvers, like commands, can be overridden at each level. The resolver system is a whole separate mechanism — the Resolver Mystery quest covers this.

### Error Handling

If the command isn't found in any source, the CLI prints which sources it checked and which it couldn't reach (with reasons). This is helpful — you can see if haiv_project failed to load because you're not in a haiv repo, for instance.

## What I Noticed

The `_find_command` search order (user → project → core) surprised me. It's the key design decision: higher-level packages can shadow lower-level commands. A user could override `hv help` with their own version. That's powerful but also means you need to know the precedence when debugging "why is my command not running?"

## The Trade Route, Mapped

```
"hv become luna"
    │
    ▼
main() ─── sys.argv → command_string
    │
    ▼
_find_command() ─── user → project → core (first match wins)
    │
    ▼
find_route() ─── filesystem tree walk, literal > param
    │
    ▼
load_command() ─── importlib, wraps in Command
    │
    ▼
build_ctx() ─── route + define() → Ctx with parsed args + resolved params
    │
    ▼
run_command() ─── setup → execute → teardown
```

## Where I'm Going Next

I think the quest is complete. I've mapped the route from typed text to running code. The one gap is `build_ctx()` in `args.py` — but that's more about argument parsing than routing. I'll note it as a tangent for the quest board.
