"""Environment variables used by mg.

This module centralizes all environment variable names used by mg.
Import from here rather than hardcoding strings.
"""

# Root of the mg-managed repo where the mg-state control plane branch lives.
# When set, mg uses this path instead of searching for the root.
MG_ROOT = "MG_ROOT"
