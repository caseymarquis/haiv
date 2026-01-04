"""Resolver discovery and execution for mg.

Resolvers transform raw string parameters into domain objects.
For example, a "mind" resolver converts "forge" to a Mind object.

Resolver files live in `resolvers/{type}.py` within each package.
Each resolver module must have a `resolve(value: str, ctx: ResolverContext) -> Any` function.

Example resolver (resolvers/mind.py):
    def resolve(value: str, ctx: ResolverContext) -> Mind:
        return get_mind(ctx.paths.user.state / "minds", value)
"""

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from mg.args import ResolveRequest


class ResolverError(Exception):
    """Base class for resolver errors."""

    pass


class UnknownResolverError(ResolverError):
    """Raised when a resolver type is not found."""

    def __init__(self, resolver_name: str, available: list[str]):
        self.resolver_name = resolver_name
        self.available = available
        available_str = ", ".join(sorted(available)) if available else "(none)"
        super().__init__(
            f"Unknown resolver: '{resolver_name}'\n"
            f"Available resolvers: {available_str}"
        )


class UserRequiredError(ResolverError):
    """Raised when a resolver needs user context but none is available."""

    def __init__(self, resolver_name: str):
        self.resolver_name = resolver_name
        super().__init__(
            f"Resolver '{resolver_name}' requires user context.\n"
            f"Run 'mg users new --name <name>' to create a user identity."
        )


@dataclass
class ResolverContext:
    """Context passed to resolver functions.

    Provides access to paths and other resources resolvers need.
    """

    paths: Any  # mg.paths.Paths - use Any to avoid circular import
    container: Any | None = None  # punq.Container


def discover_resolvers(pkg_root: Path) -> dict[str, Path]:
    """Discover resolver files from a package's resolvers/ directory.

    Args:
        pkg_root: Root of a package (e.g., mg_core, mg_project, mg_user)
                  Should contain a resolvers/ directory.

    Returns:
        Dictionary mapping resolver names to file paths.
        Example: {"mind": Path(".../resolvers/mind.py")}

    Files starting with underscore are ignored.
    """
    resolvers_dir = pkg_root / "resolvers"
    if not resolvers_dir.exists():
        return {}

    resolvers: dict[str, Path] = {}

    for item in resolvers_dir.iterdir():
        # Skip underscore files
        if item.name.startswith("_"):
            continue

        # Only include .py files (not directories)
        if item.is_file() and item.suffix == ".py":
            resolver_name = item.stem
            resolvers[resolver_name] = item

    return resolvers


def load_resolver(resolver_path: Path, *, quiet: bool = False) -> ModuleType | None:
    """Load a resolver module from a file path.

    Invalid or broken resolvers are skipped with a warning (unless quiet=True).
    This ensures a broken resolver doesn't block the user's work.

    Args:
        resolver_path: Path to the resolver .py file
        quiet: If True, suppress warning messages for invalid resolvers

    Returns:
        Loaded module with a resolve() function, or None if invalid/broken
    """
    try:
        module_name = f"mg_resolver_{resolver_path.stem}_{id(resolver_path)}"
        spec = importlib.util.spec_from_file_location(module_name, resolver_path)

        if spec is None or spec.loader is None:
            if not quiet:
                print(f"Warning: Cannot load resolver from {resolver_path}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Validate that the module has a resolve function
        if not hasattr(module, "resolve"):
            if not quiet:
                print(f"Warning: Resolver {resolver_path} missing resolve() function, skipping")
            return None

        return module

    except Exception as e:
        if not quiet:
            print(f"Warning: Error loading resolver {resolver_path}: {e}")
        return None


def make_resolver(
    pkg_roots: list[Path],
    paths: Any,  # mg.paths.Paths
    container: Any | None = None,  # punq.Container
    *,
    has_user: bool = False,
    quiet: bool = False,
) -> Callable[[ResolveRequest], Any]:
    """Create a resolve callback from discovered resolvers.

    Discovers resolvers from all pkg_roots. Later packages override earlier ones,
    so mg_user resolvers take precedence over mg_project over mg_core.

    Resolution behavior depends on whether the resolver was explicit or implicit:
    - Explicit (param != resolver, from _target_as_mind_/): Resolver must exist
    - Implicit (param == resolver, from _mind_/): Resolver optional, returns raw value

    Args:
        pkg_roots: List of package roots to scan for resolvers/
        paths: Paths object for resolver context
        container: Optional DI container for resolver context
        has_user: Whether user context is available. If False and a resolver
                  is found, raises UserRequiredError.
        quiet: If True, suppress warning messages for invalid resolvers

    Returns:
        Callback function suitable for build_ctx(resolve=...)
    """
    # Discover all resolvers, later packages override earlier
    all_resolver_paths: dict[str, Path] = {}
    for pkg_root in pkg_roots:
        discovered = discover_resolvers(pkg_root)
        all_resolver_paths.update(discovered)

    # Load all resolver modules upfront (skipping broken ones)
    loaded_resolvers: dict[str, ModuleType] = {}
    for name, path in all_resolver_paths.items():
        module = load_resolver(path, quiet=quiet)
        if module is not None:
            loaded_resolvers[name] = module

    # Create the resolver context
    ctx = ResolverContext(paths=paths, container=container)

    def resolve(req: ResolveRequest) -> Any:
        """Resolve a parameter value using the appropriate resolver."""
        is_explicit = req.param != req.resolver

        # Check if resolver exists
        if req.resolver not in loaded_resolvers:
            if is_explicit:
                # Explicit resolver must exist
                raise UnknownResolverError(req.resolver, list(loaded_resolvers.keys()))
            else:
                # Implicit resolver is optional - return raw value
                return req.value

        # Found a resolver - now check if we have user context
        if not has_user:
            raise UserRequiredError(req.resolver)

        # Call the resolver
        resolver_module = loaded_resolvers[req.resolver]
        return resolver_module.resolve(req.value, ctx)

    return resolve
