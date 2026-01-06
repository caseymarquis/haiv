"""Resolver for mind names.

Converts a mind name string to a Mind object using the helpers.minds module.
"""

import sys

from mg.resolvers import ResolverContext

from mg_core.helpers.minds import Mind, resolve_mind


def resolve(value: str, ctx: ResolverContext) -> Mind:
    """Resolve a mind name to a Mind object.

    Args:
        value: The mind name (e.g., "wren", "reed").
        ctx: Resolver context with paths.

    Returns:
        Mind object with resolved paths.

    Raises:
        MindNotFoundError: If mind not found.
        DuplicateMindError: If duplicate names exist.
    """
    mind = resolve_mind(value, ctx.paths.minds)

    # Ensure structure, warn on issues
    try:
        issues = mind.ensure_structure(fix=True)
        for issue in issues:
            status = "fixed" if issue.fixed else "not fixed"
            print(f"Warning: {issue.message} ({status})", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not ensure mind structure: {e}", file=sys.stderr)

    return mind
