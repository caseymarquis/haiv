# Routing doesn't handle quoted flag values

**Source:** Mind feedback
**Area:** hv routing/argument parsing

Flag values with quotes aren't being parsed correctly. For example:

```bash
hv users new --name "Casey Smith"
```

The quoted string isn't being handled as a single value.
