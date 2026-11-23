#!/usr/bin/env python3
"""The test guards: list every test a pull request deletes and every test it newly skips, and
check that the PR's description gives each one a one-line reason.

An agent that builds a change also writes the tests that grade it, and agents are known to
delete or skip a failing test rather than fix the code. The guards scan the changed test files,
as they were where the branch left the base and as they are at the head, without running them,
so they work before any CI does. The developer reads each listed change and its reason before
merging. tests/test-guards/cases.md holds the cases they read and how they read them.

- Deleted: a test the old file defines and the new one does not, unless another test file now
  defines it with the same body. A test file taken away whole is listed once, as the file,
  unless every test in it has moved. A renamed test is listed under its old name.
- Newly skipped: a skip, or a focused test that turns off the rest of its file, that the new file
  holds and the old one did not hold on the same test. A test moved into a skipped group or
  file, or added there, is listed too.
- Changed: with --guard PATH, any change to that file, or to any file in that folder. CI names
  the guards' own script, its test_guards folder and the CI file that runs them.

They know Python, JavaScript and TypeScript, Go, the JVM languages, .NET, Ruby, Rust, PHP, Swift,
Elixir and Dart (test_guards/languages.py), but not every framework of those: not Go's Ginkgo,
not Spock's feature methods named in quotes, and not a test table written over several lines, as
`it.each([` with its rows below it.

They read text, so they catch the ways an agent deletes or skips a test in ordinary work, not a
change written to slip past them. Known gaps: a test's name kept in a one-line string or a Ruby
heredoc still counts as a test; a JavaScript regex after an operator or a keyword is read as a
division; a test turned off by code rather than a skip (`if False:`, `del test_x`, a nested test,
`__test__ = False`, a test wrapped in an if) is not seen, nor is RSpec's `before { skip }` or a
skip mark saved under a name in another file; a skip in a helper is listed under the helper's
name; a placeholder disguised with an escape, a link or an invisible character is taken as a
reason; and a line of the description that opens with ``` inside a code span, or after four
spaces, hides the reasons after it.

Each listed change prints as a line to paste into the PR's Tests section, its reason in place of
the placeholder:

    - `tests/test_cart.py::test_remove` deleted (old line 12): <one-line reason>

With --body-env or --body-file, a change has its reason when a line of the description shown on
the page has that shape with a real reason. In CI the description comes through an environment
variable, never pasted into the command.

Usage:
    test-guards.py [--base REF]       # list what HEAD changes; REF defaults to origin/HEAD
    test-guards.py --base REF --head PR --body-env PR_BODY --guard PATH ...

Exit code 0 when nothing is listed, every listed change has its reason, or no description was
given; 1 when a reason is missing; 2 when the guards cannot run.
"""
import argparse
import os
import sys


def main(argv=None):
    # The guards' parts sit in test_guards/ beside this script, found even under python -I.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_guards.changes import changed_guards, deleted_tests, skipped_tests
    from test_guards.reasons import PLACEHOLDER, reason
    from test_guards.repo import GitError, changed_files, git, read_file

    parser = argparse.ArgumentParser(description="List deleted and newly skipped tests; check each has a reason.")
    parser.add_argument("--base", default="origin/HEAD", help="the branch the PR merges into (default origin/HEAD)")
    parser.add_argument("--head", default="HEAD", help="the PR's commit (default HEAD)")
    parser.add_argument("--tests", action="append", default=[], metavar="GLOB",
                        help="another pattern for test files in the languages the guards know, such as "
                             "'checks/*.py'; may repeat")
    parser.add_argument("--guard", action="append", default=[], metavar="PATH",
                        help="a file or a folder whose every change is listed, as the guards' own files and CI "
                             "file; may repeat")
    body = parser.add_mutually_exclusive_group()
    body.add_argument("--body-env", metavar="NAME", help="the environment variable holding the PR's description")
    body.add_argument("--body-file", metavar="PATH", help="a file holding the PR's description")
    args = parser.parse_args(argv)
    try:
        start = git("merge-base", args.base, args.head).strip()
        files = changed_files(args.base, args.head)
        read_old = lambda path: read_file(start, path)
        read_new = lambda path: read_file(args.head, path)
        listed = ([(key, "changed", "changed") for key, _ in changed_guards(files, args.guard)]
                  + [(key, "deleted", f"deleted (old line {number})" if number else "deleted")
                     for key, number in deleted_tests(files, read_old, read_new, args.tests)]
                  + [(key, "newly skipped", f"newly skipped (new line {number})")
                     for key, number in skipped_tests(files, read_old, read_new, args.tests)])
    except GitError as error:
        print(f"test-guards: cannot read the diff from {args.base}: {error}", file=sys.stderr)
        return 2
    if not listed:
        print("Test guards: no test deleted or newly skipped.")
        return 0
    if args.body_env is None and args.body_file is None:
        print(f"Test guards: {len(listed)} change(s) need a one-line reason in the PR's Tests section:")
        for key, _, shown in listed:
            print(f"- `{key}` {shown}: {PLACEHOLDER}")
        return 0
    if args.body_file is not None:
        with open(args.body_file, encoding="utf-8", errors="replace") as file:
            text = file.read()
    else:
        text = os.environ.get(args.body_env, "")
    missing = []
    for key, kind, shown in listed:
        given = reason(text, key, kind)
        if given is None:
            missing.append((key, shown))
        else:
            print(f"- `{key}` {shown}: {given}")
    if not missing:
        print(f"Test guards: each of the {len(listed)} listed change(s) has its reason on the PR.")
        return 0
    print(f"Test guards: {len(missing)} change(s) have no reason on the PR. Add each line below to the PR's "
          "Tests section, with its one-line reason in place of the placeholder:")
    for key, shown in missing:
        print(f"- `{key}` {shown}: {PLACEHOLDER}")
    return 1


def run(argv=None):
    """main, with any failure it did not foresee exiting 2, never 1, which means a missing reason."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="backslashreplace")
    try:
        return main(argv)
    except Exception as error:  # noqa: BLE001: an unforeseen failure must not read as a missing reason.
        print(f"test-guards: could not run: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())
