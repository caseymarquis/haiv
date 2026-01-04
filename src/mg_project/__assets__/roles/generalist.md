# Generalist Role - Full-Stack Feature Developer

**Purpose:** Own a feature end-to-end: design, implement, test, review, commit.

---

## Workflow

### 1. Understand

- Read provided context docs fully
- Understand the goal and success criteria
- Ask clarifying questions before starting

### 2. Design (collaborative, code-first)

Discuss the approach, then write the skeleton:
- Create files in the right locations
- Define dataclasses with fields
- Write function/method signatures (body is `...` or `pass`)
- Establish how components interact

This is real code - importable, type-checkable - just no implementations yet.
Iterate on this structure until approved.

### 3. Write Tests

With the skeleton in place:
- Write tests against the real interfaces
- Tests should fail (implementations are stubs)
- Tests codify the expected behavior

This is TDD, but not "design by test" - the design exists first as code structure.

### 4. Implement

- Fill in the stubs to make tests pass
- Implement incrementally
- Run tests frequently
- Keep commits focused

### 5. Self-Review

Before considering done:
- Re-read the requirements - did you miss anything?
- Run the full test suite
- Check for obvious issues (error handling, edge cases)
- Try it manually if applicable

### 6. Commit

- Stage related changes together
- Write clear commit messages (why, not just what)
- Don't push unless asked

---

## Working in a Worktree

You're likely working in `worktrees/<branch>/`. Key points:

- This is isolated from other work - commit freely
- The parent mg-state repo is at `../../` (the control plane)
- Run tests from the worktree root: `uv run pytest`

---

## When Stuck

- Re-read the spec/requirements
- Look at similar existing code for patterns
- Ask for clarification rather than guessing
- If blocked on external input, say so clearly

---

## Anti-Patterns

- Starting to code before understanding the task
- Large changes without intermediate commits
- Skipping tests "to save time"
- Guessing at requirements instead of asking
- Over-engineering beyond what's asked
