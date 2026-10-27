"""Runs skills/ask-team/hooks/merge-guard.py on every row of cases.tsv, the way Claude Code
calls it: the tool call as JSON on stdin, exit code 2 to refuse, 0 to allow.

Run: python3 -m unittest discover tests/merge-guard
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "..", "..", "skills", "ask-team", "hooks", "merge-guard.py")
CASES = os.path.join(HERE, "cases.tsv")


def run(*arguments, cwd):
    subprocess.run(arguments, cwd=cwd, check=True, capture_output=True)


def make_repo(root, name, default, workflow):
    """A repo whose origin/HEAD points at `default`, with that branch and feature-x."""
    path = os.path.join(root, name)
    os.makedirs(path)
    run("git", "init", "-q", "-b", default, cwd=path)
    run("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "start", cwd=path)
    run("git", "branch", "feature-x", cwd=path)
    run("git", "update-ref", f"refs/remotes/origin/{default}", "HEAD", cwd=path)
    run("git", "symbolic-ref", "refs/remotes/origin/HEAD", f"refs/remotes/origin/{default}", cwd=path)
    run("git", "branch", "tracking", cwd=path)
    run("git", "remote", "add", "origin", os.path.join(root, "nowhere.git"), cwd=path)
    run("git", "config", "branch.tracking.remote", "origin", cwd=path)
    run("git", "config", "branch.tracking.merge", f"refs/heads/{default}", cwd=path)
    run("git", "config", "alias.p", "push", cwd=path)
    run("git", "config", "alias.ship", f"!git push origin {default}", cwd=path)
    run("git", "config", "alias.g", "!git", cwd=path)
    for name, text in (("m.graphql", 'mutation { mergePullRequest(input: {pullRequestId: "x"}) { clientMutationId } }'),
                       ("q.json", '{"query": "mutation { mergePullRequest(input: {pullRequestId: \\"x\\"}) { clientMutationId } }"}'),
                       ("read.graphql", "query { viewer { login } }")):
        with open(os.path.join(path, name), "w", encoding="utf-8") as out:
            out.write(text)
    if workflow:
        os.makedirs(os.path.join(path, "docs"))
        with open(os.path.join(path, "docs", "project-map.md"), "w", encoding="utf-8") as out:
            out.write("# Project map: test\n")
    return path


def guard(event, cwd):
    done = subprocess.run([sys.executable, HOOK], input=event if isinstance(event, str) else json.dumps(event),
                          capture_output=True, text=True, cwd=cwd, timeout=20)
    return done.returncode, done.stderr


class MergeGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = tempfile.mkdtemp()
        cls.repos = {"workflow": make_repo(root, "workflow", "main", True),
                     "plain": make_repo(root, "plain", "main", False),
                     "trunk": make_repo(root, "trunk", "trunk", True)}

    def test_every_case(self):
        rows = [line.rstrip("\n").split("\t") for line in open(CASES, encoding="utf-8")
                if line.strip() and not line.startswith("#")]
        self.assertGreater(len(rows), 50)
        for expected, repo, branch, tool, *rest in rows:
            command = (rest[0] if rest else "").replace("\\n", "\n").replace("WORKFLOW", self.repos["workflow"])
            path = self.repos["trunk" if branch == "trunk" else repo]
            run("git", "checkout", "-q", branch, cwd=path)
            event = {"tool_name": tool, "cwd": path, "tool_input": {"command": command} if command else {}}
            with self.subTest(expected=expected, repo=repo, branch=branch, tool=tool, command=command):
                code, said = guard(event, path)
                self.assertEqual(code, 2 if expected == "refused" else 0, said)
                if expected == "refused":
                    self.assertIn("merge guard", said)

    def test_a_call_it_cannot_read_is_refused_only_in_a_workflow_project(self):
        self.assertEqual(guard("not json", self.repos["workflow"])[0], 2)
        self.assertEqual(guard("not json", self.repos["plain"])[0], 0)


if __name__ == "__main__":
    unittest.main()
