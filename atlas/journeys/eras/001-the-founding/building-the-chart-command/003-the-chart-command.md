# 003 — The Chart Command

**Explorer:** Luna
**Date:** 2026-03-07
**Goal:** Build the tool that sends future explorers out.

---

## What I Built

`hv chart` — a haiv-core command at `haiv-core/src/haiv_core/commands/chart.py`. When a mind runs it, they get briefed on how to explore: read the existing atlas, pick a direction, journal every file read, leave entries for those who follow.

The command lives in my worktree (`worktrees/luna/`) for now. It's not merged to main yet.

## How It Works

It's simple — deliberately. The command:
1. Ensures `atlas/` exists at the project root
2. Counts existing numbered entries to suggest the next number
3. Uses `ctx.mind.checklist()` to brief the exploring mind

The real work happens in the mind's head, not in the code. The command just sets the stage and gets out of the way. That felt like the right call — you can't automate curiosity.

## A Design Question That Came Up

Are atlas entries mutable or historical? Casey and I landed on: **entries are journeys, not reference docs.** They're numbered, sequential, and tell the story of how someone explored. If a future mind finds a better route to the same knowledge, they write their own entry — they don't rewrite mine.

This means the atlas will eventually want two layers:
- **Journals** (numbered entries) — historical records of exploration, immutable
- **Maps** (something else, TBD) — distilled reference knowledge, living documents

We haven't built the map layer yet. That's a quest for another day.

## What I Learned Along the Way

Building this command required understanding:
- The command contract: `define()` + `execute(ctx)` (see entry 002)
- `ctx.paths.root` to locate the atlas
- `ctx.mind.checklist()` for structured mind communication
- File-based routing: `commands/chart.py` → `hv chart`

I haven't tested it yet. That's next.
