"""Runs skills/ask-team/scripts/test-guards.py on every case of cases.md, each in a fresh git
repo with the case's files on main and on a branch, and checks how it reads a PR's description.

Run: python3 -m unittest discover tests/test-guards
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "skills", "ask-team", "scripts", "test-guards.py")
CASES = os.path.join(HERE, "cases.md")
LISTED = re.compile(r"^- `(.+)` (deleted|newly skipped)(?: \((?:old|new) line \d+\))?: ")


def side(body, label):
    """A file's Before or After block, or None for (none)."""
    match = re.search(rf"^{label}:\n(?:\(none\)$|```\n(.*?)^```$)", body, re.M | re.S)
    if match is None:
        raise ValueError(f"no {label} block in {body!r}")
    return match.group(1)


def read_cases():
    """cases.md as {name: dict(arguments, files={path: (before, after)}, listed={(key, kind)})}."""
    with open(CASES, encoding="utf-8") as file:
        text = file.read()
    cases = {}
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        name, _, rest = block.partition("\n")
        arguments = re.search(r"^Arguments: (.+)$", rest, re.M)
        files = {path: (side(body, "Before"), side(body, "After"))
                 for path, body in re.findall(r"^File: ([^\n]+)\n(.*?)(?=^File: |^Listed: |\Z)", rest, re.M | re.S)}
        listed = set(re.findall(r"^Listed: (.+) (deleted|newly skipped)$", rest, re.M))
        cases[name.strip()] = dict(arguments=arguments.group(1).split() if arguments else [], files=files, listed=listed,
                                   nothing=bool(re.search(r"^Listed: nothing$", rest, re.M)))
    return cases


def git(*arguments, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *arguments], cwd=cwd, check=True,
                   capture_output=True)


def write(root, files, side):
    for path, sides in files.items():
        full = os.path.join(root, path)
        if sides[side] is None:
            if os.path.exists(full):
                os.remove(full)
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as file:
            file.write(sides[side])


def make_repo(root, files):
    """A repo with the files' before side on main and their after side on the branch pr, checked out."""
    git("init", "-q", "-b", "main", cwd=root)
    write(root, files, 0)
    git("add", "-A", cwd=root)
    git("commit", "-q", "--allow-empty", "-m", "base", cwd=root)
    git("checkout", "-q", "-b", "pr", cwd=root)
    write(root, files, 1)
    git("add", "-A", cwd=root)
    git("commit", "-q", "--allow-empty", "-m", "change", cwd=root)


def guards(root, *arguments, env=None):
    return subprocess.run([sys.executable, SCRIPT, "--base", "main", *arguments], cwd=root, capture_output=True,
                          text=True, env=env)


def listed(output):
    return {match.groups() for match in map(LISTED.match, output.splitlines()) if match}


class Cases(unittest.TestCase):
    def test_every_case(self):
        cases = read_cases()
        self.assertGreater(len(cases), 20)
        for name, case in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as root:
                self.assertTrue(case["files"], "a case needs at least one file")
                self.assertNotEqual(bool(case["listed"]), case["nothing"], "a case lists changes, or Listed: nothing")
                make_repo(root, case["files"])
                done = guards(root, *case["arguments"])
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(listed(done.stdout), case["listed"], done.stdout)


class Reasons(unittest.TestCase):
    """On the case where one change deletes test_remove and skips test_add."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        make_repo(self.root, read_cases()["A deletion and a skip in one change are both listed"]["files"])

    def tearDown(self):
        self.tmp.cleanup()

    def with_body(self, body):
        path = os.path.join(self.root, ".git", "body.md")
        with open(path, "w", encoding="utf-8") as file:
            file.write(body)
        return guards(self.root, "--body-file", path)

    def test_without_a_description_it_lists_each_change_with_a_placeholder_and_passes(self):
        done = guards(self.root)
        self.assertEqual(done.returncode, 0)
        self.assertIn("- `tests/test_cart.py::test_remove` deleted (old line 5): <one-line reason>", done.stdout)
        self.assertIn("- `tests/test_cart.py::test_add` newly skipped (new line 5): <one-line reason>", done.stdout)

    def test_every_change_with_its_reason_passes(self):
        done = self.with_body("## Tests\n\n- `tests/test_cart.py::test_remove` deleted: the feature it tested is gone\n"
                              "- `tests/test_cart.py::test_add` newly skipped: waits on the price service, ticket #12\n")
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_missing_reason_fails_and_names_the_change(self):
        done = self.with_body("- `tests/test_cart.py::test_remove` deleted: the feature it tested is gone\n")
        self.assertEqual(done.returncode, 1)
        self.assertIn("- `tests/test_cart.py::test_add` newly skipped (new line 5): <one-line reason>", done.stdout)
        self.assertNotIn("<one-line reason>", done.stdout.split("test_add")[0])

    def test_the_placeholder_is_not_a_reason(self):
        done = self.with_body("- `tests/test_cart.py::test_remove` deleted: <one-line reason>\n"
                              "- `tests/test_cart.py::test_add` newly skipped: <one-line reason>\n")
        self.assertEqual(done.returncode, 1)

    def test_a_change_named_with_no_text_after_it_has_no_reason(self):
        done = self.with_body("- `tests/test_cart.py::test_remove` deleted\n- `tests/test_cart.py::test_add` newly skipped:\n")
        self.assertEqual(done.returncode, 1)

    def test_a_longer_name_does_not_stand_for_a_shorter_one(self):
        done = self.with_body("- `tests/test_cart.py::test_remove_all` deleted: gone\n"
                              "- `tests/test_cart.py::test_add` newly skipped: waits on prices\n")
        self.assertEqual(done.returncode, 1)
        self.assertIn("test_remove` deleted (old line 5): <one-line reason>", done.stdout)

    def test_the_lines_the_guards_print_are_read_back_with_their_reasons(self):
        done = self.with_body("- `tests/test_cart.py::test_remove` deleted (old line 5): the feature is gone\n"
                              "- `tests/test_cart.py::test_add` newly skipped (new line 9): waits on prices\n")
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_longer_name_with_a_space_does_not_stand_for_a_shorter_one(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, {"src/cart.test.js": ('it("adds", () => {\n  add();\n});\n\n'
                                                  'it("adds two", () => {\n  add(2);\n});\n', "")})
            path = os.path.join(root, ".git", "body.md")
            with open(path, "w", encoding="utf-8") as file:
                file.write("- `src/cart.test.js::adds two` deleted: the two-item path is gone\n")
            done = guards(root, "--body-file", path)
            self.assertEqual(done.returncode, 1, done.stdout)
            self.assertIn("- `src/cart.test.js::adds` deleted (old line 1): <one-line reason>", done.stdout)
            with open(path, "a", encoding="utf-8") as file:
                file.write("- src/cart.test.js::adds: one item is added by the cart's own tests now\n")
            self.assertEqual(guards(root, "--body-file", path).returncode, 0)

    def test_a_path_inside_a_longer_path_does_not_stand_for_it(self):
        done = self.with_body("- `src/tests/test_cart.py::test_remove` deleted: gone\n"
                              "- `tests/test_cart.py::test_add` newly skipped: waits on prices\n")
        self.assertEqual(done.returncode, 1)

    def test_the_description_can_come_from_an_environment_variable(self):
        env = dict(os.environ, PR_BODY="- `tests/test_cart.py::test_remove` deleted: gone\n"
                                       "- `tests/test_cart.py::test_add` newly skipped: waits on prices\n")
        self.assertEqual(guards(self.root, "--body-env", "PR_BODY", env=env).returncode, 0)
        env["PR_BODY"] = ""
        self.assertEqual(guards(self.root, "--body-env", "PR_BODY", env=env).returncode, 1)

    def test_a_description_is_read_as_text_never_run(self):
        env = dict(os.environ, PR_BODY="$(touch ran) `touch ran`\n- `tests/test_cart.py::test_remove` deleted: gone")
        guards(self.root, "--body-env", "PR_BODY", env=env)
        self.assertFalse(os.path.exists(os.path.join(self.root, "ran")))

    def test_a_base_git_cannot_read_exits_2(self):
        done = subprocess.run([sys.executable, SCRIPT, "--base", "no-such-branch"], cwd=self.root, capture_output=True,
                              text=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn("cannot read the diff", done.stderr)


class NothingListed(unittest.TestCase):
    def test_a_change_with_no_test_deleted_or_skipped_passes_with_or_without_a_description(self):
        with tempfile.TemporaryDirectory() as root:
            make_repo(root, {"tests/test_cart.py": ("def test_add():\n    pass\n",
                                                    "def test_add():\n    pass\n\n\ndef test_remove():\n    pass\n")})
            self.assertEqual(guards(root).returncode, 0)
            empty = os.path.join(root, ".git", "body.md")
            open(empty, "w").close()
            done = guards(root, "--body-file", empty)
            self.assertEqual(done.returncode, 0)
            self.assertIn("no test deleted or newly skipped", done.stdout)


if __name__ == "__main__":
    unittest.main()
