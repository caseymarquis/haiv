"""Testing utilities for mg commands.

These helpers support TDD for mg commands at three levels:

1. routes_to() - Test file structure only (file can be empty)
2. parse() - Test command definition and arg parsing (needs define())
3. execute() - Test full execution (needs define() and execute())

Example command structure:
    commands/
    └── _mind_/                    # param="mind", resolver="mind" (implicit)
        └── message/
            └── _target_as_mind_/  # param="target", resolver="mind" (explicit)
                └── send.py        # mg forge message specs send

Example test:
    from mg import test
    from mg_core import commands

    def test_send_message():
        # Mock resolver for both params - both use "mind" resolver
        def mock_resolve(req: test.ResolveRequest) -> Any:
            # req.resolver is "mind" for both params
            # req.param distinguishes which one ("mind" vs "target")
            # req.value is the raw string ("forge" or "specs")
            return MockMind(name=req.value)

        # Command: mg forge message specs send
        # Captures: mind="forge", target="specs"
        result = test.execute("forge message specs send", commands, resolve=mock_resolve)
        assert "sent" in result.output
"""

from __future__ import annotations

import inspect
import shutil
import tempfile
import weakref
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from punq import Container

from mg import cmd
from mg.args import ResolveRequest, build_ctx
from mg.loader import Command, load_command
from mg.paths import Paths, PkgPaths
from mg.routing import RouteMatch, find_route


class CommandsNotFoundError(Exception):
    """Raised when auto-discovery cannot find a commands module."""

    pass


def _find_commands_module() -> ModuleType:
    """Auto-discover the caller's commands module using PkgPaths."""
    import importlib

    pkg = _find_pkg_paths()

    if not pkg.commands.is_dir():
        raise CommandsNotFoundError(
            f"No commands/ directory found at {pkg.commands}"
        )

    if not (pkg.commands / "__init__.py").exists():
        raise CommandsNotFoundError(
            f"commands/ directory at {pkg.commands} has no __init__.py"
        )

    module_name = f"{pkg.root.name}.commands"
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        raise CommandsNotFoundError(
            f"Failed to import {module_name}: {e}"
        ) from e


@dataclass
class ExecuteResult:
    """Result of execute().

    Use pytest's capsys fixture to capture output if needed.
    """

    ctx: cmd.Ctx


def routes_to(
    command_string: str,
    commands: ModuleType | None = None,
    *,
    expected: str | None = None,
    exists: bool = True,
) -> RouteMatch:
    """
    Test that a command string routes to the expected file.
    """
    if commands is None:
        commands = _find_commands_module()

    result = find_route(command_string, commands)

    if exists:
        if result is None:
            commands_dir = Path(commands.__file__).parent
            raise FileNotFoundError(
                f"No route found for '{command_string}' in {commands_dir}"
            )
        if expected:
            commands_dir = Path(commands.__file__).parent
            actual_relative = result.file.relative_to(commands_dir)
            if str(actual_relative) != expected:
                raise AssertionError(
                    f"Expected route '{expected}', got '{actual_relative}'"
                )
        return result
    else:
        if result is not None:
            raise AssertionError(
                f"Expected no route for '{command_string}', but found {result.file}"
            )
        return RouteMatch(file=None, params={}, rest=[], raw_flags=[])


def parse(
    command_string: str,
    commands: ModuleType | None = None,
    *,
    resolve: Callable[[ResolveRequest], Any] | None = None,
) -> cmd.Ctx:
    """
    Parse a command string and return the context.
    """
    if commands is None:
        commands = _find_commands_module()

    from mg.loader import Command

    route = find_route(command_string, commands)
    if route is None:
        commands_dir = Path(commands.__file__).parent
        raise FileNotFoundError(
            f"No route found for '{command_string}' in {commands_dir}"
        )

    command = load_command(route.file)
    ctx = build_ctx(route, command, resolve=resolve)

    # Register command for run_command to retrieve
    ctx.container.register(Command, instance=command)

    return ctx


def execute(
    command_string: str,
    commands: ModuleType | None = None,
    *,
    container: Container | None = None,
    resolve: Callable[[ResolveRequest], Any] | None = None,
) -> ExecuteResult:
    """
    Execute a command for unit testing.

    Skips setup() and teardown() - only runs execute().
    This is intentional: real dependencies aren't registered,
    so tests must explicitly provide mocks via the container parameter.

    Use pytest's capsys fixture to capture output if needed.
    """
    if commands is None:
        commands = _find_commands_module()

    ctx = parse(command_string, commands, resolve=resolve)
    command = ctx.container.resolve(Command)

    if container is not None:
        ctx.container = container

    command.execute(ctx)

    return ExecuteResult(ctx=ctx)


# =============================================================================
# Sandbox API for integration testing
# =============================================================================


@dataclass
class SandboxConfig:
    """Configuration for test sandboxes.

    Attributes:
        explicit: If True, only specified scaffolding is created.
            If nothing is specified, the sandbox folder will be empty.
        container: Provide mock dependencies in place of the command's setup().
        pkg_root: Package module root directory. If not set, auto-discovered.
    """

    explicit: bool = False
    container: Container | None = None
    pkg_root: Path | None = None


def _find_pkg_paths() -> PkgPaths:
    """Auto-discover the caller's package by walking up from the call site.

    Walks up the call stack to find the first file outside this module,
    then walks up directories to find src/<module>/ with __init__.py.
    """
    # Find caller's file (skip frames in this module)
    this_file = Path(__file__).resolve()
    caller_file = None
    for frame_info in inspect.stack():
        frame_file = Path(frame_info.filename).resolve()
        if frame_file != this_file:
            caller_file = frame_file
            break

    if caller_file is None:
        raise RuntimeError("Could not find caller's file for pkg discovery")

    # Walk up to find directory containing src/
    current = caller_file.parent
    while current != current.parent:
        src_dir = current / "src"
        if src_dir.is_dir():
            # Find module directory with __init__.py
            for child in src_dir.iterdir():
                if child.is_dir() and (child / "__init__.py").exists():
                    return PkgPaths(root=child)
        current = current.parent

    raise RuntimeError(f"Could not find src/<module>/ from {caller_file}")


class Sandbox:
    """Isolated filesystem sandbox for integration testing."""

    def __init__(self, config: SandboxConfig | None = None):
        if config is None:
            config = SandboxConfig()

        self._temp_dir = Path(tempfile.mkdtemp(prefix="mg-test-"))
        self._root = self._temp_dir / "grandparent" / "parent" / "root"
        self._root.mkdir(parents=True)
        self._config = config
        self._cwd = self._root

        # Discover or use provided pkg
        if config.pkg_root is not None:
            pkg = PkgPaths(root=config.pkg_root)
        else:
            pkg = _find_pkg_paths()

        # Create initial context with paths
        container = config.container or Container()
        self._ctx = cmd.Ctx(
            args=cmd.Args(),
            container=container,
            paths=Paths(root=self._root, pkg=pkg),
        )

        # Automatic cleanup when Sandbox is garbage collected
        weakref.finalize(self, self._cleanup)

    def _cleanup(self) -> None:
        """Remove temp directory tree."""
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    @property
    def ctx(self) -> cmd.Ctx:
        """Initial context with paths set (empty args)."""
        return self._ctx

    def run(
        self,
        command: str,
        commands: ModuleType | None = None,
        *,
        setup: bool = False,
        teardown: bool = False,
    ) -> cmd.Ctx:
        """Execute a command in this sandbox.

        Args:
            command: Command string (e.g., "init --force").
            commands: Commands module to route against. Auto-discovered if None.
            setup: If True, run the command's setup() before execute().
            teardown: If True, run the command's teardown() after execute().

        Returns:
            The command's context (with parsed args).
        """
        if commands is None:
            commands = _find_commands_module()

        ctx = parse(command, commands)
        loaded_command = ctx.container.resolve(Command)
        ctx.container = self._ctx.container
        ctx.paths = self._ctx.paths

        if setup:
            loaded_command.setup(ctx)

        try:
            loaded_command.execute(ctx)
        finally:
            if teardown:
                loaded_command.teardown(ctx)

        return ctx

    def cd(self, path: Path | str) -> None:
        """Change current working directory."""
        path = Path(path)
        if path.is_absolute():
            self._cwd = path
        else:
            self._cwd = (self._cwd / path).resolve()


def create_sandbox(config: SandboxConfig | None = None) -> Sandbox:
    """Create an isolated sandbox for integration testing."""
    return Sandbox(config)
