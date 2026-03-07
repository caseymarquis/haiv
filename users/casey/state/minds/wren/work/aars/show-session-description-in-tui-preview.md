# AAR: Show session description in TUI preview

## Summary

Wired the `description` field through the full TUI pipeline so it displays in the session preview pane. Also redesigned the preview layout to be more compact: `mind: task` header, metadata on one line, description as its own block below.

## Key Decisions

- Compact preview layout (`mind: task\nStatus: status | Session: id\n\ndescription`) — proposed by Casey, replaces the previous four separate labeled lines. Cleaner and mirrors the tree label format.
- Description block omitted entirely when empty — no blank lines or placeholder text when absent.
- `max-height: 8` kept as-is — long descriptions will clip, which is acceptable for a preview pane. Scrolling can be added later if needed.

## Open Items

- TUI widget layer has no tests. The `sessions_refresh` helper tests exercise the `Session → SessionEntry` pipeline but don't explicitly assert on description. Low risk given simplicity.
- Long descriptions will truncate at max-height 8 (~5 lines of description visible). Fine for now.

## Commits and Files Changed

- 21cacf9 feat: wire session description through TUI preview
  Key files: haiv/src/haiv/helpers/tui/TuiModel.py, haiv/src/haiv/helpers/tui/helpers.py, haiv-tui/src/haiv_tui/widgets/sessions.py
