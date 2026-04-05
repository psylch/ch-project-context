#!/usr/bin/env python3
"""
Validate docs/ directory against ch-project-context conventions.

Usage:
  python3 validate-docs.py [--root <project-root>]

Checks:
  1. Required frontmatter fields (title, description, status, date)
  2. Completed plans must have 'summary' field
  3. Status values are valid per doc type
  4. File naming conventions
  5. Misplaced files (e.g., completed plan still in active/)

Exit code 0 = all pass, 1 = has warnings, 2 = has errors.
"""

import os
import sys
import re
import glob as globmod
import argparse


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


REQUIRED_FIELDS = ['title', 'description', 'status', 'date']
VALID_STATUSES = {'active', 'completed', 'in-progress', 'pending', 'draft'}
DECISION_PATTERN = re.compile(r'^D\d{3}-')
ISSUE_PATTERN = re.compile(r'^I\d{3}-')


def validate_file(filepath, docs_dir):
    """Validate a single doc file. Returns list of (level, message)."""
    findings = []
    rel = os.path.relpath(filepath, docs_dir)
    basename = os.path.basename(filepath)

    meta, body = parse_frontmatter(filepath)

    # Check 1: Frontmatter exists
    if meta is None:
        findings.append(('error', f'{rel}: missing YAML frontmatter'))
        return findings

    # Check 2: Required fields
    for field in REQUIRED_FIELDS:
        if field not in meta:
            findings.append(('error', f'{rel}: missing required field "{field}"'))

    # Check 3: Valid status
    status = meta.get('status', '')
    if status and not status.startswith('superseded-by'):
        if status not in VALID_STATUSES:
            findings.append(('warn', f'{rel}: unknown status "{status}"'))

    # Check 4: Completed plans must have summary
    in_completed = '/completed/' in filepath.replace(os.sep, '/')
    if in_completed and 'summary' not in meta:
        findings.append(('error', f'{rel}: completed plan missing "summary" field'))

    # Check 5: Status/directory mismatch
    in_active = '/active/' in filepath.replace(os.sep, '/')
    in_pending = '/pending/' in filepath.replace(os.sep, '/')
    if in_active and status == 'completed':
        findings.append(('error', f'{rel}: status is "completed" but file is in active/ — move to completed/'))
    if in_completed and status in ('in-progress', 'pending'):
        findings.append(('warn', f'{rel}: status is "{status}" but file is in completed/'))
    if in_pending and status == 'in-progress':
        findings.append(('warn', f'{rel}: status is "in-progress" but file is in pending/ — move to active/'))

    # Check 6: Naming conventions
    if '/decisions/' in filepath.replace(os.sep, '/'):
        if not DECISION_PATTERN.match(basename):
            findings.append(('warn', f'{rel}: decision file should follow D001-short-description.md pattern'))
    if '/known-issues/' in filepath.replace(os.sep, '/') and '/resolved/' not in filepath.replace(os.sep, '/'):
        if not ISSUE_PATTERN.match(basename):
            findings.append(('warn', f'{rel}: issue file should follow I001-short-description.md pattern'))

    return findings


def main():
    parser = argparse.ArgumentParser(description='Validate docs/ conventions')
    parser.add_argument('--root', default='.', help='Project root directory')
    args = parser.parse_args()

    docs_dir = os.path.join(os.path.abspath(args.root), 'docs')
    if not os.path.isdir(docs_dir):
        print(f'No docs/ directory found at {docs_dir}')
        sys.exit(0)

    all_findings = []
    md_files = sorted(globmod.glob(os.path.join(docs_dir, '**', '*.md'), recursive=True))

    if not md_files:
        print('No markdown files found in docs/')
        sys.exit(0)

    for filepath in md_files:
        # Skip workflow.md (no frontmatter required)
        if os.path.basename(filepath) == 'workflow.md':
            continue
        # Skip architecture.md template placeholder
        findings = validate_file(filepath, docs_dir)
        all_findings.extend(findings)

    errors = [f for f in all_findings if f[0] == 'error']
    warns = [f for f in all_findings if f[0] == 'warn']

    print(f'Scanned {len(md_files)} files in docs/')
    print()

    if not all_findings:
        print('All checks passed.')
        sys.exit(0)

    if errors:
        print(f'ERRORS ({len(errors)}):')
        for _, msg in errors:
            print(f'  x {msg}')
        print()

    if warns:
        print(f'WARNINGS ({len(warns)}):')
        for _, msg in warns:
            print(f'  ! {msg}')
        print()

    sys.exit(2 if errors else 1)


if __name__ == '__main__':
    main()
