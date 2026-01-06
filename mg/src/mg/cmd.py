"""Command types for mg commands."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

from punq import Container

if TYPE_CHECKING:
    from mg.git import Git
    from mg.paths import Paths
    from mg.templates import TemplateRenderer

T = TypeVar("T")

_MISSING = object()


def _missing_or(value: Any) -> Any:
    """Pass through _MISSING, or wrap value in list."""
    return _MISSING if value is _MISSING else [value]


@dataclass
class Flag:
    """Flag definition for command arguments.

    Examples:
        Flag("verbose", type=bool)  # boolean: --verbose
        Flag("file")  # single value (default): --file path.txt
        Flag("reply-to", resolver="message")  # --reply-to msg-123 → Message
        Flag("include", max_args=None)  # one or more: --include a b c
        Flag("tags", min_args=0, max_args=None)  # zero or more: --tags a b c

    Semantics:
        type=bool → boolean flag (presence = True), min/max ignored
        min_args defaults to 1, max_args defaults to 1
    """

    name: str
    type: type = str
    resolver: str | None = None
    min_args: int = 1
    max_args: int | None = 1
    description: str | None = None


@dataclass
class Def:
    """Command definition returned by define()."""

    description: str
    flags: list[Flag] = field(default_factory=list)


class Args:
    """Command arguments - accessed via explicit methods."""

    def __init__(self) -> None:
        self._route: list[str] = []
        self._rest: list[str] = []
        self._values: dict[str, list[Any]] = {}

    @property
    def route(self) -> list[str]:
        """Matched path segments (excluding _rest_)."""
        return self._route

    @property
    def rest(self) -> list[str]:
        """Remaining positional args after route, before flags."""
        return self._rest

    def has(self, name: str) -> bool:
        """Check if argument/flag exists."""
        return name in self._values

    def get_list(
        self, name: str, *, type: type[T] = str, default_value: list[T] | Any = _MISSING
    ) -> list[T]:
        """Get argument as list."""
        if name not in self._values:
            if default_value is not _MISSING:
                return default_value
            raise KeyError(f"Required argument '{name}' not provided")
        # TODO: type casting/validation
        return self._values[name]

    def get_one(
        self, name: str, *, type: type[T] = str, default_value: T | Any = _MISSING
    ) -> T:
        """Get single value. Errors if not exactly one (unless default provided)."""
        result = self.get_list(name, type=type, default_value=_missing_or(default_value))
        if len(result) != 1:
            raise ValueError(f"Expected exactly one '{name}', got {len(result)}")
        return result[0]

    def get_first(
        self, name: str, *, type: type[T] = str, default_value: T | Any = _MISSING
    ) -> T:
        """Get first value. Errors if none (unless default provided)."""
        result = self.get_list(name, type=type, default_value=_missing_or(default_value))
        if len(result) == 0:
            raise ValueError(f"Expected at least one '{name}', got 0")
        return result[0]


@dataclass
class Ctx:
    """Command context passed to execute().

    Attributes:
        args: Parsed command arguments and flags.
        paths: Paths object with called_from, pkg, root, etc.
            - paths.called_from: Always available.
            - paths.pkg: Always available (from command's module location).
            - paths.root, paths.project: Require `mg start`.
        container: Dependency injection container.
    """

    args: Args
    paths: "Paths"
    container: Container = field(default_factory=Container)

    @property
    def git(self) -> "Git":
        """Get a Git instance for the project root."""
        from mg.git import Git

        return Git(self.paths.root)

    @property
    def templates(self) -> "TemplateRenderer":
        """Get a TemplateRenderer for the current package's assets."""
        from mg.templates import TemplateRenderer

        return TemplateRenderer(self.paths.pkg.assets)

    def print(self, text: str = "") -> None:
        """Print output."""
        print(text)
