"""General utilities for haiv."""

import shlex
import subprocess
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


def shell_quote(s: str) -> str:
    """Quote a string for the current platform's shell."""
    if sys.platform == "win32":
        return subprocess.list2cmdline([s])
    return shlex.quote(s)


def shell_join(args: list[str]) -> str:
    """Join a command list into a shell string for the current platform."""
    if sys.platform == "win32":
        return subprocess.list2cmdline(args)
    return shlex.join(args)


def module_to_file(module: ModuleType) -> Path:
    """Get a module's file path, raising if unavailable."""
    if module.__file__ is None:
        raise RuntimeError(f"Module {module.__name__} has no __file__")
    return Path(module.__file__)


def module_to_folder(module: ModuleType) -> Path:
    """Get a module's parent directory, raising if unavailable."""
    return module_to_file(module).parent


class Atom(Generic[T]):
    """Thread-safe wrapper for a single value.

    Encapsulates a lock so callers can't forget to acquire/release.
    Use for values shared across threads.

    Usage:
        counter = Atom(0)
        counter.value = 5           # atomic write
        x = counter.value           # atomic read
        y = counter.modify(lambda n: n + 1)  # atomic read-modify-write
    """

    def __init__(self, value: T) -> None:
        self._lock = threading.Lock()
        self._value = value

    @property
    def value(self) -> T:
        """Read the value atomically."""
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        """Write the value atomically."""
        with self._lock:
            self._value = new_value

    def modify(self, fn: Callable[[T], T]) -> T:
        """Apply a transformation atomically, returning the new value."""
        with self._lock:
            self._value = fn(self._value)
            return self._value
