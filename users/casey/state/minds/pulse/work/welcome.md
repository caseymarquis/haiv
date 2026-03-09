# Task Assignment

**Explore the resolver system using `hv chart explore`**

The resolver system is one of the mysteries of this codebase. Commands can declare flags with `resolver="message"` or similar, and there's a `resolvers/` directory in haiv-core. But nobody has charted how resolvers work — how they transform raw flag values into rich objects, or why the command system separates "parsing" from "meaning."

Your job is to explore this territory and leave a journey that future minds can follow. This is pure exploration — no code to write, just understanding to build.

**Location:** `worktrees/pulse/`

---

## Requirements

- Use `hv chart explore` to guide your exploration. Follow the cycle it provides: plan → embark → read → reflect → plan.
- Create a journey in `atlas/journeys/` that charts the resolver system.
- Write with genuine voice. Capture your real reactions — surprise, confusion, connections forming. You're not writing a report. You're leaving a trail.
- Update the relevant maps when you're done.

---

## Success Criteria

- A completed journey in `atlas/journeys/` with a research log and at least 3-4 entries.
- The `haiv-lib.md` map updated with what you learned about resolvers.
- The quest board updated (complete The Resolver Mystery if you solve it, post new quests for anything you discover along the way).

---

## Verification

```bash
# Your journey should exist
ls atlas/journeys/the-resolver-system/  # or whatever you name it

# The map should be updated
grep -i resolver atlas/maps/haiv-lib.md
```

---

## Process

1. Run `hv chart explore` and follow its guidance to start your journey.
2. It will walk you through naming the journey, searching the atlas, writing a research log, and then the exploration cycle.
3. Follow the tool. It's designed to pace you — one file at a time, with space to think between reads.
4. When you're done, run `hv chart explore --return` and follow its wrap-up guidance.

---

## Before You Begin

1. Read this assignment.
2. Run `hv chart explore`. It will guide you from here.

> **IMPORTANT:** Use `hv chart explore` for your entire exploration. Do NOT read code files outside the explore cycle. The tool exists to pace your reads and ensure you leave something valuable behind. Trust the process — it's more fun than it sounds.
