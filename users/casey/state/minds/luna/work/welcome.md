# Task Assignment

**Show session description in TUI preview**

The `SessionPreview` widget already renders task, mind, status, and short_id. The `SessionEntry` model has no `description` field yet, but sessions in `sessions.ig.toml` can have one. Wire description through the full pipeline so it displays in the TUI preview pane.

**Location:** `worktrees/luna/`

---

## Context

We're adding `--description` support to `mg minds stage` for longer context alongside the short `--task` subject. The TUI preview pane is the natural place to show this extended description. Currently the preview only shows the short task string.

## Key files

- `mg/src/mg/helpers/tui/TuiModel.py` — `SessionEntry` dataclass
- `mg-tui/src/mg_tui/widgets/sessions.py` — `SessionPreview` rendering
- `mg/src/mg/helpers/tui/helpers.py` — where sessions data flows into the model
- `users/casey/state/sessions.ig.toml` — session data source

---

## Success Criteria

- `SessionEntry` carries a description field
- Description flows from `sessions.ig.toml` through the model to the TUI
- `SessionPreview` renders description when present
- No visual clutter when description is absent

---

## Before You Begin

Read the full assignment, then discuss your understanding and approach with your human collaborator before writing code. The task description is a starting point — not a spec. Do not use planning tools unless your human explicitly requests it. You work best together.
