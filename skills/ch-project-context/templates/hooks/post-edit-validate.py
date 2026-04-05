#!/usr/bin/env python3
"""
PostToolUse hook: validates exec-plan conventions after Write/Edit on docs/exec-plans/.
Only emits output when issues are found — silent otherwise.
"""

import json
import os
import sys
import glob as globmod

sys.path.insert(0, os.path.dirname(__file__))
from context import parse_frontmatter

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')


def is_exec_plan_edit(tool_input):
    """Check if the edited file is under docs/exec-plans/."""
    file_path = tool_input.get('file_path', '')
    return 'exec-plans' in file_path


def validate_exec_plans():
    """Check exec-plans for convention violations. Returns list of findings."""
    findings = []
    plans_root = os.path.join(DOCS_DIR, 'exec-plans')
    if not os.path.isdir(plans_root):
        return findings

    for subdir in ('active', 'pending', 'completed'):
        dirpath = os.path.join(plans_root, subdir)
        if not os.path.isdir(dirpath):
            continue
        for filepath in globmod.glob(os.path.join(dirpath, '**', '*.md'), recursive=True):
            meta, _ = parse_frontmatter(filepath)
            rel = os.path.relpath(filepath, DOCS_DIR)
            if meta is None:
                findings.append(f'{rel}: missing YAML frontmatter')
                continue

            # Required fields
            missing = [f for f in ('title', 'description', 'status', 'date') if f not in meta]
            if missing:
                findings.append(f'{rel} — add {", ".join(missing)} to frontmatter')

            status = meta.get('status', '')

            # Completed plans must have summary
            if subdir == 'completed' and 'summary' not in meta:
                findings.append(f'{rel} — add summary to frontmatter')

            # Status/directory mismatch
            if subdir == 'active' and status == 'completed':
                findings.append(f'{rel} — move to completed/')
            if subdir == 'completed' and status in ('in-progress', 'pending'):
                findings.append(f'{rel} — update status to completed')
            if subdir == 'pending' and status == 'in-progress':
                findings.append(f'{rel} — move to active/')

    return findings


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        return

    # Only run if the edit touched exec-plans
    tool_input = hook_input.get('tool_input', {})
    if not is_exec_plan_edit(tool_input):
        return

    findings = validate_exec_plans()
    if not findings:
        return

    audit_text = 'Fix exec-plan issues:\n'
    for f in findings:
        audit_text += f'• {f}\n'

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": audit_text,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
