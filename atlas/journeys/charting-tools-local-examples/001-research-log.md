# 001 — Research Log

**Explorer:** nova
**Date:** 2026-03-12
**Goal:** Understand how hv chart references example journeys, change it to use project-local examples

---

## What pulled me here

My assignment says `hv chart` currently references example journeys from a bundled location. Each project should have its own example journey folder instead. I need to find where that reference happens, understand the surrounding architecture, and reroute it.

Running `hv chart explore` to start this journey gave me an immediate taste of the problem — it pointed me to example files deep inside `__assets__/chart/example-journey/` in the haiv-core package. That's the bundled asset path, not something a project author would know to look at or customize.

## What I searched in the atlas

**Maps:** `haiv-core.md` lists `chart.py` as a single file in the commands directory. But the quest board says it's now a directory with subcommands — so the map is stale. `haiv-lib.md` describes `paths.py` as "The Port City" — the hub for all path resolution. It mentions `AtlasPaths` was added but doesn't detail its properties.

**Quest board:** "The Charting Tools" quest is directly relevant. It calls out that `hv chart` is now a directory with subcommands, mentions `hv chart explore`, `AtlasPaths` additions to `paths.py`, and templates in `__assets__/chart/` including "the bundled example journey." This quest was waiting for someone.

**Journeys:** No journey covers the chart command. The resolver system journey (`the-resolver-system/`) is the most recent and — interestingly — its files are the ones used as the bundled example in `__assets__/chart/example-journey/`.

## What's missing

- How does `hv chart explore` actually find and reference the example journey? The quest board says one exists but not how it's wired up.
- What does `AtlasPaths` look like? The map says it was added to `paths.py` but doesn't list its properties. I need to know if there's already a concept of an examples directory, or if I need to add one.
- Is the example reference only in `explore.py`, or does `_index_.py` also use it?

## Where I might go

1. **`explore.py`** — The `hv chart explore` subcommand. The quest board says this manages exploration state. The example journey reference almost certainly lives here, since it's the guided exploration tool. This is the most direct path.

2. **`_index_.py`** — The bare `hv chart` command. Quick check to see if it also references examples. The output I saw from running `hv chart` earlier didn't mention examples, so this may be a dead end — but worth confirming.

3. **`paths.py` (AtlasPaths)** — The path structure for the atlas. Need to understand what paths exist before I can decide where project-local examples should live.

4. **`explore-start.md.j2`** — The template that renders the "starting an exploration" message. The example path gets displayed to the user through a template, so I need to see how it's consumed.

Starting with `explore.py` — that's where the action is.
