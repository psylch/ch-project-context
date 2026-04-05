#!/usr/bin/env python3
"""
Stop hook: validates docs/ conventions after each agent turn.
Only emits output when issues are found — silent otherwise.
"""

import json
import os
import sys
import re
import glob as globmod

sys.path.insert(0, os.path.dirname(__file__))
from context import parse_frontmatter

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')


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
            for field in ('title', 'description', 'status', 'date'):
                if field not in meta:
                    findings.append(f'{rel}: missing required field "{field}"')

            status = meta.get('status', '')

            # Completed plans must have summary
            if subdir == 'completed' and 'summary' not in meta:
                findings.append(f'{rel}: completed plan missing "summary" field')

            # Status/directory mismatch
            if subdir == 'active' and status == 'completed':
                findings.append(f'{rel}: status is "completed" but file is still in active/ — move to completed/')
            if subdir == 'completed' and status in ('in-progress', 'pending'):
                findings.append(f'{rel}: status is "{status}" but file is in completed/')
            if subdir == 'pending' and status == 'in-progress':
                findings.append(f'{rel}: status is "in-progress" but file is in pending/ — move to active/')

    return findings


def main():
    findings = validate_exec_plans()
    if not findings:
        return

    audit_text = '<context-audit>\n'
    for f in findings:
        audit_text += f'  x {f}\n'
    audit_text += '</context-audit>'

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": audit_text,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
