"""hv publish haiv-cli - Build and publish haiv-cli to PyPI."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(
        description="Build and publish haiv-cli to PyPI",
        flags=[
            cmd.Flag("dry-run", type=bool, description="Build only, don't publish"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    import importlib.util

    helper_path = ctx.paths.pkgs.user.commands_dir / "publish" / "__init__.py"
    spec = importlib.util.spec_from_file_location("_publish_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    package_dir = ctx.paths.worktrees_dir / "main" / "haiv-cli"
    helper.publish_package(package_dir, dry_run=ctx.args.has("dry-run"), print_fn=ctx.print)
