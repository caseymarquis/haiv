"""Create a new user directory with standard haiv structure."""

import re
import tomllib
from dataclasses import fields
from pathlib import Path

import tomli_w

from haiv import cmd
from haiv.errors import CommandError
from haiv._infrastructure.identity import CurrentEnv, get_current_env


# Valid name pattern: starts with letter, then alphanumeric/hyphen/underscore
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")


def define() -> cmd.Def:
    """Define the users new command."""
    return cmd.Def(
        description="Create a new user directory",
        flags=[
            cmd.Flag("name"),
            cmd.Flag("replace", type=bool),
            cmd.Flag("merge", type=bool),
            cmd.Flag("quiet", type=bool),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    """Execute the users new command."""
    name = ctx.args.get_one("name")
    replace = ctx.args.has("replace")
    merge = ctx.args.has("merge")
    quiet = ctx.args.has("quiet")

    # Validate flags
    if replace and merge:
        raise CommandError("--replace and --merge are mutually exclusive")

    # Validate name
    _validate_name(name)

    # Check if user exists
    user_dir = ctx.paths.users_dir / name
    identity_file = user_dir / "identity.toml"

    if user_dir.exists():
        if not (replace or merge):
            raise CommandError(f"User '{name}' already exists. Use --replace or --merge to update.")
        # For replace/merge, we only update identity.toml
        _update_identity(identity_file, replace=replace, merge=merge)
        if not quiet:
            mode = "replaced" if replace else "merged"
            ctx.print(f"Identity {mode} for user '{name}'")
        return

    # Create new user structure
    _create_user_structure(ctx, user_dir)

    if not quiet:
        ctx.print(f"Created user '{name}'")
        ctx.print(f"  {user_dir}/")


def _validate_name(name: str) -> None:
    """Validate user name format."""
    if not name:
        raise CommandError("Name cannot be empty")

    if name != name.lower():
        raise CommandError("Name must be lowercase")

    if not name[0].isalpha():
        raise CommandError("Name must start with a letter")

    if not NAME_PATTERN.match(name):
        raise CommandError(
            "Name must be alphanumeric with hyphens/underscores only"
        )


def _create_user_structure(ctx: cmd.Ctx, user_dir: Path) -> None:
    """Create the full user directory structure."""
    # Create directories
    user_dir.mkdir(parents=True)
    (user_dir / "src" / "hv_user" / "commands").mkdir(parents=True)
    (user_dir / "state").mkdir(parents=True)

    # Write templates
    ctx.templates.write("users/pyproject.toml.j2", user_dir / "pyproject.toml")
    ctx.templates.write(
        "users/src/hv_user/__init__.py.j2",
        user_dir / "src" / "hv_user" / "__init__.py",
    )
    ctx.templates.write(
        "users/src/hv_user/commands/__init__.py.j2",
        user_dir / "src" / "hv_user" / "commands" / "__init__.py",
    )
    ctx.templates.write("users/state/.gitkeep.j2", user_dir / "state" / ".gitkeep")

    # Generate identity.toml from current environment
    _write_identity(user_dir / "identity.toml")


def _write_identity(path: Path) -> None:
    """Write identity.toml from current environment."""
    env = get_current_env()
    match_config = _env_to_match_config(env)

    data = {"match": match_config}
    path.write_bytes(tomli_w.dumps(data).encode())


def _env_to_match_config(env: CurrentEnv) -> dict[str, list[str]]:
    """Convert CurrentEnv to match config dict."""
    config: dict[str, list[str]] = {}
    for f in fields(CurrentEnv):
        value = getattr(env, f.name)
        if value is not None:
            config[f.name] = [value]
    return config


def _update_identity(path: Path, *, replace: bool, merge: bool) -> None:
    """Update existing identity.toml."""
    env = get_current_env()
    new_config = _env_to_match_config(env)

    if replace:
        # Overwrite with new config
        data = {"match": new_config}
        path.write_bytes(tomli_w.dumps(data).encode())
    elif merge:
        # Merge new values into existing
        existing: dict[str, list[str]] = {}
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
                existing = data.get("match", {})

        # Add new values that don't exist
        for key, values in new_config.items():
            if key not in existing:
                existing[key] = []
            for v in values:
                # Case-insensitive duplicate check
                if not any(v.casefold() == e.casefold() for e in existing[key]):
                    existing[key].append(v)

        data = {"match": existing}
        path.write_bytes(tomli_w.dumps(data).encode())
