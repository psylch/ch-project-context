# ch-project-context

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

All generated docs use YAML frontmatter so the hooks can parse them programmatically. See `references/conventions.md` for the full frontmatter spec, naming conventions, and document templates.

## Install

```bash
# From this repo (local path)
npx skills add /path/to/this/repo -g

# Or from GitHub (once published)
npx skills add <owner>/ch-project-context -g
```

The `-g` flag installs globally so the skill is available in all projects.

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
├── SKILL.md              # Skill definition and instructions
├── scripts/
│   └── init.py           # Init script (creates dirs, hooks, settings)
└── references/
    └── conventions.md    # Frontmatter spec, naming, and doc templates
```

## License

MIT
