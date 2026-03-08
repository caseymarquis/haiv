# 002 — The Template Pipeline

**Came from:** 001 research log — needed to understand how minds get created and what templates they receive.

## What I found

### The staging command (`haiv-core/commands/minds/stage.py`)

`hv minds stage --task "..."` does:
1. Picks or creates a mind name
2. Determines base branch
3. Creates a git worktree at `worktrees/{name}/`
4. Calls `scaffold_mind()` to build the mind's directory structure
5. Creates a session with status "staged"
6. Prints next steps telling the creator to edit `work/welcome.md`, assign a role, then `hv start`

### scaffold_mind (`haiv-lib/helpers/minds.py`)

Creates the directory structure and writes template files:
- `work/welcome.md` — from `minds/welcome.md.j2` template
- `references.toml` — from `minds/references.toml.j2` template
- `work/immediate-plan.md` — static one-liner `"# Immediate Plan\n"`
- `work/long-term-vision.md` — static one-liner
- `work/my-process.md` — static one-liner
- `work/scratchpad.md` — static one-liner

Key: templates come from `__assets__/minds/` in haiv-core. The `ctx.templates` renderer finds them via the package resolution order.

### The welcome template (`__assets__/minds/welcome.md.j2`)

This is the main template the *creator* fills in for the new mind. It has placeholder sections:
- Task title and description
- Location (if worktree, rendered by Jinja)
- Requirements
- Success Criteria
- Verification commands
- Process steps
- **"Before You Begin"** section — tells the mind to discuss with human before coding

### The references template (`__assets__/minds/references.toml.j2`)

Just a comment with an example. The creator adds role references here (e.g., path to `roles/generalist.md`).

## What this means for atlas integration

The welcome template's "Process" section and "Before You Begin" section are where atlas integration would land. Currently "Before You Begin" says "discuss your understanding and approach with your human collaborator before writing code."

The simplest change: add an instruction to run `hv chart` before beginning work. This goes in the template that every mind receives, so it becomes universal.

The static one-liners (immediate-plan, scratchpad, etc.) are just headers — they're for the mind to fill in later. Not relevant to atlas integration.

## Where to next

I've found the template. Now I need to decide exactly what to change. The welcome template is filled in by the *creator* (the PM or COO), not by the mind itself. So the "Before You Begin" section at the bottom — which speaks directly to the new mind — is the right place. That's the only part the mind reads as instruction rather than assignment.
