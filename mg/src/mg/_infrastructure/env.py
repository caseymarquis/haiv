"""Environment variables used by mg.

This module centralizes all environment variable names used by mg.
Import from here rather than hardcoding strings.
"""

# Root of the mg-managed repo where the mg-state control plane branch lives.
# When set, mg uses this path instead of searching for the root.
MG_ROOT = "MG_ROOT"

# Program name override for CLI display.
# Used by wrapper scripts that invoke mg.
MG_PROG = "MG_PROG"

# Current mind name, set by `mg start {mind}`.
# Used by commands that need to know which mind is running.
MG_MIND = "MG_MIND"

# Current mg session ID, set by `mg start {mind}`.
# Used to track delegation chains (parent session).
MG_SESSION = "MG_SESSION"
