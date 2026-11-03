#!/usr/bin/env python3
"""CI's test guards: list every test a pull request deletes and every test it newly skips, and
check that the PR's description gives each one a one-line reason.

An agent that builds a change also writes the tests that grade it, and agents are known to
delete or skip a failing test rather than fix the code. These two guards are plain scans of the
diff, so they work on any stack, and the developer reads each listed change and its reason
before merging, as the PR template's reading list says.

It reads `git diff <base>...HEAD` and the files on both sides of it. A file is a test file
when its name follows a test convention (test_cart.py, cart_test.go, cart.test.ts,
CartTest.java, cart_spec.rb) or it sits under a test folder (test, tests, __tests__, spec,
specs), and it is source code; a Rust file always is, since Rust keeps unit tests beside the
code. --tests adds glob patterns for a stack these miss.

- Deleted: a test whose definition the diff removes and does not add back. A test whose file
  adds a test of the same name is kept, as when its signature or body is edited; one that
  another file adds with the same body has moved. Each added test stands for one removed test,
  so a common name such as 'renders' added once does not cover two removals. A commented-out
  test counts as removed, and so does a test whose marker alone goes (@Test, #[test], [Fact]).
  A renamed test is listed under its old name: a diff cannot tell a rename from a deletion. A
  test file taken away whole is listed once, as the file, unless every test in it has moved: one
  deleted, or renamed so it is no longer a test file (test_cart.py.disabled, a move out of the
  test folder). Lines inside a block comment, or inside a Python triple-quoted string, are still
  read as code unless they start with a comment mark, so a test wrapped in one is not listed.
- Newly skipped: a skip marker the diff adds (pytest's skip, skipif and xfail, unittest's skip,
  it.skip, xit, t.Skip, @Disabled, [Ignore], #[ignore], markTestSkipped and their kin), unless
  the diff removes the same line in the same file, as when code moves; a skip word in a comment
  is not a skip. It is named after the test or the group it skips, or after its file when it
  skips the whole file.

It knows the conventions of Python, JavaScript and TypeScript, Go, the JVM languages, .NET,
Ruby, Rust, PHP, Swift, Elixir and Dart. tests/test-guards/cases.md has cases for each, Java
standing for the JVM languages and C# for .NET.

Each listed change prints as a line to paste into the PR's Tests section, with the line to read
in the diff (in the old file for a deletion, the new one for a skip) and its reason in place of
the placeholder:

    - `tests/test_cart.py::test_remove` deleted (old line 12): <one-line reason>
    - `tests/test_cart.py::test_total` newly skipped (new line 30): <one-line reason>

With --body-env or --body-file, it also reads the PR's description: a change has its reason
when a line of the description names it whole and has text after it other than the placeholder.
The line numbers may go or be out of date there; the name is what counts.

Usage:
    test-guards.py [--base REF]                    # list; REF defaults to origin/HEAD
    test-guards.py --base REF --body-env PR_BODY   # in CI: also fail when a reason is missing

Exit code 0 when nothing is listed, or every listed change has its reason or no description was
given; 1 when a reason is missing; 2 when git cannot read the diff.

In CI the description comes through an environment variable, never pasted into the command,
so its text is never run, and the job runs again when the description is edited.
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from collections import Counter

TEST_FOLDERS = {"test", "tests", "__tests__", "spec", "specs"}
# A file's name without its extension: test_cart, cart_test, cart.test, cart-spec, CartTest, CartTests, CartSpec, CartIT.
TEST_NAME = re.compile(r"^test_|[._-](test|spec)$|[a-z0-9](Tests?|Spec|IT)$")

# Each language's file extensions, how a test is defined in it, and how a test is skipped.
# "named": a line that defines a test and names it; the first group that matched is the name.
# "group": a line that names a group of tests (a class, a describe block), used to name a skip.
# "marker": a line that marks the next declaration as a test; "declaration" names it.
# "comment": a line that is a comment, so defines and skips nothing; "doc_marker": a marker
# written in a comment, as PHPUnit's @test.
C_COMMENT = r"^\s*(?://|/\*|\*)"
HASH_COMMENT = r"^\s*#"
QUOTED = r"""\s*\(?\s*(?:'([^']*)'|"([^"]*)"|`([^`]*)`)"""
LANGUAGES = {
    "python": dict(
        comment=HASH_COMMENT,
        extensions={".py"},
        named=[r"^\s*(?:async\s+)?def\s+(test\w*)\s*\("],
        group=[r"^\s*class\s+(\w+)\s*[(:]"],
        skips=[r"@pytest\.mark\.(?:skip|skipif|xfail)\b", r"\bpytest\.(?:skip|xfail)\s*\(",
               r"@(?:unittest\.)?(?:skip|skipIf|skipUnless|expectedFailure)\b", r"\.skipTest\s*\(",
               r"\braise\s+(?:unittest\.)?SkipTest\b", r"^\s*pytestmark\s*=.*\b(?:skip|skipif|xfail)\b"]),
    "javascript": dict(
        comment=C_COMMENT,
        extensions={".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte"},
        named=[r"(?<![\w$.])x?(?:it|test|specify)(?:\.\w+)*" + QUOTED],
        group=[r"(?<![\w$.])x?(?:describe|context|suite)(?:\.\w+)*" + QUOTED],
        skips=[r"(?<![\w$.])(?:it|test|describe|context|suite|specify)\.(?:skip|todo|fixme)\b",
               r"(?<![\w$.])x(?:it|test|describe|context|specify)\s*\(", r"(?<![\w$.])pending\s*\("]),
    "go": dict(
        comment=C_COMMENT,
        extensions={".go"},
        named=[r"^\s*func\s+((?:Test|Fuzz|Example)\w*)\s*\("],
        skips=[r"\b\w+\.Skip(?:f|Now)?\s*\("]),
    "jvm": dict(
        comment=C_COMMENT,
        extensions={".java", ".kt", ".kts", ".scala", ".groovy"},
        named=[r"^\s*(?:test|it|should)" + QUOTED],
        group=[r"^\s*(?:public\s+|internal\s+|abstract\s+)*(?:class|object)\s+(\w+)"],
        marker=[r"@(?:Test|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate)\b"],
        declaration=[r"\b(?:void|fun|def)\s+(`[^`]+`|\w+)\s*[(<]"],
        skips=[r"@Disabled\w*\b", r"@Ignore\b"]),
    "dotnet": dict(
        comment=r"^\s*(?://|/\*|\*|\(\*|')",
        extensions={".cs", ".fs", ".vb"},
        group=[r"^\s*(?:public\s+|internal\s+|sealed\s+|static\s+|partial\s+)*class\s+(\w+)"],
        marker=[r"\[\s*(?:Test|TestCase|Fact|Theory|TestMethod|DataTestMethod)\b"],
        declaration=[r"\b(?:void|Task|let|Sub)\s+(``[^`]+``|\w+)\s*[(<]"],
        skips=[r"\[\s*(?:Ignore|Explicit)\b", r"\bSkip\s*=\s*\""]),
    "ruby": dict(
        comment=HASH_COMMENT,
        extensions={".rb"},
        named=[r"^\s*(?:it|specify|example|scenario|test|xit|xspecify)" + QUOTED, r"^\s*def\s+(test_\w+)"],
        group=[r"^\s*x?(?:describe|context|feature)\s+(?:'([^']*)'|\"([^\"]*)\"|(\w[\w:]*))", r"^\s*class\s+(\w+)"],
        skips=[r"^\s*(?:skip|pending)\b", r"^\s*x(?:it|describe|context|specify)\b"]),
    "rust": dict(
        comment=C_COMMENT,
        extensions={".rs"},
        marker=[r"#\[(?:\w+::)?test\b"],
        declaration=[r"\bfn\s+(\w+)\s*[(<]"],
        skips=[r"#\[ignore\b"]),
    "php": dict(
        comment=r"^\s*(?://|/\*|\*|#(?!\[))",
        extensions={".php"},
        named=[r"\bfunction\s+(test\w*)\s*\("],
        group=[r"^\s*(?:final\s+|abstract\s+)*class\s+(\w+)"],
        marker=[r"#\[Test\]"],
        doc_marker=[r"@test\b"],
        declaration=[r"\bfunction\s+(\w+)\s*\("],
        skips=[r"\bmarkTest(?:Skipped|Incomplete)\s*\(", r"#\[(?:Skip|Ignore)\w*\b"]),
    "swift": dict(
        comment=C_COMMENT,
        extensions={".swift"},
        named=[r"\bfunc\s+(test\w*)\s*\("],
        group=[r"^\s*(?:final\s+)?class\s+(\w+)"],
        marker=[r"@Test\b"],
        declaration=[r"\bfunc\s+(\w+)\s*[(<]"],
        skips=[r"\bXCTSkip\w*\b", r"\.disabled\s*\("]),
    "elixir": dict(
        comment=HASH_COMMENT,
        extensions={".ex", ".exs"},
        named=[r"^\s*test\s+\"([^\"]*)\""],
        group=[r"^\s*describe\s+\"([^\"]*)\""],
        skips=[r"@(?:module)?tag\s+:?skip\b", r"@tag\s+skip:"]),
    "dart": dict(
        comment=C_COMMENT,
        extensions={".dart"},
        named=[r"(?<![\w.])(?:test|testWidgets)" + QUOTED],
        group=[r"(?<![\w.])group" + QUOTED],
        skips=[r"\bskip:\s*(?:true|'|\")"]),
}
for language in LANGUAGES.values():
    for kind in ("named", "group", "marker", "doc_marker", "declaration", "skips"):
        language[kind] = [re.compile(pattern) for pattern in language.get(kind, [])]
    language["comment"] = re.compile(language["comment"])
# How far a marker or a skip decorator may sit above the declaration it applies to.
REACH = 6
PLACEHOLDER = "<one-line reason>"


class GitError(Exception):
    pass


def git(*args):
    done = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, text=True)
    if done.returncode:
        raise GitError(done.stderr.strip() or f"git {' '.join(args)} failed")
    return done.stdout


def language_of(path):
    extension = os.path.splitext(path)[1].lower()
    return next((name for name, language in LANGUAGES.items() if extension in language["extensions"]), None)


def by_name(path):
    """Whether a file's own name says it holds tests."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return bool(TEST_NAME.search(stem))


def is_test_file(path, extra=()):
    if not path or language_of(path) is None:
        return False
    if language_of(path) == "rust" or by_name(path):
        return True
    folders = path.split("/")[:-1]
    return any(folder in TEST_FOLDERS for folder in folders) or any(fnmatch.fnmatch(path, glob) for glob in extra)


def unquote(path):
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1").decode("utf-8")
    return path


def parse(diff):
    """A unified diff's files, each as dict(old, new, copy, removed, added): old and new are paths
    or None for an added or deleted file; copy is whether new is a copy of old, which stays;
    removed and added are lists of (line number, text), the line number in the old file for
    removed lines and in the new file for added ones."""
    files, current, header, old_line, new_line = [], None, False, 0, 0
    for line in diff.split("\n"):
        if line.startswith("diff --git "):
            current, header = dict(old=None, new=None, copy=False, removed=[], added=[]), True
            files.append(current)
        elif current is None:
            continue
        elif header and line.startswith("--- "):
            path = unquote(line[4:].rstrip("\t"))
            current["old"] = None if path == "/dev/null" else path[2:]
        elif header and line.startswith("+++ "):
            path = unquote(line[4:].rstrip("\t"))
            current["new"] = None if path == "/dev/null" else path[2:]
        elif header and line.startswith(("rename from ", "copy from ")):
            current["old"] = unquote(line.split(" from ", 1)[1])
            current["copy"] = line.startswith("copy ")
        elif header and line.startswith(("rename to ", "copy to ")):
            current["new"] = unquote(line.split(" to ", 1)[1])
        elif line.startswith("@@"):
            header = False
            numbers = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            old_line, new_line = int(numbers.group(1)), int(numbers.group(2))
        elif header:
            continue
        elif line.startswith("-"):
            current["removed"].append((old_line, line[1:]))
            old_line += 1
        elif line.startswith("+"):
            current["added"].append((new_line, line[1:]))
            new_line += 1
        elif line.startswith(" "):
            old_line += 1
            new_line += 1
    return files


def first_group(match):
    return next((group for group in match.groups() if group is not None), "").strip("`").strip()


def named(language, text, kinds=("named",)):
    for kind in kinds:
        for pattern in language[kind]:
            match = pattern.search(text)
            if match:
                return first_group(match)
    return None


def is_comment(language, text):
    return bool(language["comment"].match(text))


def is_marker(language, text):
    kind = "doc_marker" if is_comment(language, text) else "marker"
    return any(pattern.search(text) for pattern in language[kind])


def declared_below(language, whole, number):
    """The declaration a marker on line `number` (1-based) of a file's lines applies to, as
    (line number, name), or None."""
    for below, text in enumerate(whole[number:number + REACH], start=number + 1):
        name = None if is_comment(language, text) else named(language, text, ("declaration",))
        if name:
            return below, name
    return None


def marked_above(language, whole, number):
    """Whether a marker sits above line `number` (1-based) of a file's lines, with only
    annotations, attributes and comments between them."""
    for text in reversed(whole[max(0, number - 1 - REACH):number - 1]):
        if is_marker(language, text):
            return True
        if not is_attachment(text):
            return False
    return False


def body(lines, index):
    """The stripped lines of the test that starts at lines[index], as far as lines hold it
    unbroken: the lines indented under its first line, and the one closing it."""
    number, first = lines[index]
    depth, own = indent(first), [first.strip()]
    for next_number, text in lines[index + 1:]:
        if next_number != number + 1:
            break
        number, stripped = next_number, text.strip()
        if not stripped:
            continue
        if indent(text) > depth:
            own.append(stripped)
            continue
        if indent(text) == depth and (stripped[0] in ")]}" or re.match(r"end\b", stripped)):
            own.append(stripped)
        break
    return tuple(own)


def definitions(language, lines, whole=lambda: []):
    """The tests that lines define, in order, as (name, body, line number): lines as (number, text), not
    necessarily contiguous. A comment defines nothing, so a test commented out counts as removed.
    whole() gives the file's lines, to pair a marker and its declaration when only one of them is
    among lines: a marker removed alone, or a declaration renamed under a marker that stays."""
    found, marked, numbers, counted, file = [], None, {number for number, _ in lines}, set(), None
    for index, (number, text) in enumerate(lines):
        if is_marker(language, text):
            name = None if is_comment(language, text) else named(language, text, ("declaration",))
            if name:
                found.append((name, body(lines, index), number))
                marked = None
                continue
            if file is None:
                file = whole()
            declared = declared_below(language, file, number)
            if declared is None or declared[0] in numbers:
                marked = number
            elif declared[0] not in counted:
                counted.add(declared[0])
                found.append((declared[1], (), declared[0]))
            continue
        if is_comment(language, text):
            continue
        name = named(language, text)
        if name:
            found.append((name, body(lines, index), number))
            marked = None
            continue
        name = named(language, text, ("declaration",)) if language["marker"] or language["doc_marker"] else None
        if not name:
            continue
        if marked is not None and number - marked <= REACH:
            found.append((name, body(lines, index), number))
            marked = None
            continue
        if file is None:
            file = whole()
        if marked_above(language, file, number):
            found.append((name, body(lines, index), number))
    return found


def is_attachment(text):
    """A line that may sit between a skip decorator and what it skips: a decorator, an
    annotation or attribute, a comment, or a blank line."""
    stripped = text.strip()
    return not stripped or stripped[0] in "@#[/*" or stripped.startswith("--")


def indent(text):
    return len(text) - len(text.lstrip())


def skipped_name(language, lines, number):
    """What the skip on line `number` (1-based) of a file's lines skips: the test or group on its
    line, below it when the skip is a decorator or an annotation, or around it when it sits in
    its body. None for the whole file."""
    text = lines[number - 1]
    name = named(language, text, ("named", "group"))
    if name:
        return name
    if not text.strip():
        return None
    if is_attachment(text):
        for below in lines[number:number + REACH]:
            name = named(language, below, ("named", "group", "declaration"))
            if name:
                return name
            if not is_attachment(below):
                break
    # A skip on a closing line, as Dart's `}, skip: true);`, belongs to the block it closes.
    depth = indent(text) + (text.strip()[0] in ")]}")
    for above in reversed(lines[:number - 1]):
        if above.strip() in ("", "{") or indent(above) >= depth:
            continue
        name = named(language, above, ("named", "group", "declaration"))
        if name:
            return name
        depth = indent(above)
    return None


def lines_at(commit, path):
    try:
        return git("show", f"{commit}:{path}").splitlines()
    except GitError:
        return []


def head_lines(path):
    return lines_at("HEAD", path)


def tests_in(path, lines, read, extra):
    if not is_test_file(path, extra):
        return []
    return definitions(LANGUAGES[language_of(path)], lines, lambda: read(path))


def unpaired(tests, pool, key):
    """The tests that find no match in pool, a Counter of keys; each match uses one up."""
    left = []
    for test in tests:
        if pool[key(test)]:
            pool[key(test)] -= 1
        else:
            left.append(test)
    return left


def stops_being_tests(entry, extra):
    """Whether a diff entry takes a test file away: deletes it, or renames it to a path that is
    not a test file, as cart_test.py.disabled or a move out of the test folder."""
    return is_test_file(entry["old"], extra) and not entry["copy"] and not is_test_file(entry["new"], extra)


def deleted_tests(files, extra=(), read_old=lambda path: [], read_new=head_lines):
    """Every deleted test as (path::name, its line in the old file), or (path, None) for a test
    file taken away whole. A removed test is kept when its file adds a test of that name, as when
    its signature or body is edited, and moved when another file adds a test of that name with
    the same body; each added test stands for one removed test. read_old and read_new give a
    file's lines on each side of the diff."""
    name = lambda test: test[0]
    same = lambda test: test[:2]
    sides, spare = [], Counter()
    for entry in files:
        old_lines = entry["removed"]
        if entry["new"] is not None and stops_being_tests(entry, extra):
            # A rename shows only the lines it edits, yet every test in the old file stops running.
            old_lines = list(enumerate(read_old(entry["old"]), start=1)) or old_lines
        removed = tests_in(entry["old"], old_lines, read_old, extra)
        added = tests_in(entry["new"], entry["added"], read_new, extra)
        sides.append((entry, removed, unpaired(removed, Counter(map(name, added)), name)))
        spare.update(map(same, unpaired(added, Counter(map(name, removed)), name)))
    found = []
    for entry, removed, gone in sides:
        gone = unpaired(gone, spare, same)
        if stops_being_tests(entry, extra):
            if gone or (not removed and by_name(entry["old"])):
                found.append((entry["old"], None))
            continue
        first = {}
        for test, _, number in gone:
            first.setdefault(test, number)
        found.extend((f"{entry['old']}::{test}", number) for test, number in first.items())
    return found


def skipped_tests(files, extra=(), read=head_lines):
    """Every newly skipped test, as (path::name, the skip's line in the new file), or the path in
    place of path::name when the whole file is skipped."""
    found = []
    for entry in files:
        path = entry["new"]
        if not is_test_file(path, extra):
            continue
        language = LANGUAGES[language_of(path)]
        skips = lambda text: not is_comment(language, text) and any(p.search(text) for p in language["skips"])
        removed = [text.strip() for _, text in entry["removed"] if skips(text)]
        lines = None
        for number, text in entry["added"]:
            if not skips(text):
                continue
            if text.strip() in removed:
                removed.remove(text.strip())
                continue
            if lines is None:
                lines = read(path)
            name = skipped_name(language, lines, number) if 0 < number <= len(lines) else None
            found.append((f"{path}::{name}" if name else path, number))
    first = {}
    for key, number in found:
        first.setdefault(key, number)
    return list(first.items())


KIND = r"\(?(?:deleted|newly skipped|skipped)\)?"
WHERE = r"\((?:old |new )?line \d+\)"


def reason(body, key):
    """The reason the description gives for key, or None. The key must stand whole: closed by its
    backtick, or followed by its kind, its line or a separator, so `adds` is not read in
    `adds two` nor `test_remove` in `test_remove_all`."""
    named_here = re.compile(r"(?<![\w./-])" + re.escape(key)
                            + rf"(?=`|\s+{KIND}|\s+{WHERE}|\s*:(?!:)|\s+[-–—]|\s*[–—])")
    for line in body.splitlines():
        match = named_here.search(line)
        if not match:
            continue
        rest = line[match.end():].replace("`", "")
        rest = re.sub(rf"^\s*(?:{KIND})?\s*(?:{WHERE})?\s*[:\-–—]*\s*", "", rest)
        if rest.strip() and not rest.lstrip().startswith("<"):
            return rest.strip()
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="List deleted and newly skipped tests; check each has a reason.")
    parser.add_argument("--base", default="origin/HEAD", help="the branch the PR merges into (default origin/HEAD)")
    parser.add_argument("--tests", action="append", default=[], metavar="GLOB",
                        help="another pattern for test files, such as 'checks/*.py'; may repeat")
    body = parser.add_mutually_exclusive_group()
    body.add_argument("--body-env", metavar="NAME", help="the environment variable holding the PR's description")
    body.add_argument("--body-file", metavar="PATH", help="a file holding the PR's description")
    args = parser.parse_args(argv)
    try:
        start = git("merge-base", args.base, "HEAD").strip()
        files = parse(git("diff", "--no-color", "--no-ext-diff", "--no-textconv", "--find-renames",
                          "--src-prefix=a/", "--dst-prefix=b/", f"{args.base}...HEAD"))
    except GitError as error:
        print(f"test-guards: cannot read the diff from {args.base}: {error}", file=sys.stderr)
        return 2
    listed = [(key, f"deleted (old line {number})" if number else "deleted")
              for key, number in deleted_tests(files, args.tests, lambda path: lines_at(start, path))] + [
        (key, f"newly skipped (new line {number})") for key, number in skipped_tests(files, args.tests)]
    if not listed:
        print("Test guards: no test deleted or newly skipped.")
        return 0
    if args.body_env is None and args.body_file is None:
        print(f"Test guards: {len(listed)} test change(s) need a one-line reason in the PR's Tests section:")
        for key, kind in listed:
            print(f"- `{key}` {kind}: {PLACEHOLDER}")
        return 0
    if args.body_file is not None:
        with open(args.body_file, encoding="utf-8") as file:
            text = file.read()
    else:
        text = os.environ.get(args.body_env, "")
    missing = [(key, kind) for key, kind in listed if reason(text, key) is None]
    for key, kind in listed:
        if (key, kind) not in missing:
            print(f"- `{key}` {kind}: {reason(text, key)}")
    if not missing:
        print(f"Test guards: each of the {len(listed)} listed test change(s) has its reason on the PR.")
        return 0
    print(f"Test guards: {len(missing)} test change(s) have no reason on the PR. Add each line below to the PR's "
          "Tests section, with its one-line reason in place of the placeholder:")
    for key, kind in missing:
        print(f"- `{key}` {kind}: {PLACEHOLDER}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
