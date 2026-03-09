# Task Assignment

**Implement Claude Code hook integration for mind status**

Build the pipeline that lets Claude Code lifecycle events flow into the TUI as live mind status. You've worked on this before — your prior planning notes are in `work/docs/prior-scratchpad.md`. Some of the file paths in those notes are out of date (the codebase went through a rename from mg to haiv, and haiv was renamed to haiv-lib). Use exploration to reconcile what you planned with where things actually live now.

**Location:** `worktrees/echo/`

---

## Context

We manage multiple minds working in parallel. Right now there's no way to see who's idle and needs attention vs who's actively working. Claude Code provides hooks that fire on lifecycle events (idle, working, waiting for approval, session start/end). We need to capture these and surface them in the TUI.

Spark's research is at `temp-aar/claude-hook-integration.md` — it has the full design. Luna's AAR on the existing haiv hook system is at `temp-aar/luna-haiv-hooks.md`.

---

## Success Criteria

- Claude Code hook events can be received and dispatched
- Mind status is visible in the TUI
- Existing IPC and TUI functionality isn't broken

---

## Before You Begin

1. Read the full assignment above.
2. Run `hv chart` and check the maps for anything relevant to your task.
3. **Decision point:** Does the Atlas have what you need to understand the codebase for this task?
   - **Yes** → Continue to step 4.
   - **No** → Propose an exploration to your human collaborator. What territory do you need to chart? This becomes a journey before you write code.
4. Discuss your approach with your human collaborator.

Use `TaskCreate` to track these steps — there may be significant work between them. The task description is a starting point — not a spec. Work collaboratively with your human. Do not use planning tools unless they explicitly request it.

> **IMPORTANT:** When you need to explore the codebase, follow the `hv chart` process. Do NOT read through code files without it. Exploration that follows the charting process builds the Atlas for future minds. Exploration that doesn't is wasted.
>
> Before starting your exploration, read the most recent journey in `atlas/journeys/` to see what the process looks like in practice. Then state the charting rules back to your human before you begin. If you can't articulate the rules, you haven't understood them yet.
