# Task: Research mind status detection

Research how we can detect and display the current status of each mind. Possible states include: thinking (actively processing), waiting on tool approval, idle (waiting for human input), and not running.

**This is a research task — produce a written report, not code.**

---

## Context

We run multiple Claude Code instances in parallel, each in its own WezTerm pane. We need visibility into what each instance is doing so the human and coordinating minds know where attention is needed.

Our existing solution (`mg next` using `tmux capture-pane`) is outdated — we've moved from tmux to WezTerm. See Problem #1 in `users/casey/state/minds/wren/work/docs/problems.md` for background.

---

## Areas to Research

### Claude Code hooks

Claude Code supports a hooks system. Investigate what hook events are available, what data they provide, and whether they can signal status changes (e.g., "waiting for user input", "tool approval needed", "processing"). Look at the official Claude Code documentation and any configuration files in `~/.claude/`.

### Claude Code status line

Claude Code has a status line feature. Can we read it programmatically? Does it expose state information?

### WezTerm pane content

WezTerm has `cli get-text` for reading pane content. Could we detect status from the terminal output (prompt patterns, spinner, etc.)? How reliable would this be?

### File-based signaling

Could hooks write to a known file that our TUI polls? What would the latency and reliability look like?

---

## Deliverable

Write your findings to `work/research-report.md`. For each approach, cover:
- How it works
- What status information it can provide
- Limitations and reliability concerns
- How it could integrate with our TUI and `mg sessions` display
