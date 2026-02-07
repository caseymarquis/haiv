# Immediate Plan

**Updated:** 2026-02-07

---

## Current Focus: TUI Launch UX & Session Completion

The session-aware delegation model is built and the pane management is verified working. Next priorities are making the TUI the primary control surface for launching/switching minds, and adding session completion so test sessions can be cleaned up.

---

## Priority 1: TUI-Driven Mind Switching

The TUI sessions list should let the human interact with minds directly.

**Actions from session list:**
- **Enter on staged session** → start it (transition session, spawn pane, switch to it)
- **Enter on started session** → switch to it (find parked tab, swap into hud)
- **Detection:** if a started session's pane is gone from WezTerm, it's dead — offer restart

**Pane identity:** Per-mind tabs with naming convention:
- `mg({project}):mind` — active in hud
- `~mind` — parked

Tab titles are queryable via `wezterm cli list`. No user vars needed (not in list output for our WezTerm version).

**Implementation path:**
- TUI needs to call `switch_to_mind()` or trigger `mg start` when user selects a session
- `switch_to_mind()` already exists in `TerminalManager` — needs wiring to TUI actions
- For "start staged": TUI could shell out to `mg start <mind>` or call the underlying Python directly

**Open question:** Should the TUI shell out to `mg start` (clean separation, domain logic stays in command) or call TerminalManager directly (avoids subprocess, but domain logic leaks)?

## Priority 2: Session Completion

Sessions currently have two states: `staged` and `started`. No way to mark them done.

**Needed:**
- A `completed` status (or similar)
- A way to trigger it: `mg sessions complete`? Mind marks itself done? Parent reviews?
- TUI filtering: hide completed sessions by default, show on demand
- Enables cleanup of test sessions that accumulate

## Priority 3: TUI Delegation Tree

Display parent relationships in the sessions widget. Data is already there (`parent` field). The Tree widget is already in use. Straightforward once priorities 1-2 are stable.

## Priority 4: Session Detail Pane

Richer preview when selecting a session: description, parent's task, claude_session_id, time info. Not urgent — current preview is functional.

---

## Key Files

| File | Role |
|------|------|
| `mg/src/mg/helpers/tui/terminal.py` | WezTerm pane management, tab naming, launch/switch/park |
| `mg/src/mg/helpers/tui/tui.py` | Thin facade: `launch_in_mind_pane()`, `switch_to_mind()`, `sessions_refresh()` |
| `mg/src/mg/helpers/sessions.py` | Session model, CRUD, `update_session` mutator pattern |
| `mg/src/mg/cmd.py` | `Ctx.tui` wired with TuiClient and sessions_file |
| `mg-core/src/mg_core/commands/start/_mind_.py` | Session-aware launch flow |
| `mg-core/src/mg_core/commands/minds/stage.py` | Creates staged sessions |
| `mg-core/src/mg_core/commands/tui/debug.py` | `mg tui debug` — WezTerm layout inspector |
| `mg-tui/src/mg_tui/widgets/sessions.py` | Sessions tree widget + preview |

---

## Known Issues

- **MarkdownViewer scroll lag** — Occasional hitches during scroll. Likely Textual rendering overhead. Living with it for now.
- **TUI crash recovery** — If the TUI pane crashes, `mg start` should detect and restart it. Currently requires manual restart.
- **Test sessions accumulate** — No completion mechanism yet. Priority 2.

---

## Active Minds

| Mind | Task | Status |
|------|------|--------|
| wren | TUI launch UX and session lifecycle | Active (this session) |
| sage | `mg minds suggest_role` | Paused, WIP committed |
