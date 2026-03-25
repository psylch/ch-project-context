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

### Step 2: Ask Language Preference

Ask the user what language the documentation content should be written in. This affects doc body text only (decisions, issues, plans, research). Frontmatter keys, directory names, and code stay in English.

Examples: "English", "中文", "日本語", "한국어", etc. Default to English if the user doesn't care.

Store the answer for Step 4 (template substitution).

### Step 3: Check Existing State

Before running init, check what already exists:
- If `docs/` exists with content, warn the user and ask whether to merge (skip existing dirs) or abort
- If `.claude/hooks/` already has hook files, warn and ask whether to overwrite or skip
- If `.claude/settings.json` exists, merge hook entries rather than overwriting

### Step 4: Run Init Script

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

### Step 5: Update CLAUDE.md

After the script succeeds, update CLAUDE.md:

**If CLAUDE.md exists**: Append the docs navigation block at the end (read the file first to avoid duplicating if the block already exists — check for `<!-- ch-project-context:start -->` marker).

**If CLAUDE.md does not exist**: Create a minimal CLAUDE.md with project name (inferred from directory name or package.json) and the docs navigation block.

Read `{SKILL_DIR}/templates/claude-md-block.md`, replace `{lang}` with the user's language choice from Step 2, then append to CLAUDE.md.

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
