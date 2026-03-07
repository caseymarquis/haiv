# Task Assignment

**Mind-level launch settings — `settings.toml`**

Add an optional `settings.toml` file to mind directories that configures how the mind launches. The first setting to implement is `launch.system_prompt`, which controls the Claude Code system prompt behavior for that mind.

**Location:** `worktrees/spark/`

---

## Context

Different minds have different roles. A COO (strategic, ideas, delegation) doesn't need the full Claude Code software engineering system prompt — it takes up context and encourages behaviors that aren't relevant. A code worker needs the full toolkit.

We want minds to be able to opt into a different launch experience through a settings file in their home directory.

## What Exists

- Minds live at `users/{user}/state/minds/{mind}/`
- `hv start {mind}` launches a mind (see `haiv-core` commands)
- `hv become {mind}` loads context for an existing session
- There's already project-level settings infrastructure (`haiv.toml`, `ctx.settings`)
- `references.toml` already exists as a per-mind config file

## The Setting

```toml
# minds/{mind}/settings.toml

[launch]
system_prompt = "minimal"   # or "full" (default)
```

The details of what "minimal" means and how it integrates with Claude Code's launch flags are for you and Casey to figure out together. This is a new area — discuss the approach before building.

---

## Success Criteria

- `settings.toml` is loaded during mind launch
- `launch.system_prompt` setting is respected
- Minds without a `settings.toml` get the current default behavior
- Clean integration with existing `hv start` / launch infrastructure

---

## Before You Begin

Read the full assignment, then discuss your understanding and approach with your human collaborator before writing code. The task description is a starting point — not a spec. Do not use planning tools unless your human explicitly requests it. You work best together.
