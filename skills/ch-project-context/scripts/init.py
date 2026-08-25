#!/usr/bin/env python3
"""
ch-project-context init script.

Creates the docs/ directory structure and configures context hooks for
Claude Code, Codex, or both. Zero external dependencies.

All content lives in ../templates/ — this script only copies and merges.

Usage:
    python3 init.py --root /path/to/project --target claude|codex|both
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

DOCS_DIRS = [
    "docs/exec-plans/pending",
    "docs/exec-plans/active",
    "docs/exec-plans/completed",
    "docs/decisions",
    "docs/research",
    "docs/known-issues",
    "docs/known-issues/resolved",
    "docs/archive",
]

TARGET_DIRS = {
    "claude": [".claude/hooks"],
    "codex": [".codex/hooks"],
    "both": [".claude/hooks", ".codex/hooks"],
}

HOOK_FILES = {
    "claude": {
        "context.py": "context.py",
        "session-start.py": "session-start.py",
        "subagent-context.py": "subagent-context.py",
        "post-edit-validate.py": "post-edit-validate.py",
    },
    "codex": {
        "context.py": "context.py",
        "session-start.py": "session-start.py",
        "codex-subagent-start.py": "subagent-start.py",
        "post-edit-validate.py": "post-edit-validate.py",
    },
}


# ── Main logic ────────────────────────────────────────────────────

def selected_targets(target):
    """Expand the public target value into concrete platforms."""
    return ["claude", "codex"] if target == "both" else [target]


def create_dirs(root, target):
    """Create the docs/ and selected platform hook directories."""
    created = []
    skipped = []
    for d in DOCS_DIRS + TARGET_DIRS[target]:
        path = os.path.join(root, d)
        if os.path.isdir(path):
            skipped.append(d)
        else:
            os.makedirs(path, exist_ok=True)
            created.append(d)
    return created, skipped


def install_hooks(root, platform):
    """Copy the hook templates needed by one platform."""
    hooks_dir = os.path.join(root, f'.{platform}', 'hooks')
    src_dir = os.path.join(TEMPLATES_DIR, 'hooks')

    installed = []
    for source_name, destination_name in HOOK_FILES[platform].items():
        src = os.path.join(src_dir, source_name)
        dst = os.path.join(hooks_dir, destination_name)
        shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
        if destination_name != 'context.py':
            installed.append(destination_name)

    return installed


def update_hook_config(root, platform):
    """Merge hook entries into the selected platform's JSON config."""
    if platform == 'claude':
        settings_path = os.path.join(root, '.claude', 'settings.json')
        template_name = 'settings-hooks.json'
    else:
        settings_path = os.path.join(root, '.codex', 'hooks.json')
        template_name = 'codex-hooks.json'
    template_path = os.path.join(TEMPLATES_DIR, template_name)

    existing = {}
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)

    # Replace only hooks owned by this skill, including commands from older
    # releases, while preserving unrelated handlers in the same event group.
    managed_fragments = tuple(
        f'.{platform}/hooks/{destination_name}'
        for destination_name in HOOK_FILES[platform].values()
        if destination_name != 'context.py'
    )
    for event, entries in existing.get('hooks', {}).items():
        cleaned_entries = []
        for entry in entries:
            cleaned_hooks = []
            for hook in entry.get('hooks', []):
                command = hook.get('command', '')
                if not any(fragment in command for fragment in managed_fragments):
                    cleaned_hooks.append(hook)
            if cleaned_hooks:
                cleaned_entry = dict(entry)
                cleaned_entry['hooks'] = cleaned_hooks
                cleaned_entries.append(cleaned_entry)
        existing['hooks'][event] = cleaned_entries

    # Merge hooks without replacing unrelated user configuration.
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
    parser.add_argument(
        '--target',
        choices=('claude', 'codex', 'both'),
        default='claude',
        help='Agent environment to configure (default: claude)',
    )
    args = parser.parse_args()

    root = os.path.abspath(args.root)

    if not os.path.isdir(root):
        print(json.dumps({
            "status": "error",
            "error": f"Directory not found: {root}",
        }), file=sys.stderr)
        sys.exit(1)

    if args.target in ('codex', 'both') and not os.path.exists(os.path.join(root, '.git')):
        print(json.dumps({
            "status": "error",
            "error": (
                "Codex project hooks require --root to be a Git repository root. "
                "Initialize Git first or use --target claude."
            ),
        }), file=sys.stderr)
        sys.exit(2)

    created_dirs, skipped_dirs = create_dirs(root, args.target)
    hooks_installed = {}
    configs_updated = {}
    for platform in selected_targets(args.target):
        hooks_installed[platform] = install_hooks(root, platform)
        configs_updated[platform] = update_hook_config(root, platform)

    arch_created = create_architecture(root)
    if arch_created:
        created_dirs.append('docs/architecture.md')

    result = {
        "status": "ok",
        "root": root,
        "target": args.target,
        "created": created_dirs,
        "skipped": skipped_dirs,
        "hooks_installed": hooks_installed,
        "configs_updated": configs_updated,
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
