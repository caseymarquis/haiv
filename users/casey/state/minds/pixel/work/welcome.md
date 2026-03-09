# Task Assignment

**Build `hv chart explore` — guided exploration startup command**

When a mind needs to explore the codebase, they currently get instructions in their welcome.md telling them to follow the `hv chart` process. But minds skip the narration, read files directly, and the Atlas doesn't grow. We need a command that actively walks them through starting an exploration properly.

`hv chart explore` should be the single entry point for beginning an exploration. It replaces paragraphs of instructions in welcome.md with one command to run.

**Location:** `worktrees/pixel/`

---

## Requirements

- New subcommand: `hv chart explore` (lives alongside existing `hv chart`)
- When run, it should:
  1. Show the charting rules
  2. Show the most recent journey as a concrete example of what good exploration looks like
  3. Prompt the mind to state the rules back (or otherwise verify understanding)
  4. Guide creation of `TaskCreate` tasks for the exploration plan
- Include a **hook point** so projects can customize the exploration process (e.g., inject project-specific priorities, required maps to check first, exploration checklists)
- The hook point should follow the existing pattern in `haiv-lib/src/haiv/haiv_hooks.py`

---

## Success Criteria

- Running `hv chart explore` produces a guided flow that a mind can follow to start a proper exploration
- The hook point allows project-level customization
- Tests cover routing, parsing, and basic execution

---

## Verification

```bash
cd worktrees/pixel
uv run pytest haiv-core/tests/ -k chart
```

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
