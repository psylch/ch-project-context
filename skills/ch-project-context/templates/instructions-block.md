<!-- ch-project-context:start -->
## Documentation

| Directory | Purpose |
|-----------|---------|
| `docs/exec-plans/pending/` | Planned work not yet started |
| `docs/exec-plans/active/` | Active execution plans (current work) |
| `docs/exec-plans/completed/` | Completed plans (archive) |
| `docs/decisions/` | Architecture/design decision records |
| `docs/research/` | Research findings and investigations |
| `docs/known-issues/` | Active known issues and pitfalls |
| `docs/known-issues/resolved/` | Resolved issues (kept for reference) |
| `docs/archive/` | Frozen project artifacts (PRD, specs, etc.) |

### Context Automation

- **Session-start hook**: Auto-injects active plans, known issues, and workflow rules at session start.
- **Subagent-start hook**: Gives spawned agents the same project context without relying on the dispatcher.
- **Frontmatter convention**: Every doc file uses YAML frontmatter (`title`, `description`, `status`, `date`) for hook parsing.
- Hooks return no output when all context sources are empty.

### Document Lifecycle

- Planned work goes in `exec-plans/pending/`, moves to `active/` when started, then to `completed/` when done.
- New issues go in `known-issues/`, then move to `resolved/` when fixed.
- Decisions and research are permanent: use one focused file per topic.

### Source of Truth

Use `docs/` as the durable source of truth for project state. Agent memory may keep lightweight pointers and personal preferences, but it must not duplicate plan, decision, issue, or research details.

### Writing New Content

- Put reference knowledge—architecture, decisions, research, and known issues—in `docs/`.
- Put operational runbooks in reusable skills when practical.
- Create `docs/workflow.md` only when the team has workflow rules that every agent should receive.
- Use this frontmatter on files in `docs/`:

```yaml
---
title: Short descriptive title
description: One-line summary (what + why)
status: active | completed | draft | superseded-by <ID>
date: YYYY-MM-DD
---
```

Naming: decisions use `D001-short-name.md`, issues use `I001-short-name.md`, research uses descriptive names, and exec plans use `docs/exec-plans/active/<feature>/plan.md`.

### Language

**Document content language: {lang}**. Write doc body text in this language. Keep frontmatter keys, directory names, file naming patterns, and hook code in English.
<!-- ch-project-context:end -->
