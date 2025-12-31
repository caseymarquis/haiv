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
        container: Dependency injection container.
        called_from: Directory where the command was invoked.
            Always available. Use this for commands that operate on the
            caller's directory (like `init`).
        paths: Paths within an mg project.
            - paths.pkg: Set dynamically based on the command's location.
              Works without `mg start` for core commands.
            - paths.root, paths.project, paths.user: Require `mg start`.

    TODO: Refactor so that `paths` is computed from explicit base fields (root, pkg_root).
    All base fields should be required parameters (even if set to None) to make
    construction explicit. Currently paths is set directly which is error-prone.
    """

    args: Args
    container: Container = field(default_factory=Container)
    called_from: "Path | None" = None
    paths: "Paths | None" = None

    @property
    def git(self) -> "Git":
        """Get a Git instance for the project root."""
        from mg.git import Git

        if self.paths is None:
            raise RuntimeError("Cannot access git: paths not set")
        return Git(self.paths.root)

    @property
    def templates(self) -> "TemplateRenderer":
        """Get a TemplateRenderer for the current package's assets."""
        from mg.templates import TemplateRenderer

        if self.paths is None:
            raise RuntimeError("Cannot access templates: paths not set")
        return TemplateRenderer(self.paths.pkg.assets)

    def print(self, text: str = "") -> None:
        """Print output."""
        print(text)
