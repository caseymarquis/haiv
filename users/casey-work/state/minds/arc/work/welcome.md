# Task Assignment

**Design and implement autonomous mode for haiv minds**

You're taking on a feature that touches several parts of haiv: staging, sessions, pop, and the mind launch experience. The goal is to support minds that run unsupervised alongside the current collaborative model.

**Location:** `worktrees/arc/`

---

## The Three Problems

### 1. Autonomous Launch Mode
Currently, minds are staged for collaborative work — a human is present, edits require approval, and templates encourage discussion. We need an **autonomous mode** where:
- The mind launches with edits enabled (no human approval needed)
- A separate welcome/task template encourages autonomous decision-making over collaboration
- The staging command (`hv minds stage`) needs a flag or option to select this mode

### 2. Optional Worktrees
Some tasks don't need their own worktree (e.g. research, triage, coordination work like what rove does). Currently staging always creates a worktree. We need:
- A way to stage a mind without creating a worktree
- The `pop` command needs to handle worktree-less minds gracefully
- Think about what "location" means for a mind without a worktree — they work on haiv-hq directly? Or somewhere else?

### 3. Session Metadata & Mode-Aware Tooling
The session needs to carry metadata about its mode (autonomous vs collaborative, has-worktree vs not) so that **all tools can adapt**. For example:
- `hv pop` should behave differently for autonomous minds (auto-merge? different AAR process?)
- Other commands that assume a worktree exists need to handle the no-worktree case
- This metadata should live in the session tracking system (sessions.toml or similar)

---

## Requirements

- Design the session metadata schema that supports these modes
- Modify `hv minds stage` to support autonomous and no-worktree options
- Create an autonomous-mode welcome template
- Update `hv pop` to handle all mode combinations
- Ensure other commands degrade gracefully when there's no worktree

---

## Success Criteria

- A mind can be staged and launched in autonomous mode with a single command
- A mind can be staged without a worktree
- Session metadata correctly tracks mode, and tools adapt accordingly
- Existing collaborative workflow is unchanged (autonomous is opt-in)

---

## Process

1. Start by exploring the current staging, session, and pop code to understand the architecture
2. Design the session metadata schema and propose it to your human collaborator
3. Plan the implementation across all affected commands
4. Delegate implementation work to sub-minds if the scope warrants it
5. Integrate and test

---

## Before You Begin

1. Read the full assignment above.
2. Run `hv chart` and check the maps for anything relevant to your task.
3. **Decision point:** Does the Atlas have what you need to understand the codebase for this task?
   - **Yes** → Continue to step 4.
   - **No** → Propose an exploration to your human collaborator. What territory do you need to chart? This becomes a journey before you write code.
4. Discuss your approach with your human collaborator.

Use `TaskCreate` to track these steps — there may be significant work between them. The task description is a starting point — not a spec. Work collaboratively with your human. Do not use planning tools unless they explicitly request it.

> **IMPORTANT:** When you need to understand the codebase, start with `hv chart` to check what's already mapped. If the Atlas doesn't have enough information, use `hv chart explore` — it will guide you through the exploration process. Do NOT read through code files without it. Exploration that follows the charting process builds the Atlas for future minds. Exploration that doesn't is wasted.
