"""Which files hold tests, and how each language the guards know defines, groups and skips a test,
and writes its comments and strings."""
import fnmatch
import os
import re

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
