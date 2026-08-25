#!/usr/bin/env python3
"""Codex SubagentStart hook: inject current project context into a subagent."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context import build_context

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')


def main():
    context = build_context(DOCS_DIR)
    if not context:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": context,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
