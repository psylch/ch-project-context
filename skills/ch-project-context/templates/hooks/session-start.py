#!/usr/bin/env python3
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
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
