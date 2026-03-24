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


# ── Hook: session-start.py ─────────────────────────────────────────

SESSION_START_HOOK = r'''#!/usr/bin/env python3
"""
Session-start hook: injects current project context into agent prompt.

Reads exec-plans frontmatter, active known-issues, and workflow.md
to assemble a <session-context> block. Agent receives this automatically
on every session start, compact, and clear.
"""

import json
import os
import glob as globmod
import re
import sys

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')


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


def get_active_plans():
    """Read active exec-plans and extract status summary."""
    plans_dir = os.path.join(DOCS_DIR, 'exec-plans', 'active')
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


def get_active_issues():
    """Read active known-issues from frontmatter."""
    issues_dir = os.path.join(DOCS_DIR, 'known-issues')
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


def get_workflow():
    """Read workflow.md if it exists."""
    workflow_path = os.path.join(DOCS_DIR, 'workflow.md')
    if os.path.isfile(workflow_path):
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def build_context():
    """Assemble the session context."""
    parts = ['<session-context>']

    plans = get_active_plans()
    if plans:
        parts.append('\n## Active Exec Plans\n')
        for p in plans:
            parts.append(f"**{p['title']}** — {p['status']}")
            if p['description']:
                parts.append(f"  {p['description']}")
            if p.get('handoff'):
                parts.append(f"  Last handoff: {p['handoff'][:200]}...")
            parts.append('')

    issues = get_active_issues()
    if issues:
        parts.append('\n## Active Known Issues\n')
        for i in issues:
            parts.append(f"**{i['id']}** ({i['severity']}): {i['title']}")
            if i['description']:
                parts.append(f"  {i['description']}")
            parts.append('')

    workflow = get_workflow()
    if workflow:
        parts.append('\n## Workflow Rules\n')
        parts.append(workflow)
        parts.append('')

    parts.append('</session-context>')
    return '\n'.join(parts)


def main():
    context = build_context()
    result = {
        "hookSpecificOutput": context
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
'''


# ── Hook: quality-gate.py ──────────────────────────────────────────

QUALITY_GATE_HOOK = r'''#!/usr/bin/env python3
"""
Quality-gate hook (SubagentStop): blocks subagent from stopping
until verification passes.

Checks:
1. Build verification (configurable command)
2. Agent output contains test/verification evidence

If checks fail, returns a message asking the agent to fix issues.
"""

import json
import os
import subprocess
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')

# ── Configure your build check command here ──
# Examples:
#   ['npx', 'tsc', '--noEmit']       # TypeScript
#   ['cargo', 'check']                # Rust
#   ['go', 'build', './...']          # Go
#   ['ruff', 'check', '.']            # Python
BUILD_CMD = ['npx', 'tsc', '--noEmit']
BUILD_TIMEOUT = 60


def run_build_check():
    """Run the build check command and return (success, output)."""
    try:
        result = subprocess.run(
            BUILD_CMD,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
            encoding='utf-8',
            errors='replace',
        )
        return result.returncode == 0, result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def check_agent_output(agent_output):
    """Check if agent output contains verification evidence."""
    if not agent_output:
        return False, "No agent output to check"

    evidence_patterns = [
        'tsc', 'typecheck', 'compile', 'test', 'verify',
        'npm run', 'npx', 'cargo', 'go build', 'ruff',
        'PASS', 'FAIL', 'error', 'warning',
    ]
    lower_output = agent_output.lower()
    found = [p for p in evidence_patterns if p.lower() in lower_output]
    if found:
        return True, f"Found verification evidence: {', '.join(found)}"
    return False, "No verification evidence found in agent output"


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    agent_output = hook_input.get('agentOutput', '')
    failures = []

    # Check 1: Build verification
    build_ok, build_output = run_build_check()
    if not build_ok:
        error_summary = build_output[:500] if build_output else "Unknown error"
        failures.append(f"Build check failed:\n{error_summary}")

    # Check 2: Agent provided verification evidence
    evidence_ok, evidence_msg = check_agent_output(agent_output)
    if not evidence_ok:
        failures.append(f"Verification: {evidence_msg}")

    if failures:
        message = "Quality gate failed. Please fix before completing:\n\n"
        message += "\n\n".join(f"- {f}" for f in failures)
        result = {
            "decision": "block",
            "reason": message,
        }
    else:
        result = {
            "decision": "allow",
        }

    print(json.dumps(result))


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
        "SubagentStop": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 .claude/hooks/quality-gate.py",
                        "timeout": 120000,
                    }
                ],
            }
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
    """Write hook scripts to .claude/hooks/."""
    hooks_dir = os.path.join(root, '.claude', 'hooks')
    os.makedirs(hooks_dir, exist_ok=True)

    installed = []

    session_path = os.path.join(hooks_dir, 'session-start.py')
    with open(session_path, 'w', encoding='utf-8') as f:
        f.write(SESSION_START_HOOK.lstrip('\n'))
    os.chmod(session_path, 0o755)
    installed.append('session-start.py')

    gate_path = os.path.join(hooks_dir, 'quality-gate.py')
    with open(gate_path, 'w', encoding='utf-8') as f:
        f.write(QUALITY_GATE_HOOK.lstrip('\n'))
    os.chmod(gate_path, 0o755)
    installed.append('quality-gate.py')

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
