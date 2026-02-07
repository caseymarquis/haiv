# Immediate Plan

**Updated:** 2026-02-07

---

## Current Focus: Session-Aware Delegation

Redesigning `mg minds stage` and `mg start` so that sessions track the full delegation lifecycle. The TUI reflects state changes in real time via TuiClient.

---

## Design Decisions (agreed with Casey)

### Session as assignment tracker
- Sessions track assignments, not Claude conversations
- One active session per mind (staged or started)
- Old sessions get archived when replaced
- Mind status is inferred from session state — no separate mind status field

### Session data model changes
- Add `status`: staged / started (archived for old sessions)
- Add `parent`: mg session ID of whoever staged this (null = human root)
- Add `description`: long-form body (task is the short title)
- Add `claude_session_id`: current Claude session ID (decoupled from mg session `id`)
- Add `old_claude_session_ids`: history of previous Claude session IDs
- `task` stays as short summary (commit title convention)

### `mg minds stage` changes
- Add `--task` flag (required — the delegation intent)
- Add `--description` flag (optional — long-form body)
- Create session with `status=staged`, `parent=MG_SESSION` env var
- Archive any existing active session for that mind
- Write to disk + `ctx.tui.write()` to update TUI live
- Keep `--worktree`/`--no-worktree` as-is (orthogonal concern)

### `mg start <mind>` changes
- Remove `--tmux` flag (deprecated, fully committed to WezTerm)
- Remove `--tui` flag (TUI is always running, default behavior)
- Keep `--task` for quick-start without staging
- Remove `--resume` (resuming native Claude sessions is opt-in special case only)
- Flow:
  - Session exists for mind → transition to started, generate new `claude_session_id`
  - No session + `--task` → create session with `status=started`
  - No session + no `--task` → error ("stage first or use --task")
- Set `MG_MIND` and `MG_SESSION` env vars on launched process
- Write to disk + `ctx.tui.write()` to update TUI live
- Spawn WezTerm pane

### Claude session handling
- Always launch fresh `claude` process with `mg become`
- No auto-resume of native Claude sessions (corruption risk)
- New `claude_session_id` generated each time `mg start` runs
- Old IDs tracked for potential manual recovery
- `--session-id` still passed to Claude for tracking/correlation

### Env var chain for delegation
```
Human starts wren (no MG_SESSION set)
  └─ wren runs, MG_SESSION=<wren's mg session id>
      └─ wren: mg minds stage --task "file watching"
         └─ session created: parent=<wren's mg session id>
         └─ wren: mg start spark
            └─ spark runs, MG_SESSION=<spark's mg session id>
```

### TUI updates via TuiClient (not file watching)
- Commands use `ctx.tui.write()` to push changes directly
- More reliable than file watching, extends to non-disk data
- TuiModel's `SessionEntry` extended to match new fields

---

## What's Next (implementation order)

### 1. Session data model
- Extend `Session` dataclass with new fields
- Extend `SessionEntry` in TuiModel
- Update `create_session`, `save_session`, `load_sessions` helpers
- Add archive logic (separate store for old sessions)

### 2. Update `mg minds stage`
- Add `--task` and `--description` flags
- Create session at stage time with `status=staged`
- Read `MG_SESSION` for parent link
- Archive existing session if re-staging
- Push to TUI via `ctx.tui.write()`

### 3. Update `mg start <mind>`
- Remove `--tmux`, `--tui`, `--resume` flags
- Find existing session or create with `--task`
- Transition staged → started
- Generate new `claude_session_id`, track old
- Set `MG_SESSION` env var
- Push to TUI via `ctx.tui.write()`
- Spawn WezTerm pane

### 4. TUI display updates
- Update SessionsSection widget to show status
- Show delegation tree (parent relationships)

---

## Known Issues

- **MarkdownViewer scroll lag** — Occasional hitches during scroll. Likely Textual rendering overhead. Living with it for now.
- **TUI crash recovery** — If the TUI pane crashes, `mg start` should detect and restart it. Currently requires manual restart.

---

## Active Minds

| Mind | Task | Status |
|------|------|--------|
| wren | Session-aware delegation redesign | Active (this session) |
| spark | WezTerm wrapper | Staged in `_new/`, ready to start |
| sage | `mg minds suggest_role` | Paused, WIP committed |
