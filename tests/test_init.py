import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "ch-project-context"
INIT_SCRIPT = SKILL_ROOT / "scripts" / "init.py"


class InitContextTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def run_init(self, target=None):
        command = [sys.executable, str(INIT_SCRIPT), "--root", str(self.project)]
        if target:
            command.extend(["--target", target])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def init_git(self):
        subprocess.run(
            ["git", "init", "--quiet", str(self.project)],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_default_target_remains_claude(self):
        result = self.run_init()

        self.assertEqual(result["target"], "claude")
        self.assertTrue((self.project / ".claude/settings.json").is_file())
        self.assertFalse((self.project / ".codex").exists())
        self.assertTrue((self.project / ".claude/hooks/subagent-context.py").is_file())

    def test_claude_target_replaces_legacy_owned_commands_only(self):
        config_dir = self.project / ".claude"
        config_dir.mkdir()
        config_path = config_dir / "settings.json"
        legacy_command = (
            "bash -c 'cd \"$(git rev-parse --show-toplevel)\" "
            "&& python3 .claude/hooks/session-start.py'"
        )
        config_path.write_text(json.dumps({
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"type": "command", "command": legacy_command}]},
                    {"hooks": [{"type": "command", "command": "python3 custom.py"}]},
                ]
            }
        }), encoding="utf-8")

        self.run_init("claude")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        commands = [
            hook["command"]
            for entry in config["hooks"]["SessionStart"]
            for hook in entry["hooks"]
        ]

        self.assertNotIn(legacy_command, commands)
        self.assertIn("python3 custom.py", commands)
        self.assertEqual(sum(".claude/hooks/session-start.py" in c for c in commands), 1)

    def test_codex_target_installs_native_hooks_and_preserves_existing_config(self):
        self.init_git()
        config_dir = self.project / ".codex"
        config_dir.mkdir()
        config_path = config_dir / "hooks.json"
        config_path.write_text(json.dumps({
            "custom": "preserved",
            "hooks": {
                "UserPromptSubmit": [{
                    "hooks": [{"type": "command", "command": "python3 custom.py"}]
                }]
            },
        }), encoding="utf-8")

        first = self.run_init("codex")
        second = self.run_init("codex")
        config = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(first["target"], "codex")
        self.assertEqual(second["target"], "codex")
        self.assertEqual(config["custom"], "preserved")
        self.assertIn("UserPromptSubmit", config["hooks"])
        self.assertEqual(len(config["hooks"]["SessionStart"]), 1)
        self.assertEqual(len(config["hooks"]["SubagentStart"]), 1)
        self.assertEqual(len(config["hooks"]["PostToolUse"]), 1)
        self.assertTrue((self.project / ".codex/hooks/subagent-start.py").is_file())
        self.assertFalse((self.project / ".codex/hooks/subagent-context.py").exists())

    def test_both_target_keeps_platform_files_separate(self):
        self.init_git()
        result = self.run_init("both")

        self.assertEqual(set(result["hooks_installed"]), {"claude", "codex"})
        self.assertTrue((self.project / ".claude/settings.json").is_file())
        self.assertTrue((self.project / ".codex/hooks.json").is_file())
        self.assertTrue((self.project / ".claude/hooks/subagent-context.py").is_file())
        self.assertTrue((self.project / ".codex/hooks/subagent-start.py").is_file())

    def test_codex_context_hooks_emit_the_correct_event_shapes(self):
        self.init_git()
        self.run_init("codex")
        (self.project / "docs/workflow.md").write_text(
            "Run tests before reporting completion.\n", encoding="utf-8"
        )

        for filename, event_name in (
            ("session-start.py", "SessionStart"),
            ("subagent-start.py", "SubagentStart"),
        ):
            result = subprocess.run(
                [sys.executable, str(self.project / ".codex/hooks" / filename)],
                check=True,
                capture_output=True,
                text=True,
            )
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], event_name)
            self.assertIn("Run tests before reporting completion", hook_output["additionalContext"])

    def test_context_uses_handoff_notes_and_frontmatter_completion_date(self):
        self.init_git()
        self.run_init("codex")
        active_dir = self.project / "docs/exec-plans/active/parser"
        active_dir.mkdir()
        (active_dir / "plan.md").write_text(
            """---
title: Parser
description: Implement parser
status: in-progress
date: 2026-08-20
---

# Parser

## Phases

### Phase 1: Parse

- [x] Implement

## Handoff Notes

Ready for the next agent.
""",
            encoding="utf-8",
        )
        completed_dir = self.project / "docs/exec-plans/completed/release"
        completed_dir.mkdir()
        completed_plan = completed_dir / "plan.md"
        completed_plan.write_text(
            """---
title: Release
description: Ship release
status: completed
date: 2020-01-02
summary: Released successfully
---
""",
            encoding="utf-8",
        )
        os.utime(completed_plan, None)

        result = subprocess.run(
            [sys.executable, str(self.project / ".codex/hooks/session-start.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]

        self.assertIn("Last handoff: Ready for the next agent.", context)
        self.assertIn("completed 2020-01-02", context)

    def test_codex_post_edit_hook_detects_apply_patch_commands(self):
        self.init_git()
        self.run_init("codex")
        plan_dir = self.project / "docs/exec-plans/active/example"
        plan_dir.mkdir()
        (plan_dir / "plan.md").write_text("# Missing frontmatter\n", encoding="utf-8")
        hook_input = json.dumps({
            "tool_input": {
                "patch": {
                    "body": "*** Update File: docs/exec-plans/active/example/plan.md"
                }
            }
        })

        result = subprocess.run(
            [sys.executable, str(self.project / ".codex/hooks/post-edit-validate.py")],
            input=hook_input,
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(result.stdout)

        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertIn("missing YAML frontmatter", output["hookSpecificOutput"]["additionalContext"])

    def test_codex_commands_work_from_a_nested_subdirectory(self):
        self.init_git()
        self.run_init("codex")
        (self.project / "docs/workflow.md").write_text(
            "Use upward project discovery.\n", encoding="utf-8"
        )
        nested = self.project / "src/package"
        nested.mkdir(parents=True)
        config = json.loads((self.project / ".codex/hooks.json").read_text(encoding="utf-8"))
        command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]

        result = subprocess.run(
            ["bash", "-c", command],
            cwd=nested,
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(result.stdout)

        self.assertIn(
            "Use upward project discovery",
            output["hookSpecificOutput"]["additionalContext"],
        )

    def test_codex_target_rejects_a_non_git_project(self):
        result = subprocess.run(
            [
                sys.executable,
                str(INIT_SCRIPT),
                "--root",
                str(self.project),
                "--target",
                "codex",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        error = json.loads(result.stderr)
        self.assertIn("Git repository root", error["error"])
        self.assertFalse((self.project / ".codex").exists())


if __name__ == "__main__":
    unittest.main()
