# Research Report: Claude Code Hook Integration

## Part 1: Findings

### Claude Code hooks fully cover state detection

Claude Code's hooks system provides 14 lifecycle events. Six cover our status detection needs:

| Event | Matcher | State Signal |
|-------|---------|-------------|
| `Notification` | `idle_prompt` | **Idle** — waiting for input |
| `Notification` | `permission_prompt` | **Waiting on approval** |
| `PreToolUse` | (any) | **Working** — executing a tool |
| `Stop` | — | **Finished responding** |
| `SessionStart` | — | **Session active** |
| `SessionEnd` | — | **Not running** |

All events provide structured JSON on stdin with common fields (`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `permission_mode`) plus event-specific data. No WezTerm pane scraping needed.

### Hook configuration constraints

- **No cwd override** — hooks run in Claude Code's cwd. `mg` is installed system-wide so we call it directly.
- **No dynamic variable substitution** in command strings. Only `$CLAUDE_PROJECT_DIR`, `$CLAUDE_PLUGIN_ROOT`, and `$CLAUDE_CODE_REMOTE` are expanded. All other dynamic data comes via stdin JSON.
- **No CLI for hook management** — configuration lives in `.claude/settings.local.json`.
- **Hooks load at session startup** — changes take effect on next session or after `/hooks` review.

### `$CLAUDE_PROJECT_DIR` solves mg root discovery

Claude Code expands `$CLAUDE_PROJECT_DIR` in hook command strings before execution. This provides the project root path — the starting point for `get_mg_root()`'s upward walk.

### Existing IPC: `multiprocessing.connection`

The TuiServer uses `multiprocessing.connection` for cross-platform IPC over a unix socket (or named pipe on Windows). Current protocol is request/response with optimistic concurrency via version fields.

### Approaches investigated and discarded

**Claude Code status line** — Researched but found no reliable programmatic access. The status line displays model info and token counts in the terminal UI, but there's no file-based or IPC mechanism to read it externally. Hooks provide the same state information with structured data.

**WezTerm pane content** (`wezterm cli get-text`) — The existing `mg next` approach ported to WezTerm. Works (pattern-match "esc to interrupt" in captured text) but fragile — depends on Claude Code's terminal output format. Hooks provide semantic state directly, making pane scraping unnecessary.

**File-based signaling** — Hooks writing to files that the TUI polls. Viable but adds latency and cleanup burden. The single-channel message wrapper through the existing IPC is cleaner.

### What hooks cannot detect

- **"Thinking" without tool calls** — inferred from absence of `idle_prompt`.
- **Crashes** — `SessionEnd` may not fire. Stale timestamps catch this.

---

## Part 2: Decisions

### session_id is the sole identifier

No custom environment variables. Every hook event includes `session_id`. The session registry maps sessions to minds. The dispatcher passes `session_id` through; the TUI resolves identity.

### `MG_ROOT` via inline shell variable

The hook command sets `MG_ROOT` using shell inline syntax:

```
MG_ROOT=$CLAUDE_PROJECT_DIR mg claude_hook dispatch
```

Claude Code expands `$CLAUDE_PROJECT_DIR` in the command string. The shell sets `MG_ROOT` for the process. `get_mg_root()` already checks `MG_ROOT` first before walking up from `cwd`. No CLI changes needed — the existing env var handling does exactly what we want.

### `mg claude_hook dispatch` — general-purpose dispatcher

All Claude Code hooks route through a single dispatcher. Status detection is the first handler, but the infrastructure supports future use cases. `MG_ROOT` is set via inline shell variable in the hook command. The dispatcher reads stdin JSON, deserializes to a typed event, and routes to handlers.

### Two hook systems, distinct naming

| System | Package | Purpose |
|--------|---------|---------|
| **Claude Code hooks** | `claude_hooks` | Receives Claude Code lifecycle events |
| **mg command hooks** | `mg_hooks` | Observer/event pattern for mg commands |

Class naming convention: `AbcClaudeHook` — event name first, `ClaudeHook` suffix as type family. Base class is `ClaudeHook`. Comments should always specify which hook system is being discussed.

### Typed Python models for hook events

Predefined dataclasses for each Claude Code hook event with automated JSON→type translation. `ClaudeHook` as the base, subclasses for each event type (e.g., `PreToolUseClaudeHook`, `NotificationClaudeHook`). Unknown events fall back to the base type.

### Single channel with message wrapper

Reuse the existing `multiprocessing.connection` channel — it's cross-platform, already proven, and we don't want a second socket. A message wrapper distinguishes message kinds using typed fields (multiple `SomeType | None` fields) plus a `type: str` discriminator for convenience. The server dispatches on `type`: request/response for reads and writes, fire-and-forget for hook messages.

### Claude-guided hook installation

`mg claude_hooks setup` outputs prompts, TODOs, and example configuration. Claude reads the existing `.claude/settings.local.json` and does the merge — handling edge cases naturally. All hooks call the same command: `MG_ROOT=$CLAUDE_PROJECT_DIR mg claude_hook dispatch`.

---

## Part 3: Implementation Plan

### Phase 0: Smoke test `$CLAUDE_PROJECT_DIR` expansion

Confirm that `$CLAUDE_PROJECT_DIR` is reliably expanded in hook command strings. Add a trivial hook that writes the expanded value to a temp file. This gates everything — if expansion is unreliable, we need an alternative.

### Phase 1: `claude_hooks` typed models

Dataclasses for each Claude Code hook event. Deserialization from stdin JSON keyed on `hook_event_name`. Graceful fallback for unknown events.

**Depends on:** Nothing.

### Phase 2: Message wrapper on TuiServer channel

Extend the existing IPC channel with a message wrapper. Typed fields for each message kind plus a `type` discriminator. Server dispatches on type — responds for reads/writes, fire-and-forget for hook messages. Update `TuiClient` to use the wrapper.

**Depends on:** Nothing.

### Phase 3: `mg claude_hook dispatch` command

Single entry point for all Claude Code hook events. `MG_ROOT` is set via inline shell variable in the hook command — no CLI changes needed. Uses Phase 1 for deserialization, Phase 2 for sending messages to the TUI. First handler: status derivation from hook events.

**Depends on:** Phases 1, 2.

### Phase 4: Status in `TuiModel`

Add status fields to session entries in `SessionsSection`. Model thread applies status updates from incoming hook messages by matching `session_id`.

**Depends on:** Phase 2.

### Phase 5: `mg claude_hooks setup`

Outputs prompts, TODOs, and example hook configuration for Claude to merge into `.claude/settings.local.json`.

**Depends on:** Phase 3.

### Phase 6: TUI status display

Wire session status fields to the Textual UI. The store already fires `sessions_changed` signals when the section updates.

**Depends on:** Phase 4.

### Parallelism

```
Phase 0 (smoke test)
  │
Phase 1 (typed models) ────────┐
  │                              ├──→ Phase 3 (dispatch) ──→ Phase 5 (setup)
Phase 2 (message wrapper) ─────┘──→ Phase 4 (model) ──→ Phase 6 (TUI)
```

### Technical risks

1. **`$CLAUDE_PROJECT_DIR` reliability** — [GitHub issue #9567](https://github.com/anthropics/claude-code/issues/9567) reports hook env vars can be empty. We use command-string expansion (not runtime env var access), but Phase 0 confirms this works.

2. **Message wrapper is a protocol change** — existing `TuiClient` callers need updating. Consider backward compatibility during transition.

---

## Part 4: Reference

### All Claude Code hook events (14 total)

Events we subscribe to initially are marked *.

| Event | Fires When | Can Block? |
|-------|-----------|-----------|
| `PreToolUse` * | Before tool executes | Yes |
| `PostToolUse` * | After tool succeeds | No |
| `PostToolUseFailure` | After tool fails | No |
| `Notification` * | Notification sent | No |
| `Stop` * | Response complete | Yes |
| `SessionStart` * | Session begins/resumes | No |
| `SessionEnd` * | Session terminates | No |
| `UserPromptSubmit` | User submits prompt | Yes |
| `PermissionRequest` | Permission dialog | Yes |
| `SubagentStart` | Subagent spawned | No |
| `SubagentStop` | Subagent finishes | Yes |
| `TeammateIdle` | Teammate going idle | Yes |
| `TaskCompleted` | Task marked complete | Yes |
| `PreCompact` | Before compaction | No |

### Key file locations

| Component | Path |
|-----------|------|
| TuiServer | `worktrees/main/mg/src/mg/_infrastructure/TuiServer/` |
| IPC contract | `_TuiIpc.py` in TuiServer |
| Remote client | `worktrees/main/mg/src/mg/helpers/tui/TuiClient.py` |
| Model | `worktrees/main/mg/src/mg/helpers/tui/TuiModel.py` |
| Store (UI) | `worktrees/main/mg-tui/src/mg_tui/store.py` |
| Paths/root resolution | `worktrees/main/mg/src/mg/paths.py` |
| Env vars | `worktrees/main/mg/src/mg/_infrastructure/env.py` |
