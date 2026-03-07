# Flag descriptions in command definitions

**Source:** Mind feedback
**Area:** hv command framework

Command flags should have a "description" field that explains what they do. Currently only the flag name is defined.

```python
# Current
cmd.Def(
    flags=[cmd.Flag("--force"), cmd.Flag("--name")]
)

# Desired
cmd.Def(
    flags=[
        cmd.Flag("--force", description="Overwrite existing files"),
        cmd.Flag("--name", description="Name for the new user directory"),
    ]
)
```
