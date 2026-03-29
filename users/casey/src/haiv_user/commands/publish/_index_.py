"""hv publish - Publishing workflow for haiv packages."""

from haiv import cmd


def define() -> cmd.Def:
    return cmd.Def(description="Publishing workflow for haiv packages")


def execute(ctx: cmd.Ctx) -> None:
    ctx.print("Publishing Workflow")
    ctx.print("=" * 40)
    ctx.print()
    ctx.print("All packages are versioned and published together.")
    ctx.print("Publish order (dependency order):")
    ctx.print()
    ctx.print("  1. hv publish haiv-lib")
    ctx.print("  2. hv publish haiv-core")
    ctx.print("  3. hv publish haiv-cli")
    ctx.print("  4. hv publish haiv-tui")
    ctx.print("  5. hv publish haiv")
    ctx.print()
    ctx.print("Before publishing:")
    ctx.print()
    ctx.print("  1. Bump version in all pyproject.toml files")
    ctx.print("     (haiv-lib, haiv-core, haiv-cli, haiv-tui, haiv)")
    ctx.print("  2. Run `uv lock` to update the lock file")
    ctx.print("  3. Commit the version bump")
    ctx.print("  4. Tag: git tag v0.X.0")
    ctx.print("  5. Push: git push origin main v0.X.0")
    ctx.print("  6. Run each publish command above in order")
    ctx.print()
    ctx.print("Versioning:")
    ctx.print("  - Minor bump (0.2 -> 0.3) for new features or breaking changes")
    ctx.print("  - Patch bump (0.2.0 -> 0.2.1) for bug fixes")
    ctx.print("  - All packages share the same version")
    ctx.print("  - Once we have real users, breaking changes require a major bump")
    ctx.print()
    ctx.print("Each publish command checks for a tag at HEAD and")
    ctx.print("refuses to publish without one. Use --dry-run to")
    ctx.print("build without publishing.")
