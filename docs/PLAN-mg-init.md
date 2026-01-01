# Plan: mg init Structure

**Date:** 2024-12-31

---

## Questions to Resolve

### 1. .claude/ directory
Simple folder creation. **Add to init.**

### 2. pyproject.toml + src/mg_project/ + tests/
- Init creates working package structure?
- Or scaffolding that another command guides through?
- Need template supporting easy command → package extraction

### 3. Scope documentation
- src/mg_project/ and tests/ shared across all users
- CLAUDE.md needs "common commands" section
- Comments in pyproject.toml and tests/ explaining scope

### 4. Example test
- Provide passing test demonstrating TDD pattern
- Sets expectations for command development

### 5. Command scaffolding (separate command?)
- `mg command new --user/--project`
- Strongly encourage TDD - scaffold includes test
- Not part of init

### 6. Command promotion (user → project → package)
- Watch for friction
- Manifest file consideration?

### 7. users/ folder
- Init creates `users/`
- `mg start` detects/creates first user

---

## Discussion

