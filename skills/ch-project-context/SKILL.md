---
name: ch-project-context
description: "Initialize a project-level context management system with docs/ directory structure, Claude Code hooks for automatic context injection (session-start + subagent PreToolUse), and CLAUDE.md navigation. Use when starting a new project, bootstrapping context management, or when the user says '/ch-project-context init', 'init project context', 'setup context management', 'initialize docs structure'."
---

# ch-project-context

One-command initialization of a project-level context management system for Claude Code agents.

## What It Does

Creates a structured `docs/` directory, installs Claude Code hooks for automatic context injection (session-start + subagent enrichment), and wires everything into `.claude/settings.json` and `CLAUDE.md`.

## When to Use

- Starting a new project that will use Claude Code agents
- Bootstrapping context management in an existing project that lacks it
- User says `/ch-project-context init` or similar

## Instructions

### Step 0: Assess Project Type

Before doing anything, determine whether this project actually needs the full context management system. Ask these three questions:

| Signal | Yes → Full mechanism | No → Lightweight |
|--------|---------------------|-------------------|
| **Multi-agent handoff** — Will multiple agents or people take turns working on this? | Exec-plans track phases and handoff notes | No handoff = no state to pass |
| **Cross-session state continuity** — Does work span many sessions where context could drift? | Session-start hook auto-injects "where we left off" | Single-session work = no drift risk |
| **Work item lifecycle > few days** — Do individual tasks live long enough to accumulate decisions and issues? | Decisions/known-issues directories earn their keep | Short tasks = overhead > value |

**If all three are "No"**: This is an **atomic work collection** (e.g., a workspace of independent small projects, a skill collection, a monorepo of micro-tools). The full mechanism is over-engineering. Instead, recommend:

```
[ch-project-context] This project doesn't need the full context system.

For atomic work collections, these are sufficient:
  1. A well-written CLAUDE.md with project structure and workflow conventions
  2. Batch operation SOPs (review/fix/verify flows) documented in CLAUDE.md
  3. Claude Code's memory system for cross-session context

No docs/ directory, no hooks, no frontmatter needed.
```

Then **stop** — do not proceed to Step 1.

**If one or more are "Yes"**: Proceed with the full init below.

### Step 1: Detect Project Root

Resolve the project root directory. Use the current working directory. Verify it looks like a project root (has `.git/`, `package.json`, `Cargo.toml`, `pyproject.toml`, or similar). If unsure, confirm with the user.

### Step 2: Check Existing State

Before running init, check what already exists:
- If `docs/` exists with content, warn the user and ask whether to merge (skip existing dirs) or abort
- If `.claude/hooks/` already has hook files, warn and ask whether to overwrite or skip
- If `.claude/settings.json` exists, merge hook entries rather than overwriting

### Step 3: Run Init Script

Run the init script to create the directory structure and hook files:

```bash
python3 {SKILL_DIR}/scripts/init.py --root <project-root>
```

Where `{SKILL_DIR}` is the directory containing this SKILL.md. Resolve at runtime.

The script outputs JSON:
```json
{
  "status": "ok",
  "created": ["docs/exec-plans/active/", "docs/decisions/", ...],
  "skipped": ["docs/research/"],
  "hooks_installed": ["session-start.py", "subagent-context.py"],
  "settings_updated": true
}
```

### Step 4: Update CLAUDE.md

After the script succeeds, update CLAUDE.md:

**If CLAUDE.md exists**: Append the docs navigation block at the end (read the file first to avoid duplicating if the block already exists -- check for `<!-- ch-project-context -->` marker).

**If CLAUDE.md does not exist**: Create a minimal CLAUDE.md with project name (inferred from directory name or package.json) and the docs navigation block.

The navigation block to append (between markers):

```markdown
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
```

### Step 5: Create Architecture Skeleton (Optional)

If `docs/architecture.md` does not exist, create it with a frontmatter template:

```markdown
---
title: Architecture Overview
description: High-level system architecture and key design decisions
status: draft
date: {TODAY}
---

# Architecture Overview

<!-- Replace this with your project's architecture description -->

## System Components

## Key Design Decisions

## Data Flow
```

### Step 6: Report

Present a summary:

```
[ch-project-context] Initialized!

Project: <name>
Root: <path>

Created:
  <list of created dirs/files>

Skipped (already existed):
  <list if any>

Hooks installed:
  - .claude/hooks/context.py (shared context builder)
  - .claude/hooks/session-start.py (SessionStart)
  - .claude/hooks/subagent-context.py (PreToolUse → Task/Agent)

Next Steps:
  1. Edit docs/architecture.md to describe your system
  2. Create your first exec-plan: docs/exec-plans/active/<feature>/plan.md
  3. Optionally create docs/workflow.md for team workflow rules
  4. The session-start hook will auto-inject context on every new session

If this is an existing project with code but no documentation:
  → Analyze the codebase and populate docs/ automatically.
    Read the code, infer architecture, key decisions, and known issues,
    then write docs/architecture.md, docs/decisions/, and docs/known-issues/
    following the templates in references/conventions.md.
```

## Customization Notes

After init, the user can customize:
- **session-start.py / subagent-context.py**: The `DOCS_DIR` path is auto-configured relative to the hook location. No changes needed unless docs/ moves. Both return empty output when all data sources are empty (no noise). Shared logic lives in `context.py`.
- **workflow.md**: Optional. Create only if there are team workflow rules to enforce.
- **Doc vs Skill**: Reference documentation (architecture, decisions, research) belongs in `docs/`. Operational runbooks (local-dev setup, deploy procedures, troubleshooting playbooks) are better implemented as skills — they are triggerable, executable, and carry runtime context. If you find yourself writing a step-by-step guide in `docs/`, consider whether it should be a skill instead.
