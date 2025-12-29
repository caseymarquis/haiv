# mind-games

Seamless management of a collaborative AI team, optimizing for the bottleneck constraint of expert-level human attention.

## Package Structure

```
mind-games (PyPI)     CLI tool - users install this
    └── mg-core      Core commands (git dependency)
            └── mg   API for building commands (git dependency)
```

| Package | Directory | Module | Purpose |
|---------|-----------|--------|---------|
| `mind-games` | `mind-games/` | `mind-games` | CLI entry point |
| `mg-core` | `mg-core/` | `mg_core` | Core commands |
| `mg` | `mg/` | `mg` | Public API for command authors |

Dependencies flow: `mind-games → mg-core → mg`

Only `mind-games` is published to PyPI. Internal packages are pulled via git.

## Development

```bash
uv sync        # install/update dependencies
uv run pytest  # run tests
uv run mg      # run CLI
```

## License

MIT
