"""Argument building for mg commands.

Converts route matches + flag definitions into a populated Ctx.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from mg import cmd
from mg.paths import Paths
from mg._infrastructure.loader import Command
from mg._infrastructure.routing import RouteMatch


@dataclass
class ResolveRequest:
    """Request to resolve a parameter value.

    When a route has parameters like _mind_/, the raw string value needs
    to be converted to an object. In production, resolvers load real objects.
    In tests, you provide a mock resolver.

    Example for: mg forge message specs send
        Route: commands/_mind_/message/_target_as_mind_/send.py

        Two ResolveRequests would be made:
            ResolveRequest(param="mind", resolver="mind", value="forge")
            ResolveRequest(param="target", resolver="mind", value="specs")

        Note: Both use resolver="mind", but param differs.
    """

    param: str      # The parameter name (e.g., "mind" or "target")
    resolver: str   # The resolver to use (e.g., "mind" for both above)
    value: str      # The raw value (e.g., "forge" or "specs")


def build_ctx(
    route: RouteMatch,
    command: Command,
    *,
    mg_root: Path | None = None,
    mg_username: str | None = None,
    resolve: Callable[[ResolveRequest], Any] | None = None,
) -> cmd.Ctx:
    """Build a Ctx from a route match and command definition.

    Args:
        route: The matched route with params, rest, and raw_flags
        command: The loaded command (for flag definitions)
        mg_root: Root of the mg-managed repo, if known
        mg_username: Name of the current user (folder name in users/)
        resolve: Optional callback to resolve param/flag values to objects

    Returns:
        Populated Ctx ready for execute()

    Raises:
        ValueError: If flags are invalid (unknown, missing values, etc.)
    """
    definition = command.define()
    args = cmd.Args()

    # Populate rest
    args._rest = route.rest.copy()

    # Resolve and add params
    for param_name, capture in route.params.items():
        value: Any = capture.value
        if resolve is not None:
            req = ResolveRequest(
                param=param_name,
                resolver=capture.resolver,
                value=capture.value,
            )
            value = resolve(req)
        args._values[param_name] = [value]

    # Parse flags
    flag_defs = {f.name: f for f in definition.flags}
    _parse_flags(route.raw_flags, flag_defs, args, resolve)

    paths = Paths(
        _called_from=Path(os.getcwd()),
        _pkg_root=route.pkg_root,
        _mg_root=mg_root,
        _user_name=mg_username,
    )
    return cmd.Ctx(args=args, paths=paths)


def _parse_flags(
    raw_flags: list[str],
    flag_defs: dict[str, cmd.Flag],
    args: cmd.Args,
    resolve: Callable[[ResolveRequest], Any] | None,
) -> None:
    """Parse raw flags into args._values.

    Args:
        raw_flags: List of raw flag strings (e.g., ["--file", "path.txt"])
        flag_defs: Flag definitions by name
        args: Args instance to populate
        resolve: Optional resolver callback
    """
    i = 0
    last_flag: str | None = None

    while i < len(raw_flags):
        token = raw_flags[i]

        if not token.startswith("--"):
            # Unconsumed value - this means a flag got too many values
            if last_flag:
                raise ValueError(
                    f"--{last_flag} accepts at most {flag_defs[last_flag].max_args} "
                    f"value(s), got too many values"
                )
            else:
                raise ValueError(f"Unexpected value: {token}")

        # Handle --flag=value syntax
        if "=" in token:
            flag_part, value_part = token[2:].split("=", 1)
            flag_name = flag_part
            initial_value = value_part
        else:
            flag_name = token[2:]
            initial_value = None

        last_flag = flag_name

        # Check flag is defined
        if flag_name not in flag_defs:
            raise ValueError(f"Unknown flag: --{flag_name}")

        flag_def = flag_defs[flag_name]
        i += 1

        # Handle boolean flags
        if flag_def.type is bool:
            args._values[flag_name] = [True]
            continue

        # Collect values for this flag
        values: list[str] = []
        if initial_value is not None:
            values.append(initial_value)

        # Consume following non-flag tokens up to max_args
        max_args = flag_def.max_args
        while i < len(raw_flags) and not raw_flags[i].startswith("--"):
            if max_args is not None and len(values) >= max_args:
                break
            values.append(raw_flags[i])
            i += 1

        # Validate min_args
        min_args = flag_def.min_args
        if len(values) < min_args:
            raise ValueError(
                f"--{flag_name} requires at least {min_args} value(s), got {len(values)}"
            )

        # Resolve values if resolver specified
        if flag_def.resolver and resolve is not None:
            resolved_values = []
            for v in values:
                req = ResolveRequest(
                    param=flag_name,
                    resolver=flag_def.resolver,
                    value=v,
                )
                resolved_values.append(resolve(req))
            values = resolved_values

        args._values[flag_name] = values
