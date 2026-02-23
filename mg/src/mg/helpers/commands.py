"""Command discovery for mg.

Discovers commands from mg packages. Discovery is lightweight (filesystem only);
loading definitions happens lazily via load_definition().
"""

from dataclasses import dataclass, field
from pathlib import Path

from mg import cmd
from mg.helpers.packages import PackageInfo, discover_packages
from mg._infrastructure.loader import load_command


@dataclass
class CommandInfo:
    """Information about a discovered command.

    Use `name` and `file` for lightweight operations.
    Call `load_definition()` to load the command module (cached after first call).
    """

    name: str
    file: Path
    _definition: cmd.Def | None = field(default=None, repr=False)

    def load_definition(self) -> cmd.Def:
        """Load and return the command definition.

        Loads the command module on first call, then caches the result.
        """
        if self._definition is None:
            command = load_command(self.file)
            self._definition = command.define()
        return self._definition

    def clear_definition(self) -> None:
        """Clear the cached definition, allowing reload on next access."""
        self._definition = None


@dataclass
class PackageCommands:
    """Commands discovered in a single package."""

    package: PackageInfo
    commands: list[CommandInfo]


def _segment_to_name(segment: str) -> str:
    """Convert a path segment to a command name part.

    Handles param patterns like _mind_ -> <mind> and _target_as_mind_ -> <target>.
    """
    # Check for param pattern: _name_ or _name_as_resolver_
    if segment.startswith("_") and segment.endswith("_") and not segment.startswith("__"):
        inner = segment[1:-1]  # Remove leading/trailing _
        # Handle _name_as_resolver_ pattern - extract just the param name
        if "_as_" in inner:
            param_name = inner.split("_as_", 1)[0]
            return f"<{param_name}>"
        return f"<{inner}>"
    return segment


def path_to_command_name(path: Path) -> str:
    """Convert a command file path to a command name.

    Examples:
        minds/new.py -> "minds new"
        start/_index_.py -> "start"
        start/_mind_.py -> "start <mind>"
        _mind_/status.py -> "<mind> status"

    Args:
        path: Relative path from commands/ directory.

    Returns:
        Human-readable command name.
    """
    parts = list(path.parts)

    # Handle the filename (last part)
    filename = parts[-1]
    if filename == "_index_.py":
        # _index_.py means the command is the directory itself
        parts = parts[:-1]
    else:
        # Remove .py extension and handle param patterns
        stem = filename.removesuffix(".py")
        # Handle param file: _name_.py or _name_as_resolver_.py
        if stem.startswith("_") and stem.endswith("_") and not stem.startswith("__"):
            inner = stem[1:-1]
            if "_as_" in inner:
                param_name = inner.split("_as_", 1)[0]
                parts[-1] = f"<{param_name}>"
            else:
                parts[-1] = f"<{inner}>"
        else:
            parts[-1] = stem

    # Convert directory parts (handle param directories)
    result_parts = []
    for part in parts:
        result_parts.append(_segment_to_name(part))

    return " ".join(result_parts)


def commands_for_package(package: PackageInfo) -> list[CommandInfo]:
    """Discover all commands in a package.

    Args:
        package: The package to scan.

    Returns:
        List of commands sorted by name.
    """
    commands_dir = package.paths.commands_dir
    commands: list[CommandInfo] = []

    for py_file in commands_dir.rglob("*.py"):
        relative = py_file.relative_to(commands_dir)

        # Skip any path containing dunder segments (e.g., __init__.py, __pycache__/)
        if any("__" in part for part in relative.parts):
            continue

        name = path_to_command_name(relative)
        commands.append(CommandInfo(name=name, file=py_file))

    return sorted(commands, key=lambda c: c.name)


def discover_commands(mg_root: Path | None) -> list[PackageCommands]:
    """Discover all commands across all packages.

    Returns commands grouped by package in discovery order (core first,
    user last). Does not deduplicate - routing determines precedence
    at call time.

    Args:
        mg_root: Root of the mg-managed repository.

    Returns:
        List of PackageCommands in discovery order.
    """
    packages = discover_packages(mg_root)
    return [
        PackageCommands(package=pkg, commands=commands_for_package(pkg))
        for pkg in packages
    ]
