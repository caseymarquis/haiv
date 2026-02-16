# Task Assignment

**Enforce short task descriptions in `mg minds stage`**

The `--task` flag on `mg minds stage` should behave like a git commit subject line — short, conventional-commit style. The `--description` flag already exists for longer explanations.

**Location:** `worktrees/pixel/`

---

## Context

Task descriptions show up in `mg sessions` output and the TUI sidebar. Long descriptions break formatting and are hard to scan. We want the same discipline as git commit messages: short subject, optional body.

The flags already exist (`--task` for short, `--description` for long). What's missing is guidance and/or validation to keep `--task` concise.

## What to consider

- Git default subject line limit (50 chars recommended, 72 hard limit)
- Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.) — encourage but don't enforce
- Should this be a warning or a hard rejection if too long?
- Where does this guidance surface — in the prompt, in help text, in validation?

---

## Success Criteria

- `--task` values are encouraged/enforced to stay short
- Longer context goes in `--description`
- Existing workflows aren't broken

---

## Before You Begin

Read the full assignment, then discuss your understanding and approach with your human collaborator before writing code. The task description is a starting point — not a spec. Do not use planning tools unless your human explicitly requests it. You work best together.
