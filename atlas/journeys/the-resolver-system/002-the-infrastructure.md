# 002 — The Resolver Infrastructure

**File:** `worktrees/main/haiv-lib/src/haiv/_infrastructure/resolvers.py`

## Why I came here

I wanted to see the machinery before the implementations. What contract do resolvers fulfill? How are they discovered and composed? This file should define all of that.

## What I found

It's 205 lines and every one of them is purposeful. The whole system is simpler than I expected.

**The contract is one function.** A resolver is a Python file in a `resolvers/` directory with a single function: `resolve(value: str, ctx: ResolverContext) -> Any`. That's it. No base class, no registration, no decorator. Just a function with a known signature in a file at a known location. The docstring even shows an example — `mind.py` converts a string to a `Mind` object.

**Discovery mirrors commands.** `discover_resolvers()` scans `resolvers/` within a package root and maps filenames to paths: `mind.py` → `"mind"`, `session.py` → `"session"`. Files starting with underscore are skipped (probably `__init__.py`). This is the same convention as command routing — the filesystem *is* the namespace.

**Composition is layering.** `make_resolver()` takes a list of package roots and discovers resolvers from each, with later packages overriding earlier ones. So if haiv-core defines `resolvers/mind.py` and haiv-user also defines `resolvers/mind.py`, the user's version wins. Same precedence pattern as commands. The whole multi-package architecture has one answer: last writer wins.

**The implicit/explicit distinction is the most interesting design choice.** When a route param is `_mind_/`, the param name and resolver name are the same (`param="mind", resolver="mind"`) — that's "implicit." When it's `_target_as_mind_/`, they differ (`param="target", resolver="mind"`) — that's "explicit." The difference matters at resolution time:
- **Explicit:** The resolver *must* exist. If it doesn't, `UnknownResolverError`.
- **Implicit:** The resolver is *optional*. If it doesn't exist, the raw string passes through unchanged.

This is clever. It means a command can use `_name_/` as a param and it'll just work as a string — no resolver needed. But if someone later creates a `resolvers/name.py`, it'll automatically start transforming those values. The system grows without breaking existing commands.

**User context is a gate.** If a resolver exists but there's no user context (`has_user=False`), the system raises `UserRequiredError` rather than trying to resolve. This makes sense — mind and session resolvers need to look up state in user directories, so they can't work without a user identity.

**`ResolverContext` is minimal.** Just `paths` (the Paths object) and an optional `container` (dependency injection, typed as `Any` to avoid circular imports). Resolvers get enough to find things on disk but not access to the full command context.

## What surprised me

The implicit/explicit distinction. I came in thinking resolvers were mandatory transformations — you declare `resolver="mind"` and the string always gets resolved. But the implicit case means most params are resolver-*capable* without requiring a resolver to exist. The filesystem naming convention (`_mind_/`) is doing double duty: it names the param AND optionally points at a resolver. Only the explicit form (`_target_as_mind_/`) demands the resolver exist.

Also surprised by how much defensive engineering is here. Broken resolvers are skipped with warnings rather than crashing. Missing resolvers can silently pass through. The system is designed to degrade gracefully. Someone was thinking about what happens when things go wrong, not just when they go right.

## Questions that emerged

- What does `ResolveRequest` look like? It's imported from `args.py` — I need to see its shape to understand the full handoff.
- How does `build_ctx()` call this resolver callback? When in the context-building process do params get resolved?
- What do the actual resolvers do? The infrastructure is clean, but I still don't know what `Mind` looks like or how a session gets resolved.

## Where to next?

Three options:

1. **`haiv-core/resolvers/mind.py`** — The most-used concrete resolver. Now that I know the contract (`resolve(value, ctx) -> Any`), I can see exactly what it does with a mind name. This completes the "what" — infrastructure told me "how," this tells me "to what end."

2. **`_infrastructure/args.py`** — Where `build_ctx()` and `ResolveRequest` live. This would show me the calling side — how the resolver callback gets invoked during context assembly. But `args.py` is likely large and does many things; I might get lost in flag parsing when I just want the resolver call.

3. **`haiv-core/resolvers/session.py`** — The other resolver. Probably similar pattern to mind but for session objects. Less urgent — seeing one concrete resolver should reveal the pattern.

**Decision:** `haiv-core/resolvers/mind.py`. I've seen the frame; now I want to see the picture inside it. The mind resolver is the one I can reason about most concretely — I *was* resolved by it when `hv become pulse` ran. Every mind that wakes up passed through this code.
