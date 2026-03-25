<!-- ch-project-context:start -->
## Documentation

| Directory | Purpose |
|-----------|---------|
| `docs/exec-plans/active/` | Active execution plans (current work) |
| `docs/exec-plans/completed/` | Completed plans (archive) |
| `docs/decisions/` | Architecture/design decision records |
| `docs/research/` | Research findings and investigations |
| `docs/known-issues/` | Active known issues and pitfalls |
| `docs/known-issues/resolved/` | Resolved issues (kept for reference) |
| `docs/archive/` | Frozen project artifacts (PRD, specs, etc.) |

### Context Automation

- **Session-start hook**: Auto-injects active plans, known issues, and workflow rules at session start (no output when all sources are empty)
- **Subagent-context hook** (PreToolUse): Enriches subagent prompts with the same project context, so spawned agents know about active plans and issues without relying on the dispatcher
- **Frontmatter convention**: Every doc file uses YAML frontmatter (title, description, status, related) for hook parsing

### Document Lifecycle

- New plans go in `exec-plans/active/`, move to `completed/` when done
- New issues go in `known-issues/`, move to `resolved/` when fixed
- Decisions and research are permanent (one file per topic, 30-100 lines)

### Why docs/, Not Memory

This project uses a structured `docs/` system instead of Claude Code's memory for project state. Do not duplicate docs content into memory or maintain parallel tracking.

| Concern | docs/ system | Memory |
|---------|-------------|--------|
| Structure | Frontmatter + templates, typed directories | Flat key-value, no schema |
| Lifecycle | `active/` → `completed/`, `active` → `resolved/` | None — manual cleanup |
| Cross-agent handoff | exec-plan phases + handoff notes | Cannot express "agent A finished phase 1, agent B starts phase 2" |
| Discoverability | Directory structure + session-start hook auto-injection | MEMORY.md index, 200-line truncation |

**Memory as companion**: Memory is useful as a **hot cache and pointer layer** for docs — e.g., "current highest-priority plan is X, in phase 2" — plus personal preferences and lightweight cross-session notes. But memory must never expand into details; the detail lives in `docs/` as the single source of truth.

**On init in existing projects**: If the project already has progress tracking or issue logs in memory, migrate them into the corresponding `docs/` directories, then remove the redundant memory entries. Do not maintain two parallel systems.

### Writing New Content

**Doc vs Skill**: `docs/` is for reference knowledge (architecture, decisions, research, known issues). Operational runbooks (local-dev setup, deploy procedures, troubleshooting playbooks) should be skills — they are triggerable, executable, and carry runtime context. If you're writing a step-by-step guide, it's probably a skill, not a doc.

**workflow.md**: Optional team workflow rules file in `docs/`. Create it when there are conventions that all agents must follow (branching strategy, review process, naming conventions). The session-start hook auto-injects its content. If no team-specific rules exist, don't create it.

**Adding docs**: Every file in `docs/` uses YAML frontmatter:

```yaml
---
title: Short descriptive title
description: One-line summary (what + why)
status: active | completed | draft | superseded-by <ID>
date: YYYY-MM-DD
---
```

Naming: decisions use `D001-short-name.md`, issues use `I001-short-name.md`, research uses descriptive names, exec-plans use `docs/exec-plans/active/<feature>/plan.md`.
<!-- ch-project-context:end -->
