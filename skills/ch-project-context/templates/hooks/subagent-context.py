#!/usr/bin/env python3
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
