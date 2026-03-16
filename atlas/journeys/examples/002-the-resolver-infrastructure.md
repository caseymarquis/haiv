# 002 — The Resolver Infrastructure

**File:** `haiv-lib/src/haiv/_infrastructure/resolvers.py`

## Why I came here

I wanted to see the machinery before the implementations. What contract do resolvers fulfill? How are they discovered and composed? This file should define all of that.

## What I found

It's 205 lines and every one of them is purposeful. The whole system is simpler than I expected.

**The contract is one function.** A resolver is a Python file in a `resolvers/` directory with a single function: `resolve(value: str, ctx: ResolverContext) -> Any`. That's it. No base class, no registration, no decorator. Just a function with a known signature in a file at a known location.

**Discovery mirrors commands.** `discover_resolvers()` scans `resolvers/` within a package root and maps filenames to paths: `mind.py` → `"mind"`, `session.py` → `"session"`. The filesystem *is* the namespace.

**Composition is layering.** `make_resolver()` takes a list of package roots and discovers resolvers from each, with later packages overriding earlier ones. Same precedence pattern as commands: last writer wins.

**The implicit/explicit distinction is the most interesting design choice.** When a route param is `_mind_/`, the param name and resolver name are the same — that's "implicit." When it's `_target_as_mind_/`, they differ — that's "explicit." The difference matters at resolution time: explicit resolvers *must* exist (or error), implicit resolvers are *optional* (raw string passes through if no resolver found). This means the system grows without breaking existing commands.

## What surprised me

The implicit/explicit distinction. I came in thinking resolvers were mandatory transformations. But the implicit case means most params are resolver-*capable* without requiring a resolver to exist. The filesystem naming convention (`_mind_/`) is doing double duty: it names the param AND optionally points at a resolver.

Also surprised by how much defensive engineering is here. Broken resolvers are skipped with warnings rather than crashing. Missing resolvers can silently pass through. The system is designed to degrade gracefully.

## Where to next?

**Decision:** `haiv-core/resolvers/mind.py`. I've seen the frame; now I want to see the picture inside it. The mind resolver is the one I can reason about most concretely — I *was* resolved by it when `hv become pulse` ran.
