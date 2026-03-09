# 002 — How Commands Work

**Explorer:** Luna
**Date:** 2026-03-07
**Goal:** Understand the command pattern well enough to build `hv chart`.

---

## The Package Split

I initially looked in `worktrees/main/haiv/` for `cmd.py` and found only `haiv_meta`. The actual foundation lives in **haiv-lib** — that's where `haiv.cmd`, `haiv.paths`, `haiv.errors`, `haiv.helpers`, and all the infrastructure lives. The `haiv` package at `worktrees/main/haiv/` is just metadata.

This matters: if you're looking for *how haiv works*, go to `haiv-lib/src/haiv/`. If you're looking for *what commands exist*, go to `haiv-core/src/haiv_core/commands/`.

## The Command Contract

A command file needs two functions:

**`define() -> cmd.Def`** — Declares the command's description and flags. This is metadata — it gets read by `hv help` without executing anything.

**`execute(ctx: cmd.Ctx) -> None`** — Does the work. Receives a context object with:
- `ctx.args` — parsed flags/arguments (`.has()`, `.get_one()`, `.get_list()`)
- `ctx.paths` — filesystem paths (project root, user dir, etc.) — defined in `haiv/paths.py`
- `ctx.print()` — output to the mind/human
- `ctx.mind` — structured communication patterns (like `.checklist()` for giving minds task lists)
- `ctx.templates` — Jinja2 template rendering from the current package's `__assets__/`
- `ctx.git` — Git wrapper
- `ctx.settings` — project settings

## File-Based Routing

The filename/directory structure *is* the command path:
- `commands/help.py` → `hv help`
- `commands/become/_mind_.py` → `hv become <mind>` (param capture via `_name_` dirs)
- `commands/minds/stage.py` → `hv minds stage`

So for `hv chart`, I need `commands/chart.py` (or `commands/chart/` if subcommands come later).

## Paths (`haiv-lib/src/haiv/paths.py`)

`ctx.paths` gives you the filesystem layout. The key one for me: **`ctx.paths.root`** is the haiv project root (the haiv-hq directory). So the atlas would live at `ctx.paths.root / "atlas"`.

There's no `atlas_dir` property yet — I'd need to either add one to `Paths` or just construct it in my command. For now, constructing it is simpler and avoids touching foundational code for an experiment.

Notable paths hierarchy:
- `ctx.paths.root` — haiv-hq root
- `ctx.paths.worktrees_dir` — `worktrees/`
- `ctx.paths.user` — `UserPaths` with `.minds_dir`, `.state_dir`, etc.
- `ctx.paths.pkgs` — package paths for command/resolver discovery

## Ready to Build

I now know:
1. A command needs `define()` and `execute(ctx)` in the right file location
2. `ctx.paths.root` gets me to haiv-hq where `atlas/` lives
3. `ctx.print()` for output, `ctx.mind.checklist()` for structured mind instructions
4. File at `commands/chart.py` → `hv chart`

Next step: actually write the command.
