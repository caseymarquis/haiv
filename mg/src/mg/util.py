"""General utilities for mg."""

from pathlib import Path
from types import ModuleType


def module_to_file(module: ModuleType) -> Path:
    """Get a module's file path, raising if unavailable."""
    if module.__file__ is None:
        raise RuntimeError(f"Module {module.__name__} has no __file__")
    return Path(module.__file__)


def module_to_folder(module: ModuleType) -> Path:
    """Get a module's parent directory, raising if unavailable."""
    return module_to_file(module).parent
