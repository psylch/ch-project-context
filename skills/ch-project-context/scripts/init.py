#!/usr/bin/env python3
"""
ch-project-context init script.

Creates the docs/ directory structure, copies hook templates,
and configures .claude/settings.json. Zero external dependencies.

All content lives in ../templates/ — this script only copies and merges.

Usage:
    python3 init.py --root /path/to/project
"""

import argparse
import json
import os
import shutil
import sys
from datetime import date


# ── Paths ─────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, '..', 'templates')

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


# ── Main logic ────────────────────────────────────────────────────

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
    """Copy hook templates to .claude/hooks/."""
    hooks_dir = os.path.join(root, '.claude', 'hooks')
    src_dir = os.path.join(TEMPLATES_DIR, 'hooks')

    installed = []
    for filename in sorted(os.listdir(src_dir)):
        if not filename.endswith('.py'):
            continue
        src = os.path.join(src_dir, filename)
        dst = os.path.join(hooks_dir, filename)
        shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
        if filename != 'context.py':
            installed.append(filename)

    return installed


def update_settings(root):
    """Merge hook entries from template into .claude/settings.json."""
    settings_path = os.path.join(root, '.claude', 'settings.json')
    template_path = os.path.join(TEMPLATES_DIR, 'settings-hooks.json')

    existing = {}
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)

    # Merge hooks
    if 'hooks' not in existing:
        existing['hooks'] = {}

    for event, entries in template['hooks'].items():
        if event not in existing['hooks']:
            existing['hooks'][event] = entries
        else:
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
    """Copy architecture template to docs/, substituting {today}."""
    arch_path = os.path.join(root, 'docs', 'architecture.md')
    if os.path.isfile(arch_path):
        return False

    template_path = os.path.join(TEMPLATES_DIR, 'docs', 'architecture.md')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('{today}', date.today().isoformat())

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

    created_dirs, skipped_dirs = create_dirs(root)
    hooks_installed = install_hooks(root)
    settings_updated = update_settings(root)

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
