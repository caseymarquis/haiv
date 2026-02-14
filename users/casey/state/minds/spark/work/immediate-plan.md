# Immediate Plan

## Status: Research report delivered

Wrote `work/research-report.md` covering mind status detection via Claude Code hooks.

## Key findings
- Hooks fully cover state detection (idle, working, waiting-approval, stopped)
- Every hook receives `session_id` on stdin — links to mind via session registry
- `MG_MIND` env var access from hooks needs verification (docs vs bug report conflict)
- Architecture: hooks → thin client → unix socket → TUI message queue → model update thread

## Open question requiring verification
- Does `MG_MIND` environment variable propagate to hook commands? Quick test needed.
