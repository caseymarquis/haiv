"""mg: API for building mg commands."""

from mg import cmd, errors, paths, test
from mg.wrappers import git
from mg._infrastructure import resolvers
from punq import Container

__version__ = "0.1.0"

__all__ = ["cmd", "errors", "git", "paths", "resolvers", "test", "Container"]
