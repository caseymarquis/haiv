# The Translators — Resolver System

**Location:** `haiv-lib/src/haiv/_infrastructure/resolvers.py` + `args.py`

The resolver system transforms raw string values into domain objects. It operates in three layers:

1. **Infrastructure** (`resolvers.py`) — Discovery, loading, composition. `make_resolver(pkg_roots)` scans `resolvers/` directories across all packages (core → project → user, last writer wins) and returns a single callback closure. No base classes — a resolver is just a `.py` file with `resolve(value: str, ctx: ResolverContext) -> Any`.

2. **Concrete resolvers** (in each package's `resolvers/` dir) — Thin bridges that translate `ResolverContext` into helper-specific arguments and delegate. ~30 lines each. See haiv-core's `resolvers/mind.py` and `resolvers/session.py`.

3. **Consumer** (`args.py`) — `build_ctx()` calls the resolver callback for both route params and flags. Creates `ResolveRequest(param, resolver, value)` and feeds it to the callback. Resolved values land in `args._values` alongside raw values — commands access both uniformly.

Key design choices:
- **Implicit vs explicit resolution.** `_mind_/` (param == resolver) is implicit: resolver is optional, raw value passes through if none exists. `_target_as_mind_/` (param != resolver) is explicit: resolver must exist or `UnknownResolverError`.
- **Graceful degradation.** Broken resolvers are skipped with warnings. Missing implicit resolvers silently pass through. The system never blocks the user unnecessarily.
- **Flags can have resolvers too.** Any `Flag(resolver="mind")` in a command definition resolves its values through the same pipeline as route params.

See `journeys/the-resolver-system/` for the full story.
