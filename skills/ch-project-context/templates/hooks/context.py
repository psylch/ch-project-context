#!/usr/bin/env python3
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


def get_pending_plans(docs_dir):
    """Read pending exec-plans (planned but not yet started)."""
    plans_dir = os.path.join(docs_dir, 'exec-plans', 'pending')
    if not os.path.isdir(plans_dir):
        return []

    results = []
    for filepath in sorted(globmod.glob(os.path.join(plans_dir, '**', '*.md'), recursive=True)):
        meta, _ = parse_frontmatter(filepath)
        if meta:
            name = os.path.basename(os.path.dirname(filepath))
            if name == 'pending':
                name = os.path.splitext(os.path.basename(filepath))[0]
            results.append({
                'name': name,
                'title': meta.get('title', name),
                'description': meta.get('description', ''),
            })
    return results


def get_recent_completed_plans(docs_dir, max_count=3):
    """Read recently completed exec-plans, sorted by mtime desc, up to max_count."""
    plans_dir = os.path.join(docs_dir, 'exec-plans', 'completed')
    if not os.path.isdir(plans_dir):
        return []

    # Collect all completed plan files with mtime
    candidates = []
    for filepath in globmod.glob(os.path.join(plans_dir, '**', '*.md'), recursive=True):
        meta, _ = parse_frontmatter(filepath)
        if meta:
            candidates.append((filepath, meta, os.path.getmtime(filepath)))

    # Sort by mtime descending, take top N
    candidates.sort(key=lambda x: x[2], reverse=True)
    candidates = candidates[:max_count]

    from datetime import datetime
    results = []
    for filepath, meta, mtime in candidates:
        name = os.path.basename(os.path.dirname(filepath))
        if name == 'completed':
            name = os.path.splitext(os.path.basename(filepath))[0]
        completed_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
        results.append({
            'name': name,
            'title': meta.get('title', name),
            'summary': meta.get('summary', meta.get('description', '')),
            'completed_date': completed_date,
        })
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
    pending = get_pending_plans(docs_dir)
    plans = get_active_plans(docs_dir)
    completed = get_recent_completed_plans(docs_dir)
    issues = get_active_issues(docs_dir)
    workflow = get_workflow(docs_dir)

    if not pending and not plans and not completed and not issues and not workflow:
        return ''

    parts = []

    if pending:
        lines = []
        for p in pending:
            lines.append(f"**{p['title']}**")
            if p['description']:
                lines.append(f"  {p['description']}")
            lines.append('')
        parts.append('<pending-plans>\n' + '\n'.join(lines) + '</pending-plans>')

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

    if completed:
        lines = []
        for p in completed:
            lines.append(f"**{p['title']}** — completed {p['completed_date']}")
            if p['summary']:
                lines.append(f"  {p['summary']}")
            lines.append('')
        parts.append('<recent-completed-plans>\n' + '\n'.join(lines) + '</recent-completed-plans>')

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
