"""File-based command routing for mg.

Routes command strings to Python files based on directory structure:
- Literal directories match exactly: `foo/` matches "foo"
- Param directories `_name_/` capture values: `_mind_/` captures "forge" as mind="forge"
- Explicit resolver `_name_as_resolver_/`: `_target_as_mind_/` captures with resolver="mind"
- Rest file `_rest_.py` captures remaining non-flag args
- Dunder names `__init__.py` are excluded from routing
- Flags (`--flag` only) terminate routing; everything from first flag → raw_flags
- Single-dash args (`-la`) are NOT flags - they pass through to rest

Precedence (evaluated level-by-level, not globally):
1. Literal matches always win over param matches at each level
2. If a literal leads to a valid route, param alternatives aren't tried
3. Multiple param matches at the same level → AmbiguousRouteError

Example: With `forge/status.py` and `_mind_/status.py`:
- "forge status" → literal `forge/` wins → `forge/status.py`
- "specs status" → no literal, param captures → `_mind_/status.py`

This matches user expectations: typed literals are intentional, params capture variable data.
"""

from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType


class AmbiguousRouteError(Exception):
    """Raised when multiple param directories could match."""

    pass


@dataclass
class ParamCapture:
    """Captured parameter from a param directory.

    Examples:
        _mind_/ with "forge" -> ParamCapture("forge", "mind", False)
        _target_as_mind_/ with "specs" -> ParamCapture("specs", "mind", True)
    """

    value: str
    resolver: str
    explicit_resolver: bool


@dataclass
class RouteMatch:
    """Result of routing - the matched file and captured values.

    At the routing layer, flags are not parsed - they're collected raw.
    Flag parsing happens in the parse() layer.

    file is None when no route was found (exists=False tests).
    """

    file: Path | None
    pkg_root: Path
    params: dict[str, ParamCapture] = field(default_factory=dict)
    rest: list[str] = field(default_factory=list)
    raw_flags: list[str] = field(default_factory=list)


def find_route(command_string: str, commands: ModuleType) -> RouteMatch | None:
    """Find the file that handles a command string.

    Args:
        command_string: Space-separated command like "forge message specs send"
        commands: Module whose __file__ points to commands/__init__.py

    Returns:
        RouteMatch with file path and captured params, or None if not found.
    """
    commands_dir = Path(commands.__file__).parent
    pkg_root = commands_dir.parent

    paths = paths_from_module(commands)
    result = find_route_in_paths(command_string, paths, pkg_root=pkg_root)

    if result is None:
        return None

    # Convert relative path to absolute
    result.file = commands_dir / result.file
    return result


def paths_from_module(commands: ModuleType) -> list[Path]:
    """Extract all .py file paths from a commands module directory.

    Returns paths relative to the module directory.
    """
    commands_dir = Path(commands.__file__).parent
    paths = []

    for py_file in commands_dir.rglob("*.py"):
        relative = py_file.relative_to(commands_dir)
        paths.append(relative)

    return paths


def find_route_in_paths(
    command_string: str,
    paths: list[Path],
    *,
    # Default allows tests to call without pkg_root; find_route always provides it
    pkg_root: Path = Path(),
) -> RouteMatch | None:
    """Find matching route from a list of paths.

    This is the core routing logic, operating on path lists for testability.

    Args:
        command_string: Space-separated command
        paths: List of relative paths to .py files
        pkg_root: Root of the package containing commands (set by find_route)

    Returns:
        RouteMatch or None if no match found.

    Raises:
        AmbiguousRouteError: If multiple param directories could match.
    """
    parts = command_string.split()

    # Separate routing parts from flags (everything from first - onward)
    route_parts, raw_flags = _split_at_flags(parts)

    # Build path tree for efficient matching
    tree = _build_path_tree(paths)

    # Find matches
    matches = _find_matches(tree, route_parts, {}, [])

    if not matches:
        return None

    # Check for ambiguity among param matches
    # Literal matches take precedence
    literal_matches = [m for m in matches if not m[1]]  # No params = literal
    if literal_matches:
        file_path, params, rest = literal_matches[0]
        return RouteMatch(
            file=file_path,
            pkg_root=pkg_root,
            params=params,
            rest=rest,
            raw_flags=raw_flags,
        )

    # All matches have params - check for ambiguity
    if len(matches) > 1:
        # Get the param directory names that are ambiguous
        param_dirs = set()
        for _, params, _ in matches:
            for p in params.values():
                # Find the directory name from the path
                param_dirs.add(f"_{p.resolver}_" if not p.explicit_resolver else f"_???_as_{p.resolver}_")
        raise AmbiguousRouteError(
            f"Ambiguous route: multiple param directories match: {param_dirs}"
        )

    file_path, params, rest = matches[0]
    return RouteMatch(
        file=file_path,
        pkg_root=pkg_root,
        params=params,
        rest=rest,
        raw_flags=raw_flags,
    )


def _split_at_flags(parts: list[str]) -> tuple[list[str], list[str]]:
    """Split parts into routing parts and raw flags.

    Routing stops at the first flag (starts with --).
    Only double-dash flags are recognized. Single dash is not a flag.
    Everything from the first flag onward goes to raw_flags.
    """
    for i, part in enumerate(parts):
        if part.startswith("--"):
            return parts[:i], parts[i:]
    return parts, []


def _build_path_tree(paths: list[Path]) -> dict:
    """Build a tree structure from paths for efficient matching.

    Returns a nested dict where keys are path segments and leaves have
    a special "_file_" key with the full path.
    """
    tree: dict = {}

    for path in paths:
        parts = path.parts
        node = tree

        for i, part in enumerate(parts):
            if part not in node:
                node[part] = {}
            node = node[part]

            # If this is the last part (the .py file), mark it
            if i == len(parts) - 1:
                node["_file_"] = path

    return tree


def _find_matches(
    tree: dict,
    remaining: list[str],
    params: dict[str, ParamCapture],
    rest: list[str],
) -> list[tuple[Path, dict[str, ParamCapture], list[str]]]:
    """Recursively find all matching routes.

    Returns list of (file_path, params, rest) tuples.
    """
    # If no more parts to match, check if we're at a valid endpoint
    if not remaining:
        if "_file_" in tree:
            return [(tree["_file_"], params.copy(), rest.copy())]
        # Check for _rest_.py at this level
        if "_rest_.py" in tree and "_file_" in tree["_rest_.py"]:
            return [(tree["_rest_.py"]["_file_"], params.copy(), rest.copy())]
        return []

    part = remaining[0]
    rest_parts = remaining[1:]
    matches = []

    # Skip dunder parts
    if part.startswith("__"):
        return []

    # Try literal match first (highest precedence)
    literal_key = f"{part}.py"
    if literal_key in tree and not rest_parts:
        if "_file_" in tree[literal_key]:
            matches.append((tree[literal_key]["_file_"], params.copy(), []))

    # Try literal directory
    if part in tree:
        sub_matches = _find_matches(tree[part], rest_parts, params.copy(), rest.copy())
        matches.extend(sub_matches)

    # If we have literal matches, return early - no need to check rest/params
    if matches:
        return matches

    # Check for ambiguity: _rest_.py cannot coexist with param files/dirs
    has_rest = "_rest_.py" in tree and "_file_" in tree["_rest_.py"]
    has_params = _has_param_entries(tree)

    if has_rest and has_params:
        raise AmbiguousRouteError(
            f"_rest_.py cannot coexist with param files/directories at the same level"
        )

    # Try _rest_.py at current level (consumes all remaining)
    if has_rest:
        new_rest = rest.copy() + remaining
        matches.append((tree["_rest_.py"]["_file_"], params.copy(), new_rest))

    # Try param files and directories
    for key in tree:
        if not key.startswith("_") or key.startswith("__"):
            continue
        if key == "_rest_.py":
            continue

        # Try param files (_name_.py) - must be leaf (no more parts)
        if key.endswith("_.py") and not rest_parts:
            param_info = _parse_param_file(key)
            if param_info is not None:
                param_name, resolver, explicit = param_info
                if "_file_" in tree[key]:
                    new_params = params.copy()
                    new_params[param_name] = ParamCapture(
                        value=part,
                        resolver=resolver,
                        explicit_resolver=explicit,
                    )
                    matches.append((tree[key]["_file_"], new_params, []))
            continue

        # Try param directories (_name_/)
        if not key.endswith("_"):
            continue

        # Parse param directory name
        param_info = _parse_param_dir(key)
        if param_info is None:
            continue

        param_name, resolver, explicit = param_info

        new_params = params.copy()
        new_params[param_name] = ParamCapture(
            value=part,
            resolver=resolver,
            explicit_resolver=explicit,
        )

        sub_matches = _find_matches(tree[key], rest_parts, new_params, rest.copy())
        matches.extend(sub_matches)

    return matches


def _has_param_entries(tree: dict) -> bool:
    """Check if tree has any param files or param directories."""
    for key in tree:
        if not key.startswith("_") or key.startswith("__"):
            continue
        if key == "_rest_.py":
            continue
        # Check for param file (_name_.py)
        if key.endswith("_.py") and _parse_param_file(key) is not None:
            return True
        # Check for param directory (_name_/)
        if key.endswith("_") and _parse_param_dir(key) is not None:
            return True
    return False


def _parse_param_dir(name: str) -> tuple[str, str, bool] | None:
    """Parse a param directory name like _name_ or _target_as_mind_.

    Returns (param_name, resolver_name, explicit_resolver) or None if not a param dir.
    """
    if not name.startswith("_") or not name.endswith("_"):
        return None
    if name.startswith("__"):
        return None
    if name == "_rest_":
        return None

    inner = name[1:-1]  # Remove leading/trailing _

    if "_as_" in inner:
        parts = inner.split("_as_", 1)
        return (parts[0], parts[1], True)
    else:
        # Implicit resolver: _mind_/ means param="mind", resolver="mind"
        return (inner, inner, False)


def _parse_param_file(name: str) -> tuple[str, str, bool] | None:
    """Parse a param file name like _name_.py or _target_as_mind_.py.

    Returns (param_name, resolver_name, explicit_resolver) or None if not a param file.
    """
    if not name.startswith("_") or not name.endswith("_.py"):
        return None
    if name.startswith("__"):
        return None
    if name == "_rest_.py":
        return None

    # Remove leading _ and trailing _.py
    inner = name[1:-4]

    if "_as_" in inner:
        parts = inner.split("_as_", 1)
        return (parts[0], parts[1], True)
    else:
        # Implicit resolver: _mind_.py means param="mind", resolver="mind"
        return (inner, inner, False)
