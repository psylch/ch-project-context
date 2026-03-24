---
name: ch-project-context
description: "Initialize a project-level context management system with docs/ directory structure, Claude Code hooks (session-start, quality-gate), and CLAUDE.md navigation. Use when starting a new project, bootstrapping context management, or when the user says '/ch-project-context init', 'init project context', 'setup context management', 'initialize docs structure'."
---

# ch-project-context

One-command initialization of a project-level context management system for Claude Code agents.

## What It Does

Creates a structured `docs/` directory, installs Claude Code hooks for automatic context injection and quality gating, and wires everything into `.claude/settings.json` and `CLAUDE.md`.

## When to Use

- Starting a new project that will use Claude Code agents
- Bootstrapping context management in an existing project that lacks it
- User says `/ch-project-context init` or similar

## Instructions

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
  "hooks_installed": ["session-start.py", "quality-gate.py"],
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

- **Session-start hook**: Auto-injects active plans, known issues, and workflow rules at session start
- **Quality-gate hook**: Blocks subagent completion until TypeScript compiles and verification evidence exists
- **Frontmatter convention**: Every doc file uses YAML frontmatter (title, description, status, related) for hook parsing

### Document Lifecycle

- New plans go in `exec-plans/active/`, move to `completed/` when done
- New issues go in `known-issues/`, move to `resolved/` when fixed
- Decisions and research are permanent (one file per topic, 30-100 lines)
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
  - .claude/hooks/session-start.py (SessionStart)
  - .claude/hooks/quality-gate.py (SubagentStop)

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
- **quality-gate.py**: Change the build command (default: `npx tsc --noEmit`). For non-TypeScript projects, replace with `cargo check`, `go build ./...`, `ruff check`, etc.
- **session-start.py**: The `DOCS_DIR` path is auto-configured relative to the hook location. No changes needed unless docs/ moves.
- **workflow.md**: Optional. Create only if there are team workflow rules to enforce.
