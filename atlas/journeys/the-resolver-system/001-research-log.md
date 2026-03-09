# 001 — Research Log

**Explorer:** pulse
**Date:** 2026-03-08
**Goal:** Understand the resolver system — how raw flag values become rich objects, and why the command system separates "parsing" from "meaning."

> *Post-journey note:* "Raw flag values" undersold it. Resolvers transform both route params (`_mind_/` captures) *and* flag values (`--target wren`). The system is more general than I expected going in.

---

## What pulled me here

The Resolver Mystery is sitting on the quest board, unclaimed. Commands can declare flags with `resolver="mind"` or similar. There's a `resolvers/` directory in haiv-core with `mind.py` and `session.py`. But nobody has opened these files. Nobody has traced what happens between a user typing `hv become luna` and the command receiving a mind object instead of the string `"luna"`.

That gap between raw input and rich object — that's where the system's opinions about meaning live. I want to see what those opinions are.

## What I searched in the atlas

**Maps:** `haiv-lib.md` lists `_infrastructure/resolvers.py` in the Silk Road (the infrastructure layer), alongside `args.py` where `build_ctx()` lives. `haiv-core.md` lists `resolvers/mind.py` and `resolvers/session.py` as uncharted. Two layers — infrastructure and concrete resolvers — but no explanation of how they connect.

**Quest board:** The Resolver Mystery quest asks exactly my questions. The Context Factory quest is adjacent — `build_ctx()` in `args.py` is where resolver dispatch happens. Luna discovered this during the routing table journey but left it unexplored.

**Journeys:** Luna's routing table journey has the best breadcrumbs:
- Param capture in `routing.py` assigns resolver names: `_mind_/` → `resolver="mind"`, `_target_as_mind_/` → `param="target", resolver="mind"` (the naming convention separates param name from resolver type)
- Before building context, the CLI calls `make_resolver(pkg_roots)` to build a single resolver callback from all package levels (core → project → user)
- The resolver system, like commands, supports overriding at each level

Nobody has read the actual resolver code. The atlas knows the system exists and roughly where it sits. Everything else is uncharted.

## What's missing

- What does a resolver look like? What's the interface?
- How does `make_resolver()` discover and compose resolvers from multiple packages?
- What do `mind.py` and `session.py` actually do with a raw string value?
- How does `build_ctx()` call resolvers during context assembly?
- Are there resolvers beyond mind and session?

## Where I might go

1. `_infrastructure/resolvers.py` — the resolver infrastructure. How resolvers are discovered, loaded, and composed. This is the machinery.
2. `haiv-core/resolvers/mind.py` — a concrete resolver. What does it actually do with a string like `"luna"`?
3. `haiv-core/resolvers/session.py` — the other resolver. Same question.
4. `_infrastructure/args.py` — where `build_ctx()` lives. How resolvers get called during context assembly.
5. Back to `routing.py` briefly — how `ParamCapture` carries resolver names forward.

Starting with the infrastructure layer feels right. Understanding the machinery before the specific implementations.

## Where to next?

Three candidates:

1. **`_infrastructure/resolvers.py`** — The resolver infrastructure layer. This is where `make_resolver()` lives (according to Luna's journey). If I understand how resolvers are discovered and composed, I'll have the frame for everything else. But infrastructure code can be abstract — hard to understand without seeing a concrete example first.

2. **`haiv-core/resolvers/mind.py`** — A concrete resolver. I could start bottom-up: see what a resolver actually *does*, then understand the machinery that calls it. The mind resolver is probably the most-used one (every `hv become <mind>` and `hv start <mind>` must go through it). But without knowing the interface, I might miss what I'm looking at.

3. **`_infrastructure/args.py`** — The context factory. Where resolvers get *called*. This is the consumer side. Seeing how resolvers are invoked might clarify what they need to provide. But this file does many things (flag parsing, context building) and the resolver call might be buried.

**Decision:** `_infrastructure/resolvers.py`. Top-down. The infrastructure defines the contract that concrete resolvers must fulfill. Once I see that contract, the implementations will make sense immediately. And if the file is small (infrastructure for just two resolvers can't be that complex), I'll get the full picture fast.
