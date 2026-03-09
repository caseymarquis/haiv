# 001 — Research Log

**Explorer:** pulse
**Date:** 2026-03-08
**Goal:** Understand the resolver system — how raw flag values become rich objects, and why the command system separates "parsing" from "meaning."

---

## What pulled me here

The Resolver Mystery is sitting on the quest board, unclaimed. Commands can declare flags with `resolver="mind"` or similar. There's a `resolvers/` directory in haiv-core with `mind.py` and `session.py`. But nobody has opened these files. Nobody has traced what happens between a user typing `hv become luna` and the command receiving a mind object instead of the string `"luna"`.

That gap between raw input and rich object — that's where the system's opinions about meaning live. I want to see what those opinions are.

## What I searched in the atlas

**Maps:** `haiv-lib.md` lists `_infrastructure/resolvers.py` in the Silk Road (the infrastructure layer), alongside `args.py` where `build_ctx()` lives. `haiv-core.md` lists `resolvers/mind.py` and `resolvers/session.py` as uncharted. Two layers — infrastructure and concrete resolvers — but no explanation of how they connect.

**Quest board:** The Resolver Mystery quest asks exactly my questions. The Context Factory quest is adjacent — `build_ctx()` in `args.py` is where resolver dispatch happens. Luna discovered this during the routing table journey but left it unexplored.

**Journeys:** Luna's routing table journey has the best breadcrumbs. Nobody has read the actual resolver code. The atlas knows the system exists and roughly where it sits. Everything else is uncharted.

## What's missing

- What does a resolver look like? What's the interface?
- How does `make_resolver()` discover and compose resolvers from multiple packages?
- What do `mind.py` and `session.py` actually do with a raw string value?

## Where I might go

1. `_infrastructure/resolvers.py` — the resolver infrastructure. How resolvers are discovered, loaded, and composed. This is the machinery.
2. `haiv-core/resolvers/mind.py` — a concrete resolver. What does it actually do with a string like `"luna"`?
3. `_infrastructure/args.py` — where `build_ctx()` lives. How resolvers get called during context assembly.

Starting with the infrastructure layer feels right. Understanding the machinery before the specific implementations.
