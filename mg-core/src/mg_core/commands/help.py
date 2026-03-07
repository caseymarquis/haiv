"""haiv help - List available commands with descriptions.

Discovers commands from all haiv packages (haiv_core, hv_project, hv_user)
and displays them with their descriptions from define().
"""

import re

from haiv import cmd
from haiv.helpers.commands import CommandInfo, discover_commands


def define() -> cmd.Def:
    return cmd.Def(
        description="List available commands",
        flags=[
            cmd.Flag("for", description="Show detailed help (e.g. --for 1.2 or --for become)"),
        ],
    )


def _is_numeric_id(s: str) -> bool:
    """Check if string looks like a numeric ID (e.g., '1.2')."""
    return bool(re.match(r"^\d+\.\d+$", s))


def _show_command_detail(ctx: cmd.Ctx, info, pkg_name: str, commands_dir) -> None:
    """Show detailed help for a single command."""
    definition = info.load_definition()

    ctx.print(info.name)
    ctx.print()
    ctx.print(f"  Description: {definition.description}")
    ctx.print()

    if definition.flags:
        ctx.print("  Flags:")
        for flag in definition.flags:
            flag_desc = flag.description or ""
            ctx.print(f"    --{flag.name:12} {flag_desc}")
    else:
        ctx.print("  Flags:       (none)")
    ctx.print()

    relative_path = info.file.relative_to(commands_dir)
    ctx.print(f"  Module:      {pkg_name}")
    ctx.print(f"  File:        commands/{relative_path}")
    ctx.print(f"  Full path:   {info.file}")


def execute(ctx: cmd.Ctx) -> None:
    package_commands = discover_commands(ctx.paths.root_or_none)

    # Handle --for flag
    if ctx.args.has("for"):
        query = ctx.args.get_one("for")

        # Build index for lookups
        indexed = []
        for pkg_idx, pkg_cmds in enumerate(package_commands, start=1):
            for cmd_idx, info in enumerate(pkg_cmds.commands, start=1):
                cmd_id = f"{pkg_idx}.{cmd_idx}"
                indexed.append((cmd_id, pkg_cmds.package.name, pkg_cmds.package.paths.commands_dir, info))

        if _is_numeric_id(query):
            # Lookup by numeric ID
            for cmd_id, pkg_name, commands_dir, info in indexed:
                if cmd_id == query:
                    _show_command_detail(ctx, info, pkg_name, commands_dir)
                    return
            ctx.print(f"No command with ID '{query}'")
        else:
            # Treat as regex pattern matching command names
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error:
                ctx.print(f"Invalid pattern: {query}")
                return

            matches = [(cmd_id, pkg_name, commands_dir, info)
                       for cmd_id, pkg_name, commands_dir, info in indexed
                       if pattern.search(info.name)]

            if not matches:
                ctx.print(f"No commands matching '{query}'")
            elif len(matches) == 1:
                # Single match - show detailed help directly
                cmd_id, pkg_name, commands_dir, info = matches[0]
                _show_command_detail(ctx, info, pkg_name, commands_dir)
            else:
                # Multiple matches - show list with IDs, grouped by package
                ctx.print(f"Multiple commands matching '{query}':")
                ctx.print()

                # Group by package name
                by_package: dict[str, list[tuple[str, CommandInfo]]] = {}
                for cmd_id, pkg_name, commands_dir, info in matches:
                    if pkg_name not in by_package:
                        by_package[pkg_name] = []
                    by_package[pkg_name].append((cmd_id, info))

                for pkg_name, cmds in by_package.items():
                    ctx.print(f"{pkg_name}:")
                    for cmd_id, info in cmds:
                        try:
                            definition = info.load_definition()
                            ctx.print(f"  {cmd_id:5} {info.name:24} {definition.description}")
                        except Exception:
                            ctx.print(f"  {cmd_id:5} {info.name}")
                    ctx.print()
        return

    # List view
    ctx.print("Use --for <id> to see detailed help (e.g. hv help --for 1.2)")
    ctx.print()

    for pkg_idx, pkg_cmds in enumerate(package_commands, start=1):
        pkg_root = pkg_cmds.package.paths.root
        ctx.print(f"{pkg_idx}. {pkg_cmds.package.name} ({pkg_root})")
        ctx.print()
        for cmd_idx, info in enumerate(pkg_cmds.commands, start=1):
            try:
                definition = info.load_definition()
                cmd_id = f"{pkg_idx}.{cmd_idx}"
                ctx.print(f"  {cmd_id:5} {info.name:24} {definition.description}")
            except Exception:
                pass
        ctx.print()
