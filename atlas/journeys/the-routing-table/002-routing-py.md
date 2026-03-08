# 002 — routing.py

**Explorer:** Luna the Explorer
**Date:** 2026-03-07

---

## Why I Came Here

This is the core of the routing system — `haiv-lib/src/haiv/_infrastructure/routing.py`. The quest says to map how `hv become luna` goes from typed text to running code. This file is the first half: turning text into a file path.

## What I Found

The routing algorithm works in layers:

### 1. Input parsing
`find_route_in_paths()` takes a command string like `"become luna --verbose"` and splits it:
- Route parts: `["become", "luna"]`
- Raw flags: `["--verbose"]` (everything from first `--` onward)

### 2. Path tree
All `.py` files under `commands/` are collected and built into a tree (nested dict). So `become/_mind_.py` becomes `{"become": {"_mind_.py": {"_file_": Path(...)}}}`.

### 3. Recursive matching (`_find_matches`)
This is the heart. It walks the tree and the route parts in parallel:
- **Literal match** wins first: `become` matches the directory `become/`
- **Param capture** is fallback: `luna` doesn't match any literal, so `_mind_/` or `_mind_.py` captures it as `ParamCapture(value="luna", resolver="mind")`
- **`_rest_.py`** consumes all remaining parts
- **`_index_.py`** is the default when a directory matches but nothing deeper does

### 4. Precedence
- Literal > param at every level (not globally)
- If a literal path leads somewhere, params aren't even tried
- Multiple param matches at the same level = `AmbiguousRouteError`

### 5. Param naming convention
- `_mind_/` → param="mind", resolver="mind" (implicit — name IS the resolver)
- `_target_as_mind_/` → param="target", resolver="mind" (explicit — different name, specific resolver)

### The key insight
The filesystem *is* the router. There's no route table, no config, no registration. You make a file, it becomes a command. The tree structure encodes both the command grammar AND the parameter types. This is why CLAUDE.md says "literals take precedence over params at each level" — it's baked into the algorithm.

## What I Don't Know Yet

I've seen how text becomes a file path + captured params. I haven't seen:
- How the file gets loaded and its `define()`/`execute()` called — that's `loader.py`
- How the captured params (with resolver names) get turned into real objects — that's the resolver system
- Who calls `find_route()` in the first place — that's the CLI entry point

## Where I'm Going Next

`loader.py` — the second half of the journey. How does a matched file become a running command?
