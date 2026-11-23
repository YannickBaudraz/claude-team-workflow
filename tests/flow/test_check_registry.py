"""Unit tests for the deny rules skills/ask-team/scripts/check-registry.py reads, on an invented
registry, home and plugin only.

Run: python3 -m unittest discover tests/flow
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "skills", "ask-team", "scripts")

REGISTRY = """# Registry

| Command | Source | Visibility | Used at | Calls | Arguments | Does |
|---|---|---|---|---|---|---|
| `pl:other` | `them/repo` | auto | any time |  |  | Something else. |
{extra}
## Denied duplicates

| Command | Source | Visibility | Denied in | Duplicates |
|---|---|---|---|---|
| `pl:tdd` | `them/repo` | denied | {denied_in} | test-driven-development |
"""
GUARD_HOOK = {"PreToolUse": [{"matcher": "", "hooks": [
    {"type": "command", "command": "python3 merge-guard.py", "onFailure": "block"}]}]}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text if isinstance(text, str) else json.dumps(text))


def problems(extra_row="", user_deny=(), template_deny=("Skill(pl:tdd)",), denied_in="project settings",
             tdd_front="", overrides=None):
    """The PROBLEM lines check-registry.py prints for a registry with the plugin pl, from the
    marketplace in them/repo, whose tdd is denied where `denied_in` says."""
    root = tempfile.mkdtemp()
    try:
        repo, home = os.path.join(root, "repo"), os.path.join(root, "home")
        ask_team = os.path.join(repo, "skills", "ask-team")
        for script in ("check-registry.py", "flow.py"):
            os.makedirs(os.path.join(ask_team, "scripts"), exist_ok=True)
            shutil.copy(os.path.join(SCRIPTS, script), os.path.join(ask_team, "scripts", script))
        write(os.path.join(ask_team, "scripts", "check-contracts.py"), "")
        for router in ("SKILL.md", "ROUTER.md", "FLOW.md"):
            write(os.path.join(ask_team, router), "# Router\n")
        write(os.path.join(ask_team, "REGISTRY.md"), REGISTRY.format(extra=extra_row, denied_in=denied_in))
        write(os.path.join(ask_team, "templates", "claude-settings.json"),
              {"permissions": {"deny": ["Bash(gh pr merge *)", *template_deny]}})
        plugin = os.path.join(home, "plugin")
        for skill in ("tdd", "other"):
            front = tdd_front if skill == "tdd" else ""
            write(os.path.join(plugin, "skills", skill, "SKILL.md"), f"---\nname: {skill}\n{front}---\n")
        write(os.path.join(home, ".claude", "settings.json"),
              {"permissions": {"deny": list(user_deny)}, "enabledPlugins": {"pl@mp": True}, "hooks": GUARD_HOOK,
               "skillOverrides": overrides or {}})
        write(os.path.join(home, ".claude", "plugins", "known_marketplaces.json"),
              {"mp": {"source": {"source": "github", "repo": "them/repo"}}})
        write(os.path.join(home, ".claude", "plugins", "installed_plugins.json"),
              {"plugins": {"pl@mp": [{"installPath": plugin}]}})
        out = subprocess.run([sys.executable, os.path.join(ask_team, "scripts", "check-registry.py")],
                             capture_output=True, text=True, env={**os.environ, "HOME": home})
        return [line[len("PROBLEM "):] for line in out.stdout.splitlines() if line.startswith("PROBLEM ")]
    finally:
        shutil.rmtree(root)


class DeniedPerProject(unittest.TestCase):
    def test_a_registry_that_matches_its_settings_passes(self):
        self.assertEqual(problems(), [])

    def test_a_row_for_the_same_skill_by_another_name_is_reported(self):
        # Claude Code blocks a call to the bare name too: the rule matches the skill the call resolves to.
        found = problems(extra_row="| `tdd` | `them/repo` | auto | any time |  |  | Test-first work. |")
        self.assertEqual(found, ["tdd: is the same skill as pl:tdd, which templates/claude-settings.json "
                                 "denies, so workflow projects block it too"])

    def test_a_skill_also_denied_on_the_whole_machine_is_reported(self):
        self.assertEqual(problems(user_deny=["Skill(pl:tdd)"]),
                         ["pl:tdd: denied in project settings only, but settings and frontmatter "
                          "make it denied everywhere"])

    def test_a_skill_its_frontmatter_makes_command_only_is_reported(self):
        self.assertEqual(problems(tdd_front="disable-model-invocation: true\n"),
                         ["pl:tdd: denied in project settings only, but settings and frontmatter "
                          "make it typed everywhere"])

    def test_a_skill_hidden_on_the_whole_machine_is_reported(self):
        self.assertEqual(problems(overrides={"tdd": "user-invocable-only"}),
                         ["pl:tdd: denied in project settings only, but settings and frontmatter "
                          "make it hidden everywhere"])

    def test_a_skill_overridden_on_the_whole_machine_is_reported(self):
        self.assertEqual(problems(overrides={"tdd": "off"}),
                         ["pl:tdd: denied in project settings only, but ~/.claude/settings.json "
                          "sets skillOverrides tdd to off everywhere"])


class DeniedOnTheMachine(unittest.TestCase):
    def test_a_row_for_the_same_skill_by_another_name_is_reported(self):
        # The user settings deny pl:tdd by its row's name; the bare tdd row resolves to the same file.
        found = problems(extra_row="| `tdd` | `them/repo` | auto | any time |  |  | Test-first work. |",
                         user_deny=["Skill(pl:tdd)"], template_deny=(), denied_in="user settings")
        self.assertEqual(found, ["tdd: registry says auto, settings and frontmatter say denied"])


class TemplateRules(unittest.TestCase):
    def test_a_rule_that_names_no_single_row_is_reported(self):
        for rule in ("Skill", "Skill(*)", "Skill(pl:*)"):
            with self.subTest(rule=rule):
                self.assertEqual(problems(template_deny=["Skill(pl:tdd)", rule]),
                                 [f"templates/claude-settings.json denies {rule}, "
                                  "which is not one registry row denied in project settings"])

    def test_a_rule_without_its_row_is_reported(self):
        self.assertEqual(problems(template_deny=["Skill(pl:tdd)", "Skill(pl:review)"]),
                         ["templates/claude-settings.json denies Skill(pl:review), "
                          "which is not one registry row denied in project settings"])


if __name__ == "__main__":
    unittest.main()
