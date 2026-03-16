# Task Assignment

**Encourage thoughtful (and fun!) mind naming in `hv minds stage`**

When minds auto-name or when coordinators pick names, we're getting bland utility names like "fix1" — names that treat minds as disposable tools rather than emerging identities. These names stick around! A mind named "Balthazar" has character. A mind named "fix1" has a ticket number.

The `hv minds stage` command should nudge coordinators toward picking real names. Not enforce it — just make it clear that naming matters and is meant to be enjoyable.

**Location:** `worktrees/zephyr/`

---

## What to Change

The `--name` flag description and the stage command's help/output should communicate that:
- Names are identities, not labels — they persist across assignments
- Auto-generated names are fine, but choosing your own is encouraged
- Have fun with it! Steve, Luna, Wren, Ptolemy, Jinx — anything with personality
- Avoid purely functional names like "fix1", "test-runner", "worker-3"

Look at the stage command's `define()` for flag descriptions, and the output after staging for the "Next steps" messaging. Both are opportunities to add guidance.

---

## Requirements

- Update the `--name` flag description to convey that names are meaningful identities
- Add a brief note about naming in the post-stage output or help text
- Keep it light and concise — a sentence or two, not a lecture
- Don't break existing tests (or update them if messaging changes)

---

## Success Criteria

- `hv help --for minds.stage` shows updated `--name` description that encourages thoughtful naming
- The tone is warm and inviting, not prescriptive
- Tests pass

---

## Verification

```bash
cd worktrees/zephyr/haiv-core && uv run pytest
```

---

## Process

1. Read the stage command implementation
2. Update flag description and/or output messaging
3. Run tests, fix any that break due to changed strings

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
