#!/usr/bin/env python3
"""
ch-project-context init script.

Creates the docs/ directory structure, installs Claude Code hooks,
and configures .claude/settings.json. Zero external dependencies.

Usage:
    python3 init.py --root /path/to/project
"""

import argparse
import json
import os
import sys
from datetime import date


# ── Directory structure to create ──────────────────────────────────

DIRS = [
    "docs/exec-plans/active",
    "docs/exec-plans/completed",
    "docs/decisions",
    "docs/research",
    "docs/known-issues",
    "docs/known-issues/resolved",
    "docs/archive",
    ".claude/hooks",
]


# ── Shared module: context.py ─────────────────────────────────────

CONTEXT_MODULE = r'''#!/usr/bin/env python3
"""
Shared context builder for ch-project-context hooks.

Reads docs/ directory structure and assembles structured context
with layered XML tags. Used by both session-start and subagent-context hooks.
"""

import os
import glob as globmod
import re


def parse_frontmatter(filepath):
    """Extract YAML frontmatter as a dict from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError):
        return None, ''

    if not content.startswith('---'):
        return None, content

    end = content.find('---', 3)
    if end == -1:
        return None, content

    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()

    # Simple YAML parser (no pyyaml dependency)
    meta = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip() for v in value[1:-1].split(',') if v.strip()]
            meta[key] = value
    return meta, body


def get_active_plans(docs_dir):
    """Read active exec-plans and extract status summary."""
    plans_dir = os.path.join(docs_dir, 'exec-plans', 'active')
    if not os.path.isdir(plans_dir):
        return []

    results = []
    for filepath in sorted(globmod.glob(os.path.join(plans_dir, '**', '*.md'), recursive=True)):
        meta, body = parse_frontmatter(filepath)
        if meta:
            name = os.path.basename(os.path.dirname(filepath))
            if name == 'active':
                name = os.path.splitext(os.path.basename(filepath))[0]
            results.append({
                'name': name,
                'title': meta.get('title', name),
                'description': meta.get('description', ''),
                'status': meta.get('status', 'unknown'),
            })

            handoff_match = re.search(
                r'## Phase \d+ .*?\n(.*?)(?=\n## |\Z)',
                body, re.DOTALL
            )
            if handoff_match:
                results[-1]['handoff'] = handoff_match.group(1).strip()[:500]
    return results


def get_active_issues(docs_dir):
    """Read active known-issues from frontmatter."""
    issues_dir = os.path.join(docs_dir, 'known-issues')
    if not os.path.isdir(issues_dir):
        return []

    results = []
    for filepath in sorted(globmod.glob(os.path.join(issues_dir, '*.md'))):
        meta, _ = parse_frontmatter(filepath)
        if meta and meta.get('status') == 'active':
            results.append({
                'id': os.path.splitext(os.path.basename(filepath))[0],
                'title': meta.get('title', ''),
                'description': meta.get('description', ''),
                'severity': meta.get('severity', ''),
            })
    return results


def get_workflow(docs_dir):
    """Read workflow.md if it exists."""
    workflow_path = os.path.join(docs_dir, 'workflow.md')
    if os.path.isfile(workflow_path):
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def build_context(docs_dir):
    """Assemble project context with layered XML tags. Returns empty string if no data."""
    plans = get_active_plans(docs_dir)
    issues = get_active_issues(docs_dir)
    workflow = get_workflow(docs_dir)

    if not plans and not issues and not workflow:
        return ''

    parts = []

    if plans:
        lines = []
        for p in plans:
            lines.append(f"**{p['title']}** — {p['status']}")
            if p['description']:
                lines.append(f"  {p['description']}")
            if p.get('handoff'):
                lines.append(f"  Last handoff: {p['handoff'][:200]}...")
            lines.append('')
        parts.append('<active-plans>\n' + '\n'.join(lines) + '</active-plans>')

    if issues:
        lines = []
        for i in issues:
            lines.append(f"**{i['id']}** ({i['severity']}): {i['title']}")
            if i['description']:
                lines.append(f"  {i['description']}")
            lines.append('')
        parts.append('<known-issues>\n' + '\n'.join(lines) + '</known-issues>')

    if workflow:
        parts.append(f'<workflow>\n{workflow}\n</workflow>')

    return '\n\n'.join(parts)
'''


# ── Hook: session-start.py ─────────────────────────────────────────

SESSION_START_HOOK = r'''#!/usr/bin/env python3
"""
Session-start hook: injects current project context at session start.
Uses shared context module for docs/ parsing.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context import build_context

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')


def main():
    context = build_context(DOCS_DIR)
    print(json.dumps({"hookSpecificOutput": context}))


if __name__ == '__main__':
    main()
'''


# ── Hook: subagent-context.py ─────────────────────────────────────

SUBAGENT_CONTEXT_HOOK = r'''#!/usr/bin/env python3
"""
PreToolUse hook: injects project context into subagent prompts.

Intercepts Task/Agent tool calls and appends docs/ context summary
so subagents are aware of active plans, known issues, and workflow rules.
Does not modify the original prompt — only adds context via updatedInput.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context import build_context

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = hook_input.get('tool_input', {})
    original_prompt = tool_input.get('prompt', '')

    context = build_context(DOCS_DIR)
    if not context:
        sys.exit(0)

    injection = f"\n\n<project-context>\n{context}\n</project-context>"
    new_prompt = original_prompt + injection

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {**tool_input, "prompt": new_prompt},
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
'''


# ── Settings.json template ─────────────────────────────────────────

SETTINGS_HOOKS = {
    "hooks": {
        "SessionStart": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 .claude/hooks/session-start.py",
                        "timeout": 10000,
                    }
                ],
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Task",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 .claude/hooks/subagent-context.py",
                        "timeout": 10000,
                    }
                ],
            },
            {
                "matcher": "Agent",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 .claude/hooks/subagent-context.py",
                        "timeout": 10000,
                    }
                ],
            },
        ],
    }
}


# ── Architecture template ──────────────────────────────────────────

ARCHITECTURE_TEMPLATE = """---
title: Architecture Overview
description: High-level system architecture and key design decisions
status: draft
date: {today}
---

# Architecture Overview

<!-- Replace this with your project's architecture description -->

## System Components

## Key Design Decisions

## Data Flow
"""


# ── Main logic ─────────────────────────────────────────────────────

def create_dirs(root):
    """Create the docs/ and .claude/hooks/ directory structure."""
    created = []
    skipped = []
    for d in DIRS:
        path = os.path.join(root, d)
        if os.path.isdir(path):
            skipped.append(d)
        else:
            os.makedirs(path, exist_ok=True)
            created.append(d)
    return created, skipped


def install_hooks(root):
    """Write hook scripts and shared module to .claude/hooks/."""
    hooks_dir = os.path.join(root, '.claude', 'hooks')
    os.makedirs(hooks_dir, exist_ok=True)

    installed = []

    # Shared context module
    context_path = os.path.join(hooks_dir, 'context.py')
    with open(context_path, 'w', encoding='utf-8') as f:
        f.write(CONTEXT_MODULE.lstrip('\n'))
    os.chmod(context_path, 0o755)

    # Session-start hook
    session_path = os.path.join(hooks_dir, 'session-start.py')
    with open(session_path, 'w', encoding='utf-8') as f:
        f.write(SESSION_START_HOOK.lstrip('\n'))
    os.chmod(session_path, 0o755)
    installed.append('session-start.py')

    # Subagent context hook (PreToolUse)
    subagent_path = os.path.join(hooks_dir, 'subagent-context.py')
    with open(subagent_path, 'w', encoding='utf-8') as f:
        f.write(SUBAGENT_CONTEXT_HOOK.lstrip('\n'))
    os.chmod(subagent_path, 0o755)
    installed.append('subagent-context.py')

    return installed


def update_settings(root):
    """Merge hook entries into .claude/settings.json."""
    settings_path = os.path.join(root, '.claude', 'settings.json')
    existing = {}

    if os.path.isfile(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    # Merge hooks
    if 'hooks' not in existing:
        existing['hooks'] = {}

    for event, entries in SETTINGS_HOOKS['hooks'].items():
        if event not in existing['hooks']:
            existing['hooks'][event] = entries
        else:
            # Check if hook command already registered
            existing_cmds = set()
            for entry in existing['hooks'][event]:
                for h in entry.get('hooks', []):
                    existing_cmds.add(h.get('command', ''))
            for entry in entries:
                for h in entry.get('hooks', []):
                    if h.get('command', '') not in existing_cmds:
                        existing['hooks'][event].append(entry)
                        break

    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)
        f.write('\n')

    return True


def create_architecture(root):
    """Create docs/architecture.md if it doesn't exist."""
    arch_path = os.path.join(root, 'docs', 'architecture.md')
    if os.path.isfile(arch_path):
        return False

    content = ARCHITECTURE_TEMPLATE.format(today=date.today().isoformat())
    with open(arch_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def main():
    parser = argparse.ArgumentParser(description='Initialize project context management system')
    parser.add_argument('--root', required=True, help='Project root directory')
    args = parser.parse_args()

    root = os.path.abspath(args.root)

    if not os.path.isdir(root):
        print(json.dumps({
            "status": "error",
            "error": f"Directory not found: {root}",
        }), file=sys.stderr)
        sys.exit(1)

    # Create directories
    created_dirs, skipped_dirs = create_dirs(root)

    # Install hooks
    hooks_installed = install_hooks(root)

    # Update settings.json
    settings_updated = update_settings(root)

    # Create architecture skeleton
    arch_created = create_architecture(root)
    if arch_created:
        created_dirs.append('docs/architecture.md')

    result = {
        "status": "ok",
        "root": root,
        "created": created_dirs,
        "skipped": skipped_dirs,
        "hooks_installed": hooks_installed,
        "settings_updated": settings_updated,
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
