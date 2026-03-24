# ch-project-context

[中文文档](README.zh.md)

A [skills.sh](https://skills.sh/) skill for Claude Code that bootstraps a project-level context management system in one command.

## What It Does

Running `/ch-project-context init` in a Claude Code session will:

1. Create a structured `docs/` directory (`exec-plans/`, `decisions/`, `research/`, `known-issues/`, `archive/`)
2. Install two Claude Code hooks:
   - **session-start** -- auto-injects active plans, known issues, and workflow rules into every new session
   - **quality-gate** -- blocks subagent completion until the build passes and verification evidence exists
3. Wire hooks into `.claude/settings.json`
4. Append a documentation navigation block to `CLAUDE.md`
5. Optionally create a `docs/architecture.md` skeleton

All generated docs use YAML frontmatter so the hooks can parse them programmatically.

## Install

### Via skills.sh (recommended)

```bash
npx skills add psylch/ch-project-context -g -y
```

### Manual Install

```bash
git clone https://github.com/psylch/ch-project-context.git ~/.claude/skills/ch-project-context
```

Restart your agent after installation.

## Prerequisites

- Any AI coding agent that supports [skills.sh](https://skills.sh/) (Claude Code, Cursor, Windsurf, etc.)
- **Python 3.6+** (for skill scripts, zero external dependencies)

## Usage

In any Claude Code session:

```
/ch-project-context init
```

The skill detects the project root, checks for existing files (prompts before overwriting), runs the init script, and reports what was created.

## Customization

After init, you can customize:

- **`.claude/hooks/quality-gate.py`** -- Change `BUILD_CMD` from `['npx', 'tsc', '--noEmit']` to your project's build check (e.g., `['cargo', 'check']`, `['ruff', 'check', '.']`)
- **`docs/workflow.md`** -- Create this file to inject team workflow rules into every session automatically

## File Structure

```
ch-project-context/
├── skills/
│   └── ch-project-context/
│       ├── SKILL.md              # Skill definition and instructions
│       ├── scripts/
│       │   └── init.py           # Init script (creates dirs, hooks, settings)
│       └── references/
│           └── conventions.md    # Frontmatter spec, naming, and doc templates
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── README.md
├── README.zh.md
└── LICENSE
```

## License

MIT
