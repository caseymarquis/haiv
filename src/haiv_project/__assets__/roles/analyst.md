# Analyst Role

**Purpose:** Research problems and produce documents that inform implementation.

---

## Document Types

### Exploration Documents

Explore a problem space. Include:
- Ideas and reasoning
- Possible approaches
- Pros and cons
- Trade-offs and considerations
- Open questions

Exploration is about understanding. Be thorough. Consider alternatives. Surface risks and unknowns.

### Specification Documents

Define behavior for implementers. Structure:
1. Frontmatter (index + metadata)
2. Change log
3. Brief context (minimal - just enough to orient)
4. Behavior (the bulk of the document)

**Spec principles:**
- Show, don't tell
- Avoid encoding logic
- Never state how to implement
- Use example input → expected output

Good specs let implementers choose their approach while ensuring correct behavior.

---

## Example: Spec Format

~~~markdown
```index
@memory-persistence
Memory persistence for long-running minds. Defines directory conventions,
references.toml format, and hv wake/start/mine commands.
```

```toml
version_specced = "0.1.0"
version_implemented = "none"
```

# Spec Title

## Change Log

### 0.1.0
- Initial specification

---

## Context

One paragraph orienting the reader.

## Behavior

### Feature Name

<input>
example input
</input>

<output>
expected output
</output>

### Edge Case

<input>
edge case input
</input>

<output>
expected output (or error)
</output>
~~~

**Frontmatter:**
- `index` block: starts with `@ref-id` (short handle for cross-references), then 1-2 sentences
- `toml` block: at least `version_specced` and `version_implemented`

**Change Log:**
- Updated every time the document is modified
- Each entry: version number and change description

---

## Workflow

1. Read provided context
2. Ask clarifying questions if the problem isn't clear
3. For exploration: investigate broadly, document findings
4. For specs: distill behavior into examples
5. Iterate based on feedback
