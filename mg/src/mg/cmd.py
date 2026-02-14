"""Command types for mg commands."""

from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, overload

from punq import Container

from mg._infrastructure.mg_hooks import MgHookRegistry
from mg._infrastructure.settings import SettingsCache, get_settings
from mg.helpers.tui import Tui
from mg.helpers.tui.TuiClient import TuiClient
from mg.paths import Paths
from mg.settings import MgSettings
from mg.templates import TemplateRenderer
from mg.wrappers.git import Git

T = TypeVar("T")
U = TypeVar("U")

_MISSING = object()


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
    type: builtins.type = str
    resolver: str | None = None
    min_args: int = 1
    max_args: int | None = 1
    description: str | None = None


@dataclass
class Def:
    """Command definition returned by define()."""

    description: str
    flags: list[Flag] = field(default_factory=list)
    enable_mg_hooks: bool = False


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

    def _get_values(self, name: str, default: Any = _MISSING) -> list[Any]:
        """Internal: Get raw values for a name, or default if missing.

        Raises KeyError if name not found and no default provided.
        """
        if name in self._values:
            return self._values[name]
        if default is not _MISSING:
            return default if isinstance(default, list) else [default]
        raise KeyError(f"Required argument '{name}' not provided")

    # --- get_list() ---

    @overload
    def get_list(self, name: str) -> list[str]: ...
    @overload
    def get_list(self, name: str, *, default_value: U) -> U: ...
    @overload
    def get_list(self, name: str, *, type: type[T]) -> list[T]: ...
    @overload
    def get_list(self, name: str, *, type: type[T], default_value: U) -> list[T] | U: ...

    def get_list(self, name, *, type=str, default_value=_MISSING):
        """Get argument as list.

        Examples:
            names = ctx.args.get_list("names")  # list[str]
            counts = ctx.args.get_list("counts", type=int)  # list[int]
            tags = ctx.args.get_list("tags", default_value=[])  # []
        """
        return self._get_values(name, default_value)

    # --- get_one() ---

    @overload
    def get_one(self, name: str) -> str: ...
    @overload
    def get_one(self, name: str, *, default_value: U) -> U: ...
    @overload
    def get_one(self, name: str, *, type: type[T]) -> T: ...
    @overload
    def get_one(self, name: str, *, type: type[T], default_value: U) -> T | U: ...

    def get_one(self, name, *, type=str, default_value=_MISSING):
        """Get single value. Errors if not exactly one (unless default provided).

        Examples:
            name = ctx.args.get_one("name")  # str
            mind = ctx.args.get_one("mind", type=Mind)  # Mind
            reply = ctx.args.get_one("reply", type=Message, default_value=None)  # Message | None
        """
        values = self._get_values(name, [default_value] if default_value is not _MISSING else _MISSING)
        if len(values) != 1:
            raise ValueError(f"Expected exactly one '{name}', got {len(values)}")
        return values[0]

    # --- get_first() ---

    @overload
    def get_first(self, name: str) -> str: ...
    @overload
    def get_first(self, name: str, *, default_value: U) -> U: ...
    @overload
    def get_first(self, name: str, *, type: type[T]) -> T: ...
    @overload
    def get_first(self, name: str, *, type: type[T], default_value: U) -> T | U: ...

    def get_first(self, name, *, type=str, default_value=_MISSING):
        """Get first value. Errors if none (unless default provided).

        Examples:
            name = ctx.args.get_first("name")  # str
            mind = ctx.args.get_first("mind", type=Mind)  # Mind
        """
        values = self._get_values(name, [default_value] if default_value is not _MISSING else _MISSING)
        if len(values) == 0:
            raise ValueError(f"Expected at least one '{name}', got 0")
        return values[0]


@dataclass
class Ctx:
    """Command context passed to execute().

    Attributes:
        args: Parsed command arguments and flags.
        paths: Paths object. See mg/paths.py for details.
        container: Dependency injection container.
        _mg_hook_registry: MgHookRegistry for mg hook dispatch (set when enable_mg_hooks=True).
    """

    args: Args
    paths: Paths
    container: Container = field(default_factory=Container)
    _mg_hook_registry: MgHookRegistry | None = field(default=None, repr=False)
    _settings_cache: SettingsCache = field(default_factory=SettingsCache)
    _tui: Tui | None = field(default=None, repr=False)

    @property
    def settings(self) -> MgSettings:
        """Get project settings (merged with user settings if available)."""
        return get_settings(self.paths, self._settings_cache)

    @property
    def git(self) -> Git:
        """Get a Git instance for the project root."""
        return Git(self.paths.root)

    @property
    def tui(self) -> Tui:
        """Get a Tui instance for this project."""
        if self._tui is None:
            self._tui = Tui(
                self.paths.root,
                self.settings,
                client=TuiClient(self.paths.root.name),
                sessions_file=self.paths.user.sessions_file,
            )
        return self._tui

    @property
    def templates(self) -> TemplateRenderer:
        """Get a TemplateRenderer for the current package's assets."""
        return TemplateRenderer(self.paths.pkgs.current.assets_dir)

    @property
    def mind(self) -> MindNS:
        """Namespace for structured communication with the running mind."""
        return MindNS(self.print)

    def print(self, text: str = "") -> None:
        """Print output."""
        print(text)


class MindNS:
    """Helpful patterns for collaborating with the mind running a command.

    Accessed via ``ctx.mind``.
    """

    def __init__(self, print_fn: Callable[[str], None]) -> None:
        self._print = print_fn

    _DEFAULT_PREAMBLE = (
        "Create a task for each item before starting any work. "
        "Give each task genuine consideration \u2014 don't skip or rush "
        "through items that feel obvious."
    )

    def checklist(
        self,
        items: list[str],
        *,
        preamble: str | None = _DEFAULT_PREAMBLE,
        postamble: str | None = None,
    ) -> None:
        """Present a checklist for the mind to work through.

        Args:
            items: The checklist items.
            preamble: Guidance printed before the list. Defaults to
                standard task-creation encouragement. Pass None to omit.
            postamble: Optional context printed after the list.
        """
        if preamble:
            self._print(preamble)
            self._print("")

        for i, item in enumerate(items, 1):
            self._print(f"  {i}. {item}")

        if postamble:
            self._print("")
            self._print(postamble)
