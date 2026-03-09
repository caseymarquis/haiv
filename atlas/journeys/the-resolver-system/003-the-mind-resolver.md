# 003 — The Mind Resolver

**File:** `worktrees/main/haiv-core/src/haiv_core/resolvers/mind.py`

## Why I came here

I've seen the infrastructure — how resolvers are discovered, loaded, and composed. Now I want to see what a resolver actually *does*. The mind resolver is the most personal one: it's the code that ran when `hv become pulse` turned the string `"pulse"` into... me. Or at least, into the object that represents me.

## What I found

It's 39 lines. The resolver itself is almost nothing — a thin bridge between the resolver contract and an existing helper.

**The function:** `resolve(value, ctx) -> Mind` — exactly matching the contract from `resolvers.py`. Takes a string name and a `ResolverContext`, returns a `Mind` object.

**The real work is delegated.** The actual resolution happens in `resolve_mind(value, ctx.paths.user.minds_dir, ctx.paths.root)` from `haiv.helpers.minds`. The resolver is just a translator: it extracts the paths the helper needs from the `ResolverContext` and calls the helper. The resolver knows the *contract*, the helper knows the *domain*.

**Structure enforcement is a side effect of resolution.** After resolving the mind, it calls `mind.ensure_structure(fix=True)`, which checks the mind's directory structure and auto-fixes issues. This is interesting — resolution isn't just lookup, it's also maintenance. Every time a mind is resolved (every `hv become`, every `hv start <mind>`), its structure gets verified and repaired if needed. That's a clever place to put this — you'd want structural issues caught before the command runs, not during.

**Error handling is gentle.** If `ensure_structure` itself fails, it catches the exception and prints a warning to stderr rather than blocking. The philosophy from the infrastructure layer carries through: resolvers degrade gracefully. A mind with structural issues still resolves; you just get a warning.

**Two error cases from the helper:** `MindNotFoundError` if the mind doesn't exist, `DuplicateMindError` if there are duplicates. These propagate up — no catching here. Resolution failure is a hard stop; structural issues are a soft warning. That distinction makes sense: you can't proceed without a mind, but you can proceed with a slightly malformed one.

## What surprised me

How thin this file is. The resolver is a *seam*, not a *layer*. It translates between two systems (resolver infrastructure and mind helpers) without adding its own logic. The real intelligence is in `resolve_mind()` and `Mind.ensure_structure()`.

Also: `ctx.paths.user.minds_dir` — the resolver reaches into the user's directory structure to find minds. This confirms why the infrastructure requires `has_user=True`: no user means no minds directory means no way to resolve.

## Questions that emerged

- What does `Mind` look like? What fields does the resolved object carry? (This is Pixel's territory — their journey is about `ctx.mind`. I should note the connection but not duplicate their exploration.)
- What does `resolve_mind()` do internally? How does it search? What does "duplicate names" mean in practice?
- What does the session resolver look like? Is it the same thin-bridge pattern?
- How does `build_ctx()` take this resolved `Mind` and make it available as `ctx.mind`? That's the final link in the chain.

## Where to next?

Three candidates:

1. **`haiv-core/resolvers/session.py`** — The other concrete resolver. Quick read that would confirm whether the thin-bridge pattern holds. If both resolvers follow the same shape, that's a strong signal about the design intent.

2. **`_infrastructure/args.py`** — Where `build_ctx()` and `ResolveRequest` live. This is the *consumer* of resolvers — where the callback gets called and resolved values get placed into `Ctx`. I still don't know how `ResolveRequest` is shaped or when resolution happens during context assembly.

3. **`helpers/minds.py`** — Where `resolve_mind()` and the `Mind` class live. Deep domain territory. But Pixel's journey is specifically about `ctx.mind`, so I should leave this for them.

**Decision:** `haiv-core/resolvers/session.py`. Quick confirmation of the pattern, then I'll have both concrete resolvers mapped and can move to `args.py` for the consumer side. Seeing the session resolver will tell me if the thin-bridge pattern is a design principle or just how the mind resolver happened to be written.
