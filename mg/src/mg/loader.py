"""Command loader for mg.

Loads Python command modules from file paths and wraps them in a Command
class that provides a consistent interface with virtual methods for
optional lifecycle functions.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

from mg import cmd


class Command:
    """Wrapper around a command module providing consistent lifecycle interface.

    Required module functions:
        define() -> cmd.Def
        execute(ctx: cmd.Ctx) -> None

    Optional module functions (no-op if absent):
        setup(ctx: cmd.Ctx) -> None
        teardown(ctx: cmd.Ctx) -> None
    """

    def __init__(self, module: ModuleType) -> None:
        self._module = module

    def define(self) -> cmd.Def:
        """Return command definition. Raises AttributeError if missing."""
        return self._module.define()

    def setup(self, ctx: cmd.Ctx) -> None:
        """Run setup if defined, otherwise no-op."""
        if hasattr(self._module, "setup"):
            self._module.setup(ctx)

    def execute(self, ctx: cmd.Ctx) -> None:
        """Run command. Raises AttributeError if missing."""
        self._module.execute(ctx)

    def teardown(self, ctx: cmd.Ctx) -> None:
        """Run teardown if defined, otherwise no-op."""
        if hasattr(self._module, "teardown"):
            self._module.teardown(ctx)


def load_command(file: Path) -> Command:
    """Load a command module from a .py file.

    Args:
        file: Path to the .py file

    Returns:
        Command wrapper around the loaded module

    Raises:
        FileNotFoundError: If file doesn't exist
        SyntaxError: If file contains invalid Python
    """
    if not file.exists():
        raise FileNotFoundError(f"Command file not found: {file}")

    # Create a unique module name to avoid caching
    module_name = f"mg_command_{file.stem}_{id(file)}"

    spec = importlib.util.spec_from_file_location(module_name, file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return Command(module)
