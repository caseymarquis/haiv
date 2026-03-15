# Task Assignment

**fix(minds stage): surface task vs welcome.md distinction**

The `hv minds stage` command has two audiences, but it doesn't explain this to the user. The `--task` and `--description` flags are management labels — they're what the *staging* mind sees when tracking delegations. The `welcome.md` file is what the *new* mind actually reads when it wakes up. Currently, users have to learn this distinction by trial and error.

**Location:** `worktrees/ember/`

---

## The Problem

A mind using `hv minds stage` naturally assumes `--task` and `--description` are the instructions for the new mind. They aren't — they're metadata for the coordinator. The actual instructions go in `welcome.md`, which the "Next steps" output mentions but doesn't explain *why* it matters or how it differs from the flags.

This has caused confusion in practice: managers write detailed `--description` flags thinking the new mind will see them, then write thin `welcome.md` files, leaving the new mind under-briefed.

## Requirements

- After staging, the command output should clearly explain:
  - `--task`/`--description` are labels for *you* (the staging mind) to track this delegation
  - `welcome.md` is what the *new mind* reads when it wakes — this is where the real assignment goes
- Keep it concise — a couple of lines in the output, not a wall of text
- Don't change the flags themselves, just improve the output guidance

---

## Success Criteria

- Running `hv minds stage` produces output that makes the two-audience distinction clear
- A mind seeing this output for the first time understands where to put the real assignment
- Existing tests pass

---

## Verification

```bash
cd worktrees/ember/haiv-core && uv run pytest
```

---

## Process

1. Find the `minds stage` command implementation
2. Update the "Next steps" output to explain the distinction
3. Run tests to verify nothing breaks

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
