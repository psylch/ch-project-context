---
name: ch-project-context
description: "Initialize a project-level context management system with a structured docs/ directory, automatic session and subagent context injection, docs validation, and project instruction navigation. Supports Claude Code, Codex, or both. Use when starting a long-lived project, bootstrapping context management, or when the user says '/ch-project-context init', 'init project context', 'setup context management', or 'initialize docs structure'."
---

# ch-project-context

Initialize durable project context for Claude Code, Codex, or both without mixing their configuration formats.

## Step 0: Assess Project Fit

Determine whether the project needs the full mechanism:

| Signal | Full mechanism is useful when… |
|--------|-------------------------------|
| Multi-agent handoff | Multiple agents or people take turns working on it |
| Cross-session continuity | Work spans enough sessions for state to drift |
| Long-lived work items | Decisions, plans, and issues accumulate over days |

If all three signals are absent, recommend a lightweight project instruction file (`CLAUDE.md`, `AGENTS.md`, or both) and stop. Do not create `docs/` or hooks.

## Step 1: Resolve the Project Root

Use the current working directory. Verify that it looks like a project root, such as containing `.git/`, `package.json`, `Cargo.toml`, or `pyproject.toml`. If evidence points to a parent directory, resolve it before writing.

For `codex` or `both`, require the selected root to be a Git repository root (`.git` may be a directory or worktree file). Codex discovers repo-local `.codex/hooks.json` through its trusted project configuration layer; a standalone non-Git directory is not sufficient. If Git is absent, ask the user whether to initialize it or choose `claude`. Do not run `git init` without the user's approval.

## Step 2: Select Target and Language

Select one target:

- `claude`: generate `CLAUDE.md`, `.claude/hooks/`, and merge `.claude/settings.json`.
- `codex`: generate `AGENTS.md`, `.codex/hooks/`, and merge `.codex/hooks.json`.
- `both`: generate both instruction files and keep each platform's hook configuration separate.

If the user did not specify a target and the active environment does not make it unambiguous, ask which target they want. The init script defaults to `claude` only for backward-compatible direct CLI use.

Ask which language to use for documentation body text. Default to English if the user has no preference. Keep frontmatter keys, directory names, and code in English.

## Step 3: Inspect Existing State

Before running init:

- If `docs/` contains files, explain that init skips the architecture template but hook templates are refreshed.
- For `claude`, inspect `.claude/hooks/` and `.claude/settings.json`.
- For `codex`, inspect `.codex/hooks/` and `.codex/hooks.json`.
- For `both`, inspect both platform directories.
- Preserve unrelated hook entries and settings. If an existing generated hook was customized, show the overlap and ask before replacing it.

## Step 4: Run Init

Run:

```bash
python3 {SKILL_DIR}/scripts/init.py \
  --root <project-root> \
  --target <claude|codex|both>
```

The script has no external dependencies. It creates the docs structure, installs only the hooks needed by the selected target, and merges hook entries without replacing unrelated configuration.

Expected output:

```json
{
  "status": "ok",
  "root": "/path/to/project",
  "target": "both",
  "created": ["docs/exec-plans/active", ".claude/hooks", ".codex/hooks"],
  "skipped": [],
  "hooks_installed": {
    "claude": ["session-start.py", "subagent-context.py", "post-edit-validate.py"],
    "codex": ["session-start.py", "subagent-start.py", "post-edit-validate.py"]
  },
  "configs_updated": {"claude": true, "codex": true}
}
```

## Step 5: Update Project Instructions

Read `{SKILL_DIR}/templates/instructions-block.md`, replace `{lang}`, and append it to each selected instruction file:

- `claude` → `CLAUDE.md`
- `codex` → `AGENTS.md`
- `both` → both files

If the file exists, read it first and preserve its content. Do not append another block when `<!-- ch-project-context:start -->` is already present. If the file does not exist, create a minimal heading with the inferred project name before the block.

## Step 6: Verify Platform Behavior

Verify generated files and run hooks directly before reporting success:

```bash
python3 <project-root>/.claude/hooks/session-start.py
python3 <project-root>/.codex/hooks/session-start.py
python3 <project-root>/.codex/hooks/subagent-start.py
```

Run only commands for the selected target. Empty output is acceptable when the project has no active plans, issues, or workflow rules.

For Codex, tell the user to open `/hooks` and review/trust the new project-local hook definitions. Codex deliberately skips untrusted project hooks until they are approved.

Platform behavior:

- Claude Code uses `SessionStart` and `PreToolUse` prompt enrichment for `Task`/`Agent`.
- Codex uses native `SessionStart` and `SubagentStart` context injection.
- Both use `PostToolUse` to surface exec-plan convention violations after relevant edits.

## Step 7: Audit Existing Content

Report findings without automatically moving content:

1. Flag progress, plans, issues, or decisions duplicated in `MEMORY.md`.
2. Flag architecture, decision, issue, or plan documents scattered outside `docs/`.
3. Flag substantial "Known Issues", "Architecture", "Decisions", or "Roadmap" sections embedded in `README.md`.
4. Flag pre-existing files in `docs/` that lack required YAML frontmatter.
5. Suggest converting operational runbooks into reusable skills.
6. Verify the selected instruction file or files contain the navigation block and point to installed skills when appropriate.

Skip the audit section in the final report when no findings exist.

## Step 8: Report

Report:

- project root and selected target;
- created and skipped paths;
- exact hooks installed for each platform;
- configuration files merged;
- instruction files updated;
- verification results;
- audit findings;
- for Codex, the required `/hooks` trust-review step.

Recommend editing `docs/architecture.md` and creating the first active exec plan when appropriate.

## Implementation Notes

- `context.py` is shared logic copied separately into each selected platform directory.
- Hook scripts resolve `docs/` relative to their own location.
- Hooks stay silent when all data sources are empty.
- `docs/workflow.md` is optional and is injected automatically when present.
- Reference knowledge belongs in `docs/`; repeatable operational procedures belong in skills.
