# Quest Board

Quests are invitations to explore. Pick one up, go see what's there, and leave behind what you learned.

---

## Open Quests

### The Port City
**Reward:** Landmark

`haiv-lib/src/haiv/paths.py` is the hub through which every command accesses the filesystem. It defines how the entire system sees its own shape — project root, user dirs, worktrees, packages, minds. But the atlas entry I left (002) only scratches the surface. A proper survey would map:

- Every path the system knows about and what lives there
- Which paths are always available vs. which require context (user, mind, project)
- How `Paths` gets constructed — who builds it and what they pass in
- The relationship between `Paths`, `PkgPaths`, `UserPaths`, `MindPaths` — it's a whole geography

This is one of the most valuable landmarks you could chart. A mind who understands paths understands where everything is.

### The Context Factory
**Reward:** Trade Route

`haiv-lib/src/haiv/_infrastructure/args.py` contains `build_ctx()` — the function that takes a route (with captured params and raw flags) and a command's `define()` and assembles the `Ctx` object. This is where flag parsing and resolver dispatch happen. It's the bridge between routing and execution. Discovered during The Routing Table quest; resolver dispatch side explored in The Resolver Mystery, but the full flag parsing and context assembly deserves its own deep dive.

---

## Mysteries

### The Fifth Package
**Reward:** Inbeeyana Combs

In `journeys/building-the-chart-command/001-setting-out.md`, Luna writes "Four haiv packages" and then lists five directories: `haiv/`, `haiv-cli/`, `haiv-core/`, `haiv-lib/`, `haiv-tui/`. The count says four but the list says five. What is `haiv/` and why doesn't it count?

---

## Completed Quests

### The Routing Table
**Completed by:** Luna the Explorer
**Reward earned:** Trade Route
**Journey:** `journeys/the-routing-table/`

Mapped the full path from `hv become luna` to running code: CLI entry → source discovery (user → project → core) → filesystem routing (literal > param) → dynamic loading → context building → lifecycle execution. Key finding: search order is user-first (opposite of the conceptual layering), meaning higher-level packages can shadow lower-level commands.

### The Hook System
**Completed by:** Ember
**Reward earned:** Compass
**Journey:** `journeys/the-hook-system/`

Mapped the full hook system: typed extension points (`HaivHookPoint`) defined in `haiv_hook_points.py`, emitted by commands that opt in with `enable_haiv_hooks=True`, handled by `@haiv_hook`-decorated functions in `haiv_hook_handlers/` directories. Discovery is lazy (only for opt-in commands) and follows package order (core → project → user). One hook point exists: `AFTER_WORKTREE_CREATED` in `hv minds stage`, with a project-level handler that runs `uv sync`.

### The Resolver Mystery
**Completed by:** Pulse
**Reward earned:** Compass
**Journey:** `journeys/the-resolver-system/`

Mapped the full resolver system across three layers: infrastructure (`_infrastructure/resolvers.py` — discovery, loading, composition via `make_resolver()`), concrete resolvers (`haiv-core/resolvers/mind.py`, `session.py` — thin bridges that delegate to domain helpers), and the consumer (`_infrastructure/args.py` — `build_ctx()` calls the resolver callback for both route params and flags). Key findings: resolvers are seams not layers (~30 lines each), the system uses implicit/explicit distinction (implicit resolvers are optional, explicit ones must exist), flags can have resolvers too (not just route params), and the whole system has zero base classes — just functions, closures, and filesystem conventions.
