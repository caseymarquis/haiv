# Publishing

## Packages

All haiv packages are published to PyPI and share the same version number. They form a dependency chain:

```
haiv-lib          (leaf — no haiv deps)
haiv-core       → haiv-lib
haiv-cli        → haiv-core, haiv-mail
haiv-tui        → haiv-lib
haiv (meta)     → haiv-cli, haiv-tui
```

**haiv-mail** is developed in a separate colony and published independently. haiv-cli pins it with `>=0.3.0,<1` — any minor/patch within the 0.x series.

## Dependency Model

- **Project and user packages** depend only on `haiv-lib` (the command API). They get it from PyPI.
- **This repo** (where we develop haiv-lib) overrides with a local editable via `[tool.uv.sources]`.
- **Templates** (`hv init`, `hv users new`) generate pyproject.toml files that pin `haiv-lib>=<current>,<next-major>` using the installed version at creation time.

## Versioning

- **Patch** (0.3.0 → 0.3.1): bug fixes, dependency bumps
- **Minor** (0.2 → 0.3): new features, breaking changes while pre-1.0
- **Major**: reserved for when we have real users — breaking changes after 1.0

All packages bump together. No mixed versions.

## Process

Run `hv publish` for the full checklist. Summary:

1. Bump `version` in all 5 pyproject.toml files (haiv-lib, haiv-core, haiv-cli, haiv-tui, haiv)
2. `uv lock`
3. Commit the bump
4. `git tag v0.X.Y`
5. `git push origin main v0.X.Y`
6. Publish in dependency order:
   - `hv publish haiv-lib`
   - `hv publish haiv-core`
   - `hv publish haiv-cli`
   - `hv publish haiv-tui`
   - `hv publish haiv`

Each publish command refuses to run without a tag at HEAD.

## Pulling External Updates

When haiv-mail (or future external packages) releases a new version:

1. `uv lock --upgrade-package haiv-mail`
2. Bump all haiv versions (patch)
3. Tag, push, publish as above
