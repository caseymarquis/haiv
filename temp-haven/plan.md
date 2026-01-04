# Haven's Plan: Onboarding System

**Goal:** Build a system where Haven receives delegation requests and produces ready-to-use welcome docs for new minds.

---

## The Flow

```
Request (vague) → Haven evaluates → Clarify if needed → Welcome Doc → New Mind
```

1. Someone (Wren, human) sends a request - may be vague
2. Haven evaluates: what do I know, what's missing?
3. If gaps, Haven states what's needed; human fills in
4. Haven builds a templated welcome doc
5. New mind is spawned and pointed at the welcome doc

---

## Deliverables

### 1. Intake Checklist
- [ ] `temp-haven/intake-checklist.md` - Questions Haven asks when evaluating a request
- What's the goal? What does success look like?
- Who is this for? (dev, researcher, etc.)
- What context docs are relevant?
- Where does the work happen?

### 2. Welcome Doc Templates
- [ ] Templates for different task types (dev, research, etc.)
- Include relevant context based on task type
- Single entry point - no separate orientation doc needed

### 3. Role Definitions
- [ ] Evaluate and improve existing roles
- Create new roles as task types emerge

---

## Current Status

**Next action:** Create the intake checklist

---

## Open Questions

- What role types do we need beyond generalist?
- What templates make sense? (dev task, research task, ongoing role?)
