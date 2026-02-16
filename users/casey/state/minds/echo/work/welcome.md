# Task Assignment

**Implement Claude Code hook integration for mind status**

Build the pipeline that lets Claude Code lifecycle events flow into the TUI as live mind status. Spark's research has a complete design — read it first.

**Location:** `worktrees/echo/`

---

## Context

We manage multiple minds working in parallel. Right now there's no way to see who's idle and needs attention vs who's actively working. Claude Code provides hooks that fire on lifecycle events (idle, working, waiting for approval, session start/end). We need to capture these and surface them in the TUI.

## Essential Reading

- `temp-aar/claude-hook-integration.md` — Spark's full research and implementation plan. This is your roadmap. It covers typed models, IPC changes, the dispatch command, and TUI integration across 6 phases.
- `temp-aar/luna-mg-hooks.md` — The existing mg hook system (different from Claude Code hooks). Understand the distinction.

## Key files

- `mg/src/mg/_infrastructure/TuiServer/` — IPC server, needs message wrapper extension
- `mg/src/mg/helpers/tui/TuiClient.py` — IPC client
- `mg/src/mg/helpers/tui/TuiModel.py` — `SessionEntry` needs status fields
- `mg-tui/src/mg_tui/widgets/sessions.py` — TUI rendering

## Scope

This is a substantial project. The research doc has 6 phases — you may not get through all of them. Focus on getting the plumbing right (phases 1-3) so events can flow, then wire status into the TUI (phases 4-6). Discuss priorities with Casey.

---

## Success Criteria

- Claude Code hook events can be received and dispatched
- Mind status is visible in the TUI
- Existing IPC and TUI functionality isn't broken

---

## Before You Begin

Read the full assignment, then discuss your understanding and approach with your human collaborator before writing code. The task description is a starting point — not a spec. Do not use planning tools unless your human explicitly requests it. You work best together.
