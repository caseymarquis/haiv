"""Environment variables used by haiv.

This module centralizes all environment variable names used by haiv.
Import from here rather than hardcoding strings.
"""

# Root of the haiv-managed repo where the haiv control plane branch lives.
# When set, haiv uses this path instead of searching for the root.
HV_ROOT = "HV_ROOT"

# Program name override for CLI display.
# Used by wrapper scripts that invoke haiv.
HV_PROG = "HV_PROG"

# Current mind name, set by `hv start {mind}`.
# Used by commands that need to know which mind is running.
HV_MIND = "HV_MIND"

# Current haiv session ID, set by `hv start {mind}`.
# Used to track delegation chains (parent session).
HV_SESSION = "HV_SESSION"

# IPC address for Claude Code hook dispatch.
# Set by build_env() so hook commands can route events to the TUI.
HV_CLAUDE_HOOK_DISPATCH = "HV_CLAUDE_HOOK_DISPATCH"
