# 005 — The Context Factory (Where Resolvers Meet Commands)

**File:** `worktrees/main/haiv-lib/src/haiv/_infrastructure/args.py`

## Why I came here

I've seen the resolver infrastructure (discovery, loading, composition) and the concrete resolvers (mind, session). The missing piece is the *consumer* — how does `build_ctx()` create `ResolveRequest` objects and feed them to the resolver callback? This is where the circle closes: raw input → resolver → rich object → command context.

## What I found

182 lines. Two functions: `build_ctx()` and `_parse_flags()`. And the `ResolveRequest` dataclass I've been curious about.

**`ResolveRequest` is exactly what I predicted.** Three fields: `param` (the parameter name), `resolver` (which resolver to use), `value` (the raw string). The docstring has a beautiful example showing two params that use the *same* resolver but different param names:
```
Route: commands/_mind_/message/_target_as_mind_/send.py
→ ResolveRequest(param="mind", resolver="mind", value="forge")
→ ResolveRequest(param="target", resolver="mind", value="specs")
```
This is the explicit naming in action. The resolver system resolves *values*, not *params*. The param name is just where the resolved value gets stored.

**Resolution happens in two places.** This was the surprise.

1. **Route params** (lines 72-81): For each captured param from the route (like `_mind_/` capturing `"pulse"`), `build_ctx()` creates a `ResolveRequest` from the `ParamCapture`'s value and resolver name, calls the resolve callback, and stores the result in `args._values[param_name]`.

2. **Flags** (lines 170-179 in `_parse_flags()`): Flags can *also* have resolvers! If a flag definition has `flag_def.resolver` set, each of its values gets resolved through the same callback. So you could define `Flag("target", resolver="mind")` on a command, and `--target wren` would resolve `"wren"` to a `Mind` object.

I hadn't considered this. Resolvers aren't just for route params — they work for flags too. The same machinery, same callback, same concrete resolvers. A flag with `resolver="mind"` and a route param `_mind_/` both go through `resolvers/mind.py`.

**The resolve callback is optional.** `build_ctx()` takes `resolve: Callable | None`. If `None`, params keep their raw string values. This is the testing seam — tests can pass a mock resolver or no resolver at all. The `resolvers.py` infrastructure exists at the CLI level; at the library level, it's just a callback.

**Everything becomes `args._values`.** Both resolved params and parsed flags end up in the same dictionary. The resolved `Mind` object from `_mind_/` and a string from `--file path.txt` sit side by side in `args._values`. Commands access them uniformly through `args.get()` (probably). The command doesn't know or care whether a value came from a route param or a flag, or whether it was resolved.

**The `Ctx` is assembled at the end.** After params are resolved and flags are parsed, `build_ctx()` constructs `Paths` and returns `cmd.Ctx(args=args, paths=paths, ...)`. The resolver callback isn't stored in the context — it did its job during construction and is discarded.

## The full picture

I can now trace the entire resolver lifecycle:

1. **CLI startup:** `make_resolver(pkg_roots, paths)` discovers resolver files from core → project → user packages, loads them, and returns a single callback. (From `resolvers.py`)

2. **Route matching:** The router matches `hv become pulse` and captures `ParamCapture(value="pulse", resolver="mind")`. (From Luna's routing table journey)

3. **Context building:** `build_ctx()` iterates over captured params. For each one with a resolver, it creates `ResolveRequest(param="mind", resolver="mind", value="pulse")` and calls the callback. (From `args.py`)

4. **Resolver dispatch:** The callback (created by `make_resolver`) checks: is this explicit or implicit? Does the resolver exist? Is there a user context? Then calls `resolver_module.resolve(value, ctx)`. (From `resolvers.py`)

5. **Domain resolution:** The concrete resolver (`mind.py`) calls `resolve_mind("pulse", minds_dir, root)`, gets back a `Mind` object, runs `ensure_structure()`, returns the `Mind`. (From `resolvers/mind.py`)

6. **Context delivery:** The resolved `Mind` is stored in `args._values["mind"]` and the `Ctx` is returned. The command's `execute(ctx)` can now call `ctx.args.get("mind")` and receive a fully-resolved `Mind` object instead of the string `"pulse"`.

## What surprised me

Flags can have resolvers. The whole system is more general than "route params get resolved." Any value that enters the command — whether from the URL-like route path or from `--flag value` syntax — can be resolved through the same pipeline. The resolver system isn't bolted onto routing; it's a general-purpose value transformation layer that routing and flag parsing both use.

Also: the resolver callback is a closure, not an object. `make_resolver()` returns a function that closes over the loaded modules and context. Clean, simple, no class hierarchy. The whole resolver system has zero base classes.
