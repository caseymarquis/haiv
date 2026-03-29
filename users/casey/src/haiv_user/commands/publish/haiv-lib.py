"""hv publish haiv-lib - Build and publish haiv-lib to PyPI."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Build and publish haiv-lib to PyPI",
        flags=[
            cmd.Flag("dry-run", type=bool, description="Build only, don't publish"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    import importlib.util
    import sys

    # Load the publish helper from the same directory
    helper_path = ctx.paths.pkgs.user.commands_dir / "publish" / "__init__.py"
    spec = importlib.util.spec_from_file_location("_publish_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    package_dir = ctx.paths.worktrees_dir / "main" / "haiv-lib"
    helper.publish_package(package_dir, dry_run=ctx.args.has("dry-run"), print_fn=ctx.print)
