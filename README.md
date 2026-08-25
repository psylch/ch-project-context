# ch-project-context

[中文文档](README.zh.md)

A [skills.sh](https://skills.sh/) skill that bootstraps durable project context for Claude Code, Codex, or both.

## What It Does

Running `/ch-project-context init`:

1. Creates a structured `docs/` tree for plans, decisions, research, known issues, and archives.
2. Installs session-start, subagent-context, and docs-validation hooks.
3. Configures Claude Code in `.claude/`, Codex in `.codex/`, or both without mixing formats.
4. Adds the docs navigation block to `CLAUDE.md`, `AGENTS.md`, or both.
5. Creates `docs/architecture.md` when it does not already exist.

Claude Code uses `SessionStart` plus `PreToolUse` prompt enrichment. Codex uses native `SessionStart` and `SubagentStart` context injection.

## Install

```bash
npx skills add psylch/ch-project-context -g -y
```

Python 3.6+ is required; the scripts have no external dependencies.

Codex project-local hooks require the selected project root to be a Git repository. Claude-only initialization can also be used in non-Git project directories.

## Usage

Invoke the skill:

```text
/ch-project-context init
```

The skill asks for the target (`claude`, `codex`, or `both`) and documentation language, checks existing files, initializes the project, and verifies the generated hooks.

The underlying script can also be run directly:

```bash
python3 skills/ch-project-context/scripts/init.py \
  --root /path/to/project \
  --target codex
```

For backward compatibility, the direct script defaults to `--target claude`.

Codex requires project-local hooks to be reviewed and trusted through `/hooks` before they run.

## License

MIT
