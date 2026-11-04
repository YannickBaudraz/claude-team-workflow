#!/usr/bin/env python3
"""The test guards: list every test a pull request deletes and every test it newly skips, and
check that the PR's description gives each one a one-line reason.

An agent that builds a change also writes the tests that grade it, and agents are known to
delete or skip a failing test rather than fix the code. These two guards are plain scans of the
changed files, so they work on any stack, and the developer reads each listed change and its
reason before merging, as the PR template's reading list says.

It takes the files `git diff <base>...<head>` changes, and reads each changed test file whole,
as it was where the branch left the base and as it is at the head. The diff's own text is never
read, so a .gitattributes line that shows a file as binary hides nothing. A file is a test file
when its name follows a test convention (test_cart.py, cart_test.go, cart.test.ts, cart.cy.ts,
CartTest.java, cart_spec.rb, Django's tests.py) or it sits under a test folder (test, tests,
__tests__, spec, specs in any case, or a folder named after its tests, as SwiftPM's
Tests/AppTests or .NET's Shop.Tests), and it is source code in one of the languages below; a Go
file only when it ends in _test.go, since go test runs no other, and a Rust file always, since
Rust keeps unit tests beside the code. --tests adds glob patterns for test files in those
languages that the conventions miss, such as 'checks/*.py'.

Comments, block comments included, and strings that span lines (Python's triple-quoted strings,
template literals) define nothing and skip nothing, so a test commented out or wrapped in one
counts as removed, and a skip word written in one is not a skip. A JavaScript regex literal is
read as one, so a slash-star or a backtick inside it opens no comment and no string.

- Deleted: a test the old file defines and the new one does not. A test whose file still
  defines a test of its name is kept, as when its signature or body is edited; one that another
  file now defines with the same body has moved. Each test stands for one of its name, so a
  common name such as 'renders' added once does not cover two removals. A test whose marker
  alone goes (@Test, #[test], [Fact]) counts as removed, and so does a test in a pytest class
  renamed off its Test prefix, which pytest stops collecting. A renamed test is listed under its
  old name: the files cannot tell a rename from a deletion. A test file taken away whole is
  listed once, as the file, unless every test in it has moved: one deleted, or renamed so it is
  no longer a test file (test_cart.py.disabled, a move out of the test folder), or so only its
  folder makes it one when its name did before (tests/test_cart.py to tests/cart_checks.py,
  which pytest does not collect). A test from a file named as a test file has moved only into
  another file named as one.
- Newly skipped: a skip the new file holds that the old one did not hold on the same test
  (pytest's skip, skipif, xfail and importorskip, as a decorator, in a pytestmark list or on one
  case of a parametrize; unittest's skip, it.skip, it.skipIf, xit, Mocha's this.skip(),
  test.describe.skip, t.Skip, a //go:build line, @Disabled, @EnabledOnOs and the other
  @Enabled conditions, JUnit's assumeTrue, @Test(enabled = false), [Ignore], #[ignore], a Swift
  Testing .disabled trait, skip: metadata, markTestSkipped). A focused test or group (it.only,
  describe.only, Jasmine's fit and fdescribe) turns off every other test in its file, so it
  counts as a skip of the whole file. A skip that moves with its test within its group is not
  listed; one put on another test is, even one of the same name in another class or describe
  block. Two cases are listed although no test was newly turned off, the price of telling a
  skip moved from one test to another: a skipped test moved with its skip into another group or
  file, and a test that a skip already there now covers, at its own line, as a test moved into
  a skipped class or describe block, or added to a file skipped whole. A skip is named after the
  test or the group it skips, with the groups around it, as
  tests/test_shop.py::TestCart::test_empty, or after its file when it skips the whole file, as a
  pytestmark, an importorskip at the top of a module or a //go:build line do; a decorator written
  over several lines, as black writes a skipif with a reason, is read from its first line to the
  one that closes it. A skip inside a helper function or a pytest fixture is named after that
  function, unless the function sits inside a test, whose skip it then is. It covers no other
  test of its file, so a test added beside it is not listed, even beside an autouse fixture
  that skips every test of the file; a set-up function's skip (setUp, setup_method, Ruby's
  setup) covers its class or file. A pytest mark saved under a name, as
  `requires_db = pytest.mark.skipif(...)`, skips nothing where it is written: each
  `@requires_db` is a skip of its test, a pytestmark that names it is a skip of the file, and a
  change to the line that saves it is listed under its name, as tests/test_db.py::requires_db.
- Changed: with --guard PATH, any change to that file. CI names the guards' own script and the
  CI file that runs them, so a pull request that edits the check reading it is listed too.

It knows the conventions of Python, JavaScript and TypeScript, Go, the JVM languages, .NET,
Ruby, Rust, PHP, Swift, Elixir and Dart. tests/test-guards/cases.md has cases for each, Java
standing for the JVM languages and C# for .NET. Some frameworks of those languages are not
read: in Go, it reads the testing package and testify, not Ginkgo's It and Skip; in Groovy,
JUnit's annotations, not Spock's feature methods named in quotes. A test table written over
several lines, as `it.each([` with its rows below it, is not read as a test.

The guards read text, so they catch the ways an agent deletes or skips a test in ordinary work,
by mistake or by habit. They do not stop a change written to slip past them: that is for the
review and for the developer's own read of the diff before merging. Known gaps of that kind:
a test's name kept in a one-line string or a Ruby heredoc still counts as a test; a JavaScript
regex literal after an operator such as + or a keyword such as typeof is read as a division;
a test turned off by code rather than by a skip (Python's `if False:` or `del test_x`, a test
nested in another function, `__test__ = False`, a JavaScript test wrapped in an if) is not
seen; nor is a skip written mid-line in Ruby, as RSpec's `before { skip }`, or a skip mark
saved under a name in another file; a skip in a helper is listed under the helper's name, not
under the tests that call it; and a placeholder disguised with an escape, a link or an
invisible character is taken as a reason. A line of the description that opens with ``` inside
a one-line code span, or after four spaces, is read as opening a fenced block, so the reasons
after it are not read.

Each listed change prints as a line to paste into the PR's Tests section, with the line to read
(in the old file for a deletion, the new one for a skip) and its reason in place of the
placeholder:

    - `tests/test_cart.py::test_remove` deleted (old line 12): <one-line reason>
    - `tests/test_cart.py::test_total` newly skipped (new line 30): <one-line reason>

With --body-env or --body-file, it also reads the PR's description: a change has its reason
when a line of the description has the printed shape, the name whole and then its kind, the
line in brackets if kept, a colon or a dash, and a reason that is more than the placeholder or
a kind word. HTML comments, fenced code blocks and link reference definitions are not read: a
reason must show on the page.

Usage:
    test-guards.py [--base REF]       # list what HEAD changes; REF defaults to origin/HEAD
    test-guards.py --base REF --head PR --body-env PR_BODY --guard PATH ...
                                      # in CI: also fail when a reason is missing

Exit code 0 when nothing is listed, or every listed change has its reason or no description was
given; 1 when a reason is missing; 2 when the guards cannot run, as when git cannot read the
diff.

In CI the description comes through an environment variable, never pasted into the command,
so its text is never run, and the job runs again when the description is edited.
"""
import argparse
import fnmatch
import html
import os
import re
import subprocess
import sys
from collections import Counter

# Folders whose files are test files, in any case, and a folder named after its tests, as
# SwiftPM's Tests/AppTests or .NET's Shop.Tests.
TEST_FOLDERS = {"test", "tests", "__tests__", "spec", "specs"}
TEST_FOLDER = re.compile(r"[a-z0-9]Tests$|\.Tests?$")
# A file's name without its extension: tests (Django), test_cart, cart_test, cart.test, cart-spec,
# cart.cy (Cypress), CartTest, CartTests, CartSpec, CartIT.
TEST_NAME = re.compile(r"^tests?$|^test_|[._-](?:test|spec)$|\.cy$|[a-z0-9](?:Tests?|Spec|IT)$")

# Each language's file extensions, how its comments and strings are written, how a test is
# defined in it, and how a test is skipped.
# "lexer": the comments and strings, as in LEXERS below.
# "named": a line that defines a test and names it; the first group that matched is the name.
# "group": a line that names a group of tests (a class, a describe block), used to name a skip.
# "test_name": a file name the runner needs, in place of TEST_NAME and the test folders.
# "function": a line that defines a function that is no test, as a helper or a fixture, so a
# skip inside it covers that function alone; set-up functions are left out, since their skips
# skip the tests around them.
# "alias": a line that names a skip for later use, as pytest's `requires_db = mark.skipif(...)`;
# the line skips nothing, and each `@requires_db` below it is a skip.
# "file_skips": a line that turns off the other tests of its file, as it.only.
# "raw_skips": a skip written as a comment, read in the line as written, as Go's //go:build.
# "marker": a line that marks the next declaration as a test; "declaration" names it.
# "doc_marker": a marker written in a comment, as PHPUnit's @test.
# Test names are read with strings in place; skips and markers with strings emptied, so a skip
# word inside a test's name or message is not a skip.
QUOTED = r"""\s*\(?\s*(?:'([^']*)'|"([^"]*)"|`([^`]*)`)"""
# A call's arguments, one level of brackets inside: the table of it.each([...]) or skipIf(...).
CALLED = r"(?:\((?:[^()]|\([^()]*\))*\))?"
LANGUAGES = {
    "python": dict(
        extensions={".py"},
        named=[r"^\s*(?:async\s+)?def\s+(test\w*)\s*\("],
        group=[r"^\s*class\s+(\w+)\s*[(:]"],
        function=[r"^\s*(?:async\s+)?def\s+(?!(?i:set_?up))(\w+)\s*\("],
        # A mark anywhere in code: a decorator, a pytestmark list, or one case's marks in a parametrize.
        skips=[r"\bmark\.(?:skip|skipif|xfail)\b", r"\bpytest\.(?:skip|xfail)\s*\(",
               r"\bpytest\.importorskip\s*\(",
               r"@(?:unittest\.)?(?:skip|skipIf|skipUnless|expectedFailure)\b", r"\.skipTest\s*\(",
               r"\braise\s+(?:unittest\.)?SkipTest\b", r"^\s*pytestmark\s*=.*\b(?:skip|skipif|xfail)\b"],
        alias=[r"^(?!pytestmark\b)(\w+)\s*=\s*(?:pytest\.)?mark\.(?:skip|skipif|xfail)\b"]),
    "javascript": dict(
        extensions={".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte"},
        # Jasmine's fit and fdescribe focus a test or a group, as .only does.
        named=[r"(?<![\w$.])(?:x?(?:it|test|specify)|fit)(?!\.(?:describe|step)\b)(?:\.\w+)*" + CALLED + QUOTED],
        group=[r"(?<![\w$.])(?:test\.)?(?:x?(?:describe|context|suite)|fdescribe)(?:\.\w+)*" + CALLED + QUOTED],
        skips=[r"(?<![\w$.])(?:it|test|describe|context|suite|specify)(?:\.\w+)*\.(?:skip|skipIf|runIf|todo|fixme)\b",
               r"(?<![\w$.])x(?:it|test|describe|context|specify)\s*\(", r"(?<![\w$.])pending\s*\(",
               r"(?<![\w$.])this\.skip\s*\("],
        file_skips=[r"(?<![\w$.])(?:it|test|describe|context|suite|specify)(?:\.\w+)*\.only\b",
                    r"(?<![\w$.])f(?:it|describe)\s*\("]),
    "go": dict(
        extensions={".go"},
        # go test runs only the _test.go files, wherever they sit.
        test_name=r"_test$",
        # A test function, or a testify suite's test method.
        named=[r"^\s*func\s+(?:\([^)]*\)\s*)?((?:Test|Fuzz|Example)\w*)\s*\("],
        function=[r"^\s*func\s+(?:\([^)]*\)\s*)?(?!SetupTest\b|SetupSuite\b)(\w+)\s*[(\[]"],
        # The testing package's receivers by their usual names, and a testify suite's s.T().
        skips=[r"(?:(?<![\w.])(?:t|b|f|tb)|\bT\(\))\.Skip(?:f|Now)?\s*\("],
        # A build constraint added to a test file can leave it out of go test.
        raw_skips=[r"^//go:build\b", r"^//\s*\+build\b"]),
    "jvm": dict(
        extensions={".java", ".kt", ".kts", ".scala", ".groovy"},
        named=[r"^\s*(?:test|it|should)" + QUOTED],
        group=[r"^\s*(?:public\s+|internal\s+|abstract\s+)*(?:class|object)\s+(\w+)"],
        marker=[r"@(?:Test|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate)\b"],
        declaration=[r"\b(?:void|fun|def)\s+(`[^`]+`|\w+)\s*[(<]"],
        # JUnit's @EnabledOnOs and its kin run a test only where they hold, as an assumption does.
        skips=[r"@Disabled\w*\b", r"@Enabled\w+\b", r"@Ignore\b", r"@Test\s*\([^)]*\benabled\s*=\s*false\b",
               r"\bassume[A-Z]\w*\s*\("]),
    "dotnet": dict(
        extensions={".cs", ".fs", ".vb"},
        group=[r"^\s*(?:public\s+|internal\s+|sealed\s+|static\s+|partial\s+)*class\s+(\w+)"],
        marker=[r"\[\s*(?:Test|TestCase|Fact|Theory|TestMethod|DataTestMethod)\b"],
        declaration=[r"\b(?:void|Task|let|Sub)\s+(``[^`]+``|\w+)\s*[(<]"],
        # Ignore or Explicit anywhere in an attribute list, as [Test, Ignore("...")] or
        # [TestCase(1, Ignore = "...")], and xUnit's Skip = "...".
        skips=[r"\[[^\]]*(?<![\w.])(?:Ignore|Explicit)\b", r"\bSkip\s*=\s*\""]),
    "ruby": dict(
        extensions={".rb"},
        named=[r"^\s*(?:it|specify|example|scenario|test|xit|xspecify)" + QUOTED, r"^\s*def\s+(test_\w+)"],
        group=[r"^\s*x?(?:describe|context|feature)\s+(?:'([^']*)'|\"([^\"]*)\"|(\w[\w:]*))", r"^\s*class\s+(\w+)"],
        function=[r"^\s*def\s+(?!setup\b)(?:self\.)?(\w+[?!]?)"],
        skips=[r"^\s*(?:skip|pending)\b", r"^\s*x(?:it|describe|context|specify)\b",
               r",\s*(?:skip|pending):", r",\s*:(?:skip|pending)\b"]),
    "rust": dict(
        extensions={".rs"},
        marker=[r"#\[(?:\w+::)?test\b"],
        declaration=[r"\bfn\s+(\w+)\s*[(<]"],
        skips=[r"#\[ignore\b"]),
    "php": dict(
        extensions={".php"},
        named=[r"\bfunction\s+(test\w*)\s*\("],
        group=[r"^\s*(?:final\s+|abstract\s+)*class\s+(\w+)"],
        marker=[r"#\[Test\]"],
        doc_marker=[r"@test\b"],
        declaration=[r"\bfunction\s+(\w+)\s*\("],
        skips=[r"\bmarkTest(?:Skipped|Incomplete)\s*\(", r"#\[(?:Skip|Ignore)\w*\b"]),
    "swift": dict(
        extensions={".swift"},
        named=[r"\bfunc\s+(test\w*)\s*\("],
        group=[r"^\s*(?:final\s+)?class\s+(\w+)"],
        marker=[r"@Test\b"],
        declaration=[r"\bfunc\s+(\w+)\s*[(<]"],
        # .disabled only as a Swift Testing trait, inside @Test( or @Suite( even when the trait
        # list wraps: SwiftUI's .disabled(true) is not a skip.
        skips=[r"\bXCTSkip\w*\b", r"@(?:Test|Suite)\b.*\.disabled\s*\("],
        traits=[(r"\.disabled\s*\(", r"@(?:Test|Suite)\s*\($")]),
    "elixir": dict(
        extensions={".ex", ".exs"},
        named=[r"^\s*test\s+\"([^\"]*)\""],
        group=[r"^\s*describe\s+\"([^\"]*)\""],
        skips=[r"@(?:module)?tag\s+:?skip\b", r"@tag\s+skip:"]),
    "dart": dict(
        extensions={".dart"},
        named=[r"(?<![\w.])(?:test|testWidgets)" + QUOTED],
        group=[r"(?<![\w.])group" + QUOTED],
        skips=[r"\bskip:\s*(?:true|'|\")"]),
}

# How each language writes comments and strings, as regular expressions in the order they are
# tried: "regex" first, then "comment", then "string". Comment spans are emptied; string and
# regex spans keep their text where a test is named and lose it where skips and markers are
# read. A string that spans lines loses its text in both. A file whose extension has its own
# entry uses it.
SINGLE = [r'"(?:\\.|[^"\\\n])*"', r"'(?:\\.|[^'\\\n])*'"]
TRIPLE = [r'"""(?:\\.|[^\\])*?(?:"""|\Z)', r"'''(?:\\.|[^\\])*?(?:'''|\Z)"]
SLASHES = [r"//[^\n]*", r"/\*.*?(?:\*/|\Z)"]
BACKTICK = [r"`(?:\\.|[^`\\])*(?:`|\Z)"]
# A JavaScript regex literal, on one line: a slash where a value starts (at a line's start, after
# an opening bracket, an operator, a comma or `return`) that opens no comment, up to the closing
# slash outside a character class. Without it, /\/*$/ would open a block comment and /`/ a
# template literal, either running to the end of the file. A slash after a value divides.
JS_REGEX = [r"(?:(?<=[(,=:\[!&|?{};])|(?<==>)|(?<=\breturn)|(?m:^))[ \t]*/(?![/*])"
            r"(?:\\[^\n]|\[(?:\\[^\n]|[^\]\\\n])*\]|[^/\\\n\[])+/[a-z]*"]
LEXERS = {
    "python": dict(comment=[r"#[^\n]*"], string=TRIPLE + SINGLE),
    "javascript": dict(regex=JS_REGEX, comment=SLASHES, string=BACKTICK + SINGLE),
    # A Go raw string has no escapes: a backslash before its closing backtick still closes it.
    "go": dict(comment=SLASHES, string=[r"`[^`]*(?:`|\Z)"] + SINGLE),
    "jvm": dict(comment=SLASHES, string=TRIPLE + SINGLE),
    "dotnet": dict(comment=SLASHES, string=[r'"""(?:[^"]|"(?!""))*(?:"""|\Z)', r'@"(?:""|[^"])*(?:"|\Z)'] + SINGLE),
    ".fs": dict(comment=[r"//[^\n]*", r"\(\*.*?(?:\*\)|\Z)"], string=[TRIPLE[0], SINGLE[0]]),
    ".vb": dict(comment=[r"'[^\n]*"], string=[r'"(?:""|[^"\n])*"']),
    "ruby": dict(comment=[r"#[^\n]*", r"(?m:^=begin\b.*?(?:^=end\b[^\n]*|\Z))"], string=SINGLE),
    # A Rust ' is a character only when it closes; otherwise it starts a lifetime, as in &'a str.
    "rust": dict(comment=SLASHES, string=[r'"(?:\\.|[^"\\])*(?:"|\Z)', r"'(?:\\[^'\n]+|[^'\\\n])'"]),
    "php": dict(comment=SLASHES + [r"#(?!\[)[^\n]*"], string=SINGLE),
    "swift": dict(comment=SLASHES, string=[TRIPLE[0], SINGLE[0]]),
    "elixir": dict(comment=[r"#[^\n]*"], string=TRIPLE + SINGLE),
    "dart": dict(comment=SLASHES, string=TRIPLE + SINGLE),
}
for language in LANGUAGES.values():
    for kind in ("named", "group", "function", "alias", "marker", "doc_marker", "declaration", "skips",
                 "file_skips", "raw_skips"):
        language[kind] = [re.compile(pattern) for pattern in language.get(kind, [])]
    language["names_only"] = "test_name" in language
    language["test_name"] = re.compile(language.get("test_name", TEST_NAME))
    language["traits"] = [(re.compile(skip), re.compile(attribute)) for skip, attribute in language.get("traits", [])]
for name, lexer in LEXERS.items():
    LEXERS[name] = re.compile("|".join(f"(?P<{kind}{index}>{pattern})" for kind in ("regex", "comment", "string")
                                       for index, pattern in enumerate(lexer.get(kind, []))), re.S)
# How far a marker or a skip decorator may sit above the declaration it applies to.
REACH = 6
PLACEHOLDER = "<one-line reason>"


class GitError(Exception):
    pass


def git(*args):
    """git's output as text; a path git prints that is not UTF-8 keeps its bytes."""
    done = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True)
    if done.returncode:
        message = done.stderr.decode("utf-8", "replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return done.stdout.decode("utf-8", "surrogateescape")


def read_file(commit, path):
    """A file's text at a commit, decoded as UTF-8 with anything else replaced; "" when the
    commit has no such file, or it is no file (a submodule)."""
    try:
        done = subprocess.run(["git", "cat-file", "blob", f"{commit}:{path}"], capture_output=True)
    except OSError as error:
        raise GitError(str(error))
    return done.stdout.decode("utf-8", "replace") if done.returncode == 0 else ""


def language_of(path):
    extension = os.path.splitext(path)[1].lower()
    return next((name for name, language in LANGUAGES.items() if extension in language["extensions"]), None)


def by_name(path, extra=()):
    """Whether a file's own name says it holds tests, or a pattern from --tests does."""
    language = LANGUAGES.get(language_of(path or ""))
    if language is None:
        return False
    stem = os.path.splitext(os.path.basename(path))[0]
    return bool(language["test_name"].search(stem)) or any(fnmatch.fnmatch(path, glob) for glob in extra)


def is_test_file(path, extra=()):
    if not path or language_of(path) is None:
        return False
    if language_of(path) == "rust" or by_name(path, extra):
        return True
    if LANGUAGES[language_of(path)]["names_only"]:
        return False
    return any(folder.lower() in TEST_FOLDERS or TEST_FOLDER.search(folder) for folder in path.split("/")[:-1])


def changed_files(base, head):
    """The files the diff from base to head changes, as dict(old, new): a path, or None for an
    added or deleted file. A rename keeps both paths."""
    fields = git("diff", "--name-status", "-z", "--no-relative", "--find-renames", f"{base}...{head}").split("\0")
    files, index = [], 0
    while index < len(fields) and fields[index]:
        status = fields[index][0]
        if status in "RC":
            old, new = fields[index + 1], fields[index + 2]
            index += 3
        else:
            path = fields[index + 1]
            old, new = (None if status == "A" else path), (None if status == "D" else path)
            index += 2
        files.append(dict(old=old, new=new))
    return files


def lex(path, text):
    """A file's lines twice over, with comments emptied: once with its strings as written, to
    read test names, and once with their text emptied, to read skips and markers. A string that
    spans lines is emptied in both. Line numbers stay as in the file."""
    extension = os.path.splitext(path)[1].lower()
    lexer = LEXERS.get(extension) or LEXERS[language_of(path)]
    named, bare, at = [], [], 0
    blank = lambda span: re.sub(r"[^\n]", " ", span)
    for match in lexer.finditer(text):
        span = match.group()
        named.append(text[at:match.start()])
        bare.append(text[at:match.start()])
        if match.lastgroup.startswith("comment") or "\n" in span:
            named.append(blank(span))
            bare.append(blank(span))
        else:
            named.append(span)
            bare.append(span[0] + blank(span[1:-1]) + span[-1] if len(span) > 1 else span)
        at = match.end()
    named.append(text[at:])
    bare.append(text[at:])
    return "".join(named).split("\n"), "".join(bare).split("\n")


def first_group(match):
    return next((group for group in match.groups() if group is not None), "").strip("`").strip()


def named(language, text, kinds=("named",)):
    for kind in kinds:
        for pattern in language[kind]:
            match = pattern.search(text)
            if match:
                return first_group(match)
    return None


class Source:
    """A test file's lines as written (raw), with comments emptied (code), and with strings
    emptied as well (bare)."""

    def __init__(self, path, text):
        self.language = LANGUAGES[language_of(path)]
        self.raw = text.split("\n")
        self.code, self.bare = lex(path, text)
        # The brackets still open where each line starts, as (line index, column), outermost
        # first; one more entry holds those open at the end of the file.
        self.open, stack = [], []
        for index, text in enumerate(self.bare):
            self.open.append(tuple(stack))
            stack = opened(stack, index, text)
        self.open.append(tuple(stack))
        # The groups of tests, as (name, first line index, last line index, whether its tests run).
        self.groups = []
        for index, text in enumerate(self.code):
            name = named(self.language, text, ("group",))
            if name:
                self.groups.append((name, index, extent(self.code, index), runs(self.language, text, name)))

    def chain(self, index, own=True):
        """The names of the groups around line `index`, outermost first, with the name on the line
        itself when own; joined by ::, as pytest names a test in a class."""
        names = [name for name, first, last, _ in self.groups if first < index <= last]
        name = named(self.language, self.code[index], ("named", "group", "declaration", "function")) if own else None
        return "::".join(names + ([name] if name else []))

    def collected(self, index):
        """Whether the runner collects a test on line `index`: not in a class pytest leaves out."""
        return all(ran for _, first, last, ran in self.groups if first < index <= last)

    def closing(self, index):
        """The index of the line where the brackets that line `index` opens are closed again."""
        depth = len(self.open[index])
        return next((at for at in range(index, len(self.bare)) if len(self.open[at + 1]) <= depth),
                    len(self.bare) - 1)

    def innermost(self, index, column):
        """The line index and column of the innermost bracket open at a column of a line, or None."""
        stack = opened(list(self.open[index]), index, self.bare[index][:column])
        return stack[-1] if stack else None

    def is_comment(self, number):
        """Whether line `number` (1-based) holds a comment and nothing else."""
        return bool(self.raw[number - 1].strip()) and not self.code[number - 1].strip()

    def is_marker(self, number):
        if any(pattern.search(self.bare[number - 1]) for pattern in self.language["marker"]):
            return True
        return self.is_comment(number) and any(pattern.search(self.raw[number - 1])
                                                for pattern in self.language["doc_marker"])


def opened(stack, index, text):
    """stack, the brackets open before a line's text, as (line index, column), with the text's
    own brackets opened and closed; a closing bracket with none open is ignored."""
    stack = list(stack)
    for column, character in enumerate(text):
        if character in "([{":
            stack.append((index, column))
        elif character in ")]}" and stack:
            stack.pop()
    return stack


def runs(language, text, name):
    """Whether a group's tests run: pytest collects a class only when its name starts with Test,
    unless it has a base, as a unittest TestCase."""
    if language is not LANGUAGES["python"] or name.startswith("Test"):
        return True
    return bool(re.search(r"\(\s*(?!object\s*\))[^)\s]", text))


def extent(lines, index):
    """The index of the last line of the block that starts at lines[index]: the lines indented
    under its first line, and the one closing it."""
    depth, last = indent(lines[index]), index
    for at in range(index + 1, len(lines)):
        stripped = lines[at].strip()
        if not stripped:
            continue
        if indent(lines[at]) > depth:
            last = at
            continue
        if indent(lines[at]) == depth and (stripped[0] in ")]}" or re.match(r"end\b", stripped)):
            last = at
        break
    return last


def body(lines, index):
    """The stripped lines of the test that starts at lines[index]."""
    return tuple(text.strip() for text in lines[index:extent(lines, index) + 1] if text.strip())


def definitions(source):
    """The tests a file defines, in order, as (name, body, line number). A marker applies to the
    next declaration, when it sits at most REACH lines above it."""
    language, found, marked = source.language, [], None
    for index, text in enumerate(source.code):
        number = index + 1
        if source.is_marker(number):
            name = named(language, text, ("declaration",))
            if name:
                found.append((name, body(source.code, index), number))
                marked = None
            else:
                marked = number
            continue
        name = named(language, text)
        if name:
            found.append((name, body(source.code, index), number))
            marked = None
            continue
        name = named(language, text, ("declaration",)) if marked is not None else None
        if name:
            if number - marked <= REACH:
                found.append((name, body(source.code, index), number))
            marked = None
    return [test for test in found if source.collected(test[2] - 1)]


def is_attachment(text):
    """A line that may sit between a skip decorator and what it skips: a decorator, an
    annotation or attribute, a blank line, or one that held only a comment."""
    stripped = text.strip()
    return not stripped or stripped[0] in "@#["


def indent(text):
    return len(text) - len(text.lstrip())


def skipped_line(source, number):
    """The index of the line that names what the skip on line `number` (1-based) of a file skips:
    the test or group on its line, below it when the skip is a decorator or an annotation, or
    around it when it sits in its body. A skip inside the brackets of a decorator that spans
    lines, as a wrapped skipif or one case's marks in a parametrize, is read from that decorator's
    line. A skip in a helper or a fixture names that function, so it covers no test, unless the
    function sits inside a test. None for the whole file."""
    language, lines = source.language, source.code
    outer = source.open[number - 1]
    if outer and is_attachment(lines[outer[0][0]]):
        number = outer[0][0] + 1
    kinds = ("named", "group", "declaration", "function")
    text = lines[number - 1]
    if named(language, text, kinds):
        return number - 1
    if not text.strip():
        return None
    if is_attachment(text):
        # Below the line that closes the decorator's brackets, when it leaves them open.
        end = source.closing(number - 1) + 1
        for at in range(end, min(end + REACH, len(lines))):
            if named(language, lines[at], kinds):
                return at
            if not is_attachment(lines[at]):
                break
    # A skip on a closing line, as Dart's `}, skip: true);`, belongs to the block it closes.
    depth = indent(text) + (text.strip()[0] in ")]}")
    function = None
    for at in range(number - 2, -1, -1):
        above = lines[at]
        if above.strip() in ("", "{") or indent(above) >= depth:
            continue
        if named(language, above, ("named", "declaration")):
            return at
        if named(language, above, ("group",)):
            return at if function is None else function
        if function is None and named(language, above, ("function",)):
            function = at
        depth = indent(above)
    return function


def skips(source):
    """The skips a file holds, as (the skip's line, what it skips or None for the whole file, line
    number, the first and last line index of what it skips, the name a skip mark is saved under
    on that line or None). What it skips is named with the groups around it, as
    TestCart::test_empty, so the same skip on a test of the same name in another group is another
    skip. A line that saves a skip mark under a name, as `requires_db = mark.skipif(...)`, is a
    skip named after that name that covers only its own line, so a changed definition is listed;
    each `@requires_db` is a skip of its test, and a pytestmark that names it, of the file."""
    language, found = source.language, []
    aliases = {match.group(1) for text in source.bare for pattern in language["alias"]
               for match in [pattern.search(text)] if match}
    names = "|".join(map(re.escape, sorted(aliases)))
    alias = re.compile(r"^\s*@(?:%s)\b" % names) if aliases else None
    mentioned = re.compile(r"(?<![\w.])(?:%s)\b" % names) if aliases else None
    pytestmark = re.compile(r"^\s*pytestmark\s*=")
    for index, text in enumerate(source.bare):
        line = source.code[index].strip() or source.raw[index].strip()
        saved = next((match.group(1) for pattern in language["alias"] for match in [pattern.search(text)] if match),
                     None)
        if saved:
            what = "::".join(filter(None, (source.chain(index, own=False), saved)))
            found.append((line, what, index + 1, index, index, saved))
            continue
        outer = source.open[index]
        if any(pattern.search(source.raw[index]) for pattern in language["raw_skips"]):
            target = None
        elif any(pattern.search(text) for pattern in language["file_skips"]):
            target = None
        elif mentioned and mentioned.search(text) and (
                pytestmark.match(text) or (outer and pytestmark.match(source.bare[outer[0][0]]))):
            target = None
        elif (any(pattern.search(text) for pattern in language["skips"]) or in_attribute(source, index)
              or (alias and alias.search(text))):
            target = skipped_line(source, index + 1)
        else:
            continue
        if target is None:
            found.append((line, None, index + 1, 0, len(source.code) - 1, None))
        else:
            found.append((line, source.chain(target), index + 1, target, extent(source.code, target), None))
    return found


def under(source, found):
    """Each test of a file, named with its groups, with the skips that apply to it: its own, its
    groups' and its file's, as a set of (the skip's line, what it skips)."""
    return [("::".join(filter(None, (source.chain(number - 1, own=False), name))), number,
             {(line, what) for line, what, _, first, last, _ in found if first <= number - 1 <= last})
            for name, _, number in definitions(source)]


def in_attribute(source, index):
    """Whether line `index` holds a skip that counts only inside an attribute's brackets, with that
    attribute opened on an earlier line, as a Swift Testing trait list that wraps."""
    for skip, attribute in source.language["traits"]:
        for match in skip.finditer(source.bare[index]):
            opener = source.innermost(index, match.start())
            if opener and opener[0] < index and attribute.search(source.bare[opener[0]][:opener[1] + 1]):
                return True
    return False


def unpaired(tests, pool, key):
    """The tests that find no match in pool, a Counter of keys; each match uses one up."""
    left = []
    for test in tests:
        if pool[key(test)]:
            pool[key(test)] -= 1
        else:
            left.append(test)
    return left


def first_lines(found):
    """found, (key, line) pairs, with each key once, at its first line."""
    first = {}
    for key, number in found:
        first.setdefault(key, number)
    return list(first.items())


def leaves(old, new, extra=()):
    """Whether a test file is deleted, or renamed to a path its runner no longer collects: one
    that is no test file, or one that is a test file only by its folder when its name made it
    one before, as tests/test_cart.py renamed tests/cart_checks.py."""
    return is_test_file(old, extra) and (not is_test_file(new, extra) or (by_name(old, extra)
                                                                           and not by_name(new, extra)))


def deleted_tests(files, read_old, read_new, extra=()):
    """Every deleted test as (path::name, its line in the old file), or (path, None) for a test
    file taken away whole. read_old and read_new give a file's text on each side of the diff. A
    test from a file named as a test file has moved only to another file named as one."""
    name = lambda test: test[0]
    sides, spare = [], Counter()
    for entry in files:
        old, new = entry["old"], entry["new"]
        before = definitions(Source(old, read_old(old))) if is_test_file(old, extra) else []
        kept = is_test_file(new, extra) and not leaves(old, new, extra)
        after = definitions(Source(new, read_new(new))) if kept else []
        sides.append((entry, before, unpaired(before, Counter(map(name, after)), name)))
        added = unpaired(after, Counter(map(name, before)), name)
        spare.update((test, text, by_name(new, extra)) for test, text, _ in added)
    found = []
    for entry, before, gone in sides:
        old = entry["old"]
        named_file = by_name(old, extra)
        left = []
        for test, text, number in gone:
            for key in ((test, text, True),) + (() if named_file else ((test, text, False),)):
                if spare[key]:
                    spare[key] -= 1
                    break
            else:
                left.append((test, text, number))
        if leaves(old, entry["new"], extra):
            if left or (not before and named_file):
                found.append((old, None))
            continue
        found.extend((f"{old}::{test}", number) for test, _, number in left)
    return first_lines(found)


def skipped_tests(files, read_old, read_new, extra=()):
    """Every newly skipped test, as (path::name, the skip's line in the new file), or the path in
    place of path::name when the whole file is skipped. A skip the old file held on the same test,
    in the same groups, with the same line, is not new. A test that a skip the old file held now
    applies to, and did not before, is listed too, at its own line: one moved into a skipped
    group or class, or into a file skipped whole, or added there."""
    found = []
    for entry in files:
        old, new = entry["old"], entry["new"]
        if not is_test_file(new, extra):
            continue
        # The old file is read in the new one's language, even when it was no test file then.
        before = Source(new, read_old(old) if old else "")
        after = Source(new, read_new(new))
        old_skips, new_skips = skips(before), skips(after)
        held = Counter((text, what) for text, what, *_ in old_skips)
        # A skip mark saved under a new name skips nothing until a test or a pytestmark uses it.
        saved_before = {saved for *_, saved in old_skips if saved}
        for text, what, number, _, _, saved in new_skips:
            if held[(text, what)]:
                held[(text, what)] -= 1
            elif not saved or saved in saved_before:
                found.append((f"{new}::{what}" if what else new, number))
        kept = {(text, what) for text, what, *_ in old_skips}
        had = {}
        for test, _, applied in under(before, old_skips):
            had.setdefault(test, set()).update(applied)
        for test, number, applied in under(after, new_skips):
            if any(skip in kept and skip not in had.get(test, ()) for skip in applied):
                found.append((f"{new}::{test}", number))
    return first_lines(found)


def changed_guards(files, guards):
    """Each file of guards the diff changes, as (path, None)."""
    return [(path, None) for path in guards if any(path in (entry["old"], entry["new"]) for entry in files)]


KINDS = {"deleted": r"deleted", "newly skipped": r"(?:newly\s+)?skipped", "changed": r"changed"}
KIND_WORDS = {"deleted", "removed", "newly", "skipped", "edited", "moved", "renamed", "changed"}


def readable(body):
    """The description as the page shows it: without HTML comments, fenced code blocks or link
    reference definitions, whose title text never shows."""
    body = re.sub(r"<!--.*?(?:-->|\Z)", "", body, flags=re.S)
    shown, fence = [], None
    for line in body.splitlines():
        opening = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None and opening:
            fence = opening.group(1)
        elif fence is not None and line.strip().startswith(fence[0] * len(fence)) and not line.strip().strip(fence[0]):
            fence = None
        elif fence is None and not re.match(r"\s{0,3}\[[^\]]+\]:\s", line):
            shown.append(line)
    return shown


def reason(body, key, kind):
    """The reason the description gives for key, or None. The line must have the printed shape:
    the key whole, its kind, maybe its line, then a colon, a dash or a table bar, and a reason that
    is neither the placeholder nor a kind word. A key stands whole: `adds` is not read in
    `adds two`, nor `test_remove` in `test_remove_all`."""
    shape = re.compile(r"(?<![\w./-])" + re.escape(key) + r"`?\s+" + KINDS[kind]
                       + r"\b(?:\s*\((?:old |new )?line \d+\))?\s*[:|\-–—]+(.*)$")
    for line in readable(body):
        match = shape.search(line)
        if not match:
            continue
        rest = match.group(1).strip().strip("|").strip()
        words = re.findall(r"[^\W_]+", rest.lower())
        # The placeholder left in place, even in code, emphasis or an HTML entity, or followed by
        # punctuation, is no reason; a reason that starts like it, as `<Button> was removed`, is.
        bare = re.sub(r"[`*_~]", "", html.unescape(rest)).strip().rstrip(".,;:!?").strip()
        if bare == PLACEHOLDER or not words or set(words) <= KIND_WORDS:
            continue
        return rest
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="List deleted and newly skipped tests; check each has a reason.")
    parser.add_argument("--base", default="origin/HEAD", help="the branch the PR merges into (default origin/HEAD)")
    parser.add_argument("--head", default="HEAD", help="the PR's commit (default HEAD)")
    parser.add_argument("--tests", action="append", default=[], metavar="GLOB",
                        help="another pattern for test files in the languages the guards know, such as "
                             "'checks/*.py'; may repeat")
    parser.add_argument("--guard", action="append", default=[], metavar="PATH",
                        help="a file whose every change is listed, as the guards' own script and CI file; may repeat")
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
