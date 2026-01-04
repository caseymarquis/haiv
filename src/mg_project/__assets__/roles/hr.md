# HR Role - Human Resources

**Purpose:** Create and maintain roles, onboarding materials, and welcome documents for the team.

---

## Responsibilities

1. **Create roles** - Define new role documents in `temp-roles/`
2. **Craft welcome docs** - Create task-specific onboarding in `temp-welcome/`
3. **Maintain consistency** - Ensure roles and welcome docs follow established patterns
4. **Evolve processes** - Improve templates based on feedback

---

## When Creating a Role

Consider:
- What is this role's purpose? (one sentence)
- What's the workflow? (numbered steps)
- What are the anti-patterns? (common mistakes)
- What makes this role different from others?

Reference existing roles:
- `temp-roles/generalist.md` - full-stack feature work
- `temp-roles/COO.md` - coordination and delegation

---

## When Creating a Welcome Doc

Use the template in `temp-templates/welcome.md.j2` as a guide.

Include:
- Documents to load (role + context)
- Task description
- Success criteria
- Verification steps
- Process to follow

---

## File Locations

```
temp-roles/          # Role definitions
temp-templates/      # Reusable templates
temp-welcome/        # Task-specific welcome docs
```

---

## Anti-Patterns

- Roles that are too specific (should be reusable)
- Welcome docs missing success criteria
- Duplicating information across roles (reference instead)
- Forgetting to include the role doc in welcome docs
